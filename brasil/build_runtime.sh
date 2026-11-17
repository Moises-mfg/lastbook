#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="${LASTBOOK_LLAMA_BUILD:-$ROOT/derived/brasil-llama}"
REV=dde879bc4f954b809892fd0d660515f42536394a
if [ ! -d "$BUILD/source/.git" ]; then
  mkdir -p "$BUILD"
  git clone --depth 1 --branch b12032 https://github.com/ggml-org/llama.cpp.git "$BUILD/source"
fi
[ "$(git -C "$BUILD/source" rev-parse HEAD)" = "$REV" ] || { echo 'Revisão do motor diferente da esperada'; exit 1; }
cmake -S "$BUILD/source" -B "$BUILD/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_BUILD_RPATH_USE_ORIGIN=ON -DLLAMA_OPENSSL=OFF -DLLAMA_USE_PREBUILT_UI=OFF -DLLAMA_BUILD_TESTS=OFF -DGGML_NATIVE=OFF -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_BMI2=OFF -DGGML_SSE42=OFF -DGGML_FMA=OFF -DGGML_F16C=OFF -DGGML_CUDA=OFF -DGGML_VULKAN=OFF
cmake --build "$BUILD/build" --target llama-completion -j 2
mkdir -p "$ROOT/brasil/runtime"
cp "$BUILD/build/bin/llama-completion" "$BUILD/build/bin/libllama-completion-impl.so" "$BUILD/build/bin/"libllama-common.so* "$BUILD/build/bin/"libllama.so* "$BUILD/build/bin/"libggml*.so* "$ROOT/brasil/runtime/"
cp "$BUILD/source/LICENSE" "$ROOT/brasil/runtime/LICENSE-llama.cpp"
