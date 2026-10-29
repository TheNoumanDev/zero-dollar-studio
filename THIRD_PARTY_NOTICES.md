# Third-party notices

The code in this repository is MIT-licensed (see [LICENSE](LICENSE)). The tools and models below are **not** included in this repository. The plugins install or download them from their official sources, and each keeps its own license. Check them yourself before commercial use.

| Component | Used by | License | Notes |
|---|---|---|---|
| [Remotion](https://github.com/remotion-dev/remotion) (`remotion`, `@remotion/*`, including `@remotion/whisper-webgpu`) | make-video | [Remotion License](https://www.remotion.dev/license) | **Not open source.** Free for individuals, for-profit organisations with up to 3 employees, non-profits and evaluation. Larger companies need a Company License. Installed from npm, never vendored. |
| [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) (Resemble AI) | make-video | MIT | Every output carries an imperceptible Perth watermark; don't remove it. Clone only voices you have consent for. |
| [Whisper](https://github.com/openai/whisper) weights (OpenAI), via [onnx-community](https://huggingface.co/onnx-community) and [mlx-community](https://huggingface.co/mlx-community) | make-video | MIT | Captions (small.en) and take checking (large-v3-turbo). |
| [mlx-whisper](https://github.com/ml-explore/mlx-examples) | make-video | MIT | Optional take checker. |
| [FluidSynth](https://github.com/FluidSynth/fluidsynth) | make-video | LGPL-2.1 | Called as an external binary installed by the user (Homebrew). |
| [GeneralUser GS](https://github.com/mrbumpy409/GeneralUser-GS) soundfont (S. Christian Collins) | make-video | [GeneralUser GS License](https://github.com/mrbumpy409/GeneralUser-GS/blob/main/documentation/LICENSE.txt) | Free for making music, including commercial. Downloaded by `tools/setup.sh`, not redistributed here. |
| [ffmpeg](https://ffmpeg.org) | make-video | LGPL/GPL | Installed by the user (Homebrew). |
| [OpenCV](https://github.com/opencv/opencv-python) (`opencv-python-headless`) | make-video | Apache-2.0 / MIT | QA frame analysis. |
| `mido`, `soundfile`, `scipy`, `numpy`, `huggingface_hub`, PyTorch | make-video | MIT / BSD-3-Clause / Apache-2.0 | Python dependencies from PyPI. |

## Not used, on purpose

- **InsightFace models** (e.g. `buffalo_l`) are licensed for non-commercial research only. None of these plugins download or use them. If a future face step needs a face detector, it uses a permissively licensed one.
- **macOS `say` voices** are not used as voice references: Apple's licence doesn't allow commercial use of their output.
