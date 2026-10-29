"""One place that asks a logged-in coding-agent CLI for JSON (no API keys).

Pick the agent with SNIPSHORTS_LLM:
  claude (default)  Claude Code: `claude -p` with a JSON schema
  codex             OpenAI Codex CLI: `codex exec`, read-only sandbox
  gemini            Google Gemini CLI: `gemini -p`, plan (read-only) mode
  anything else     a command that reads the prompt on stdin and prints the reply,
                    e.g. SNIPSHORTS_LLM="ollama run qwen3:14b"
Agents other than Claude get the schema in the prompt; the first JSON object in
their reply is used.
"""
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AGENT = os.environ.get("SNIPSHORTS_LLM", "claude").strip() or "claude"


def check():
    """Exit with a clear message if the chosen agent's CLI isn't installed."""
    exe = shlex.split(AGENT)[0]
    if not shutil.which(exe):
        sys.exit(f"{exe} not found on PATH. Install and log in to it, or set SNIPSHORTS_LLM "
                 "(claude, codex, gemini, or a command that reads a prompt on stdin).")


def ask(prompt: str, schema: dict, timeout: int = 900):
    check()
    if AGENT == "claude":
        # Subscription login, not an API key: drop API-key routing from the env.
        env = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_", "CLAUDE_CODE_USE_"))}
        out = run(["claude", "-p", "--output-format", "json", "--json-schema", json.dumps(schema)], prompt, timeout, env)
        envelope = json.loads(out)
        return envelope.get("structured_output") or json.loads(envelope["result"])

    prompt += ("\n\nReply with ONLY one JSON object (no prose, no code fence) that matches this JSON schema:\n"
               + json.dumps(schema))
    if AGENT == "codex":
        with tempfile.TemporaryDirectory() as tmp:
            last = Path(tmp) / "reply.txt"
            run(["codex", "exec", "--skip-git-repo-check", "--ephemeral", "--sandbox", "read-only",
                 "-C", tmp, "-o", str(last), "-"], prompt, timeout)
            return first_json(last.read_text())
    if AGENT == "gemini":
        return first_json(run(["gemini", "--approval-mode", "plan", "-p", "Follow the instructions above."], prompt, timeout))
    return first_json(run(shlex.split(AGENT), prompt, timeout))


def run(cmd, prompt, timeout, env=None):
    out = subprocess.run(cmd, input=prompt, capture_output=True, text=True, env=env, timeout=timeout)
    if out.returncode != 0:
        sys.exit(f"{cmd[0]} failed: {out.stderr[-2000:]}")
    return out.stdout


def first_json(text: str):
    """The first complete JSON object in a reply (agents sometimes add prose or a fence)."""
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                return dec.raw_decode(text[i:])[0]
            except json.JSONDecodeError:
                continue
    sys.exit(f"{AGENT} reply had no JSON object:\n{text[-1500:]}")
