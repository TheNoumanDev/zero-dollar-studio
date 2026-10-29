/**
 * Note: When using the Node.JS APIs, the config file
 * doesn't apply. Instead, pass options directly to the APIs.
 *
 * All configuration options: https://remotion.dev/docs/config
 */

import fs from "node:fs";
import path from "node:path";
import { Config } from "@remotion/cli/config";

Config.setRspack(true);
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

// MP4 defaults for `npx remotion render`.
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");

/**
 * Browser fallback.
 * Remotion normally downloads its own Chrome Headless Shell from remotion.media.
 * If that download has not succeeded (for example the host is blocked on this
 * network), use the locally installed Google Chrome instead.
 * Run `npx remotion browser ensure` to retry the download; once it succeeds,
 * this fallback switches off automatically.
 */
const headlessShellDir = path.join(process.cwd(), "node_modules/.remotion/chrome-headless-shell");
const hasHeadlessShell =
  fs.existsSync(headlessShellDir) &&
  fs.readdirSync(headlessShellDir).some((f) => f !== "download.lock");
const systemChrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

if (!hasHeadlessShell && fs.existsSync(systemChrome)) {
  Config.setBrowserExecutable(systemChrome);
  Config.setChromeMode("chrome-for-testing");
}
