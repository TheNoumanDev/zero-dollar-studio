import { canUseWhisperWebGpu } from "@remotion/whisper-webgpu";
console.log(JSON.stringify(await canUseWhisperWebGpu(), null, 2));
