#!/usr/bin/env python3
"""Compila o motor fixado para o sistema de destino, sem modelo embutido."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
REV='dde879bc4f954b809892fd0d660515f42536394a'

def main():
    source=ROOT/'derived/desktop-llama/source';build=source.parent/'build';source.parent.mkdir(parents=True,exist_ok=True)
    if not (source/'.git').exists():subprocess.run(['git','clone','--depth','1','--branch','b12032','https://github.com/ggml-org/llama.cpp.git',str(source)],check=True)
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('Revisão do motor inesperada.')
    options=['-DCMAKE_BUILD_TYPE=Release','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_USE_PREBUILT_UI=OFF','-DGGML_NATIVE=OFF','-DGGML_CUDA=OFF','-DGGML_VULKAN=OFF','-DGGML_METAL=OFF','-DGGML_BACKEND_DL=ON','-DGGML_CPU_ALL_VARIANTS=ON','-DGGML_AVX=OFF','-DGGML_AVX2=OFF','-DGGML_BMI2=OFF','-DGGML_SSE42=OFF','-DGGML_FMA=OFF','-DGGML_F16C=OFF']
    if sys.platform=='win32':options+=['-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded','-DGGML_OPENMP=OFF']
    if sys.platform=='darwin':options+=['-DCMAKE_OSX_DEPLOYMENT_TARGET=13.3','-DCMAKE_BUILD_RPATH=@loader_path','-DCMAKE_INSTALL_RPATH=@loader_path']
    subprocess.run(['cmake','-S',str(source),'-B',str(build),*options],check=True)
    subprocess.run(['cmake','--build',str(build),'--config','Release','--target','llama-completion','--parallel','3'],check=True)
    target=ROOT/'brasil/runtime';target.mkdir(parents=True,exist_ok=True)
    for file in (build/'bin').rglob('*'):
        if file.is_file() and (file.name in ('llama-completion','llama-completion.exe') or file.suffix in ('.dll','.dylib') or '.so' in file.name):shutil.copy2(file,target/file.name)
    shutil.copyfile(source/'LICENSE',target/'LICENSE-llama.cpp')

if __name__=='__main__':main()
