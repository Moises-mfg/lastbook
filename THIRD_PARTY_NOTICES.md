# Third-party notices

Lastbook builds on the work below. Each part keeps its own licence. The **Where** column says whether it is in this
repository, bundled into the apps by the build, or downloaded by setup.

**Checked** means the licence was read from the licence file or package metadata of the exact version the builds use.
**Upstream** means it is taken from the project's own published licence because no local copy was at hand when this list
was written. Check those before a public release.

Versions are the pins in `packaging/requirements*.txt`, `packaging/llm/*.sh`, `packaging/build_app_windows.sh` and
`llm_local.py`.

## Vendored in this repository

| Component | Version | Licence | Source | Checked |
|---|---|---|---|---|
| pypdfium2 (`engine/vendor-macos/` on Mac; installed from PyPI for the Windows build) | 5.14.0 | Apache-2.0 or BSD-3-Clause; data files CC-BY-4.0 | https://github.com/pypdfium2-team/pypdfium2 | Checked: `pypdfium2-5.14.0.dist-info/licenses/` |
| PDFium, inside pypdfium2's `libpdfium.dylib` | as built by pdfium-binaries | BSD-3-Clause (The PDFium Authors) | https://pdfium.googlesource.com/pdfium, https://github.com/bblanchon/pdfium-binaries | Checked: `BUILD_LICENSES/pdfium.txt`, `pdfium-binaries.txt` |
| Libraries built into PDFium: abseil, agg 2.3, fast_float, FreeType, ICU, Little CMS, libjpeg-turbo, OpenJPEG, libpng, LLVM libc, simdutf, zlib | as built | Each under its own licence (Apache-2.0, BSD-style, FreeType/FTL, Unicode, MIT, IJG, zlib and others) | see each file | Checked: the full texts are in `engine/vendor-macos/pypdfium2-5.14.0.dist-info/licenses/data/darwin_arm64/BUILD_LICENSES/` |

## Bundled into the apps by the build

| Component | Version | Licence | Source | Checked |
|---|---|---|---|---|
| Python (runtime bundled by PyInstaller) | 3.11.18 (Mac), 3.14.10 or a later 3.14 (Windows) | PSF-2.0 | https://www.python.org | Upstream |
| PyInstaller bootloader | 6.22.3 | GPL-2.0-or-later with the PyInstaller exception, which allows bundling programs under any licence | https://github.com/pyinstaller/pyinstaller | Checked: package metadata |
| python-libzim | 3.13.1 (Mac), 3.13.0 (Windows) | **GPL-3.0-or-later** | https://github.com/openzim/python-libzim | Checked: `libzim-3.13.1.dist-info/licenses/LICENSE` |
| libzim (C++, inside python-libzim's wheel) | 9 | GPL-2.0 | https://github.com/openzim/libzim | Upstream |
| Xapian and ICU 73, built into libzim | as built | Xapian: GPL-2.0-or-later; ICU: Unicode License | https://xapian.org, https://icu.unicode.org | Upstream (both found in the binary) |
| zstd and liblzma (xz), used by libzim | as built | zstd: BSD-3-Clause or GPL-2.0; liblzma: 0BSD/public domain | https://github.com/facebook/zstd, https://tukaani.org/xz/ | Upstream |
| NumPy | 2.4.6 (Mac), 2.5.4 (Windows) | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | https://numpy.org | Checked: package metadata (2.4.6) |
| Beautiful Soup 4 | 4.15.0 | MIT | https://www.crummy.com/software/BeautifulSoup/ | Checked: package metadata |
| soupsieve (used by Beautiful Soup) | 3.0.4 | MIT | https://github.com/facelessuser/soupsieve | Checked: package metadata |
| PyObjC: pyobjc-core, Cocoa, WebKit (Mac) | 13.0 | MIT | https://github.com/ronaldoussoren/pyobjc | Checked: package metadata |
| onnxruntime (Windows) | 1.31.1 | MIT; its bundled components are listed in its `ThirdPartyNotices.txt` | https://github.com/microsoft/onnxruntime | Checked: metadata and notices of 1.31.0 |
| Hugging Face tokenizers (Windows) | 0.23.3 | Apache-2.0; the Rust crates built into it are listed in its SBOM (`dist-info/sboms`) | https://github.com/huggingface/tokenizers | Checked: package metadata |
| pythonnet (Windows) | 3.2.1 | MIT | https://github.com/pythonnet/pythonnet | Upstream |
| clr_loader (Windows) | 0.3.1 | MIT | https://github.com/pythonnet/clr-loader | Upstream |
| Microsoft WebView2 SDK: `Microsoft.Web.WebView2.Core.dll`, `Microsoft.Web.WebView2.WinForms.dll`, `WebView2Loader.dll` (Windows) | 1.0.3856.49 | Microsoft's licence in the NuGet package (`LICENSE.txt`), which allows redistributing these files with an app | https://www.nuget.org/packages/Microsoft.Web.WebView2 | Upstream: check the package's `LICENSE.txt` before release |
| Microsoft Edge WebView2 Runtime (Windows) | installed by Windows | Microsoft software licence terms | https://developer.microsoft.com/microsoft-edge/webview2/ | Not bundled: the app uses the copy Windows provides |
| llama.cpp and ggml, in `lastbook-llm` (optional local AI runner) | tag b12032 (dde879bc) | MIT (Copyright the ggml authors) | https://github.com/ggml-org/llama.cpp | Checked: `LICENSE`; it ships beside the runner as `LICENSE-llama.cpp.txt` |
| nlohmann/json, used by llama.cpp's `common/` | as vendored in b12032 | MIT | https://github.com/nlohmann/json | Checked: `licenses/LICENSE-jsonhpp` |
| LLVM libc++, libunwind, OpenMP runtime (`libc++.dll`, `libunwind.dll`, `libomp.dll`, Windows runner) | llvm-mingw 20261020 | Apache-2.0 WITH LLVM-exception | https://github.com/mstorsjo/llvm-mingw | Checked: ships as `LICENSE-llvm-mingw.txt` |

Build-only tools (uv, CMake, Ninja, glslc/shaderc, Vulkan and SPIR-V headers, pyinstaller-hooks-contrib, altgraph,
macholib, setuptools, packaging) are used to make the apps, and none of their code is bundled except as their licences
allow. The Vulkan loader (`vulkan-1.dll`) comes with the graphics driver and is not bundled.

## Downloaded by setup, never bundled

| Component | Version | Licence | Source | Checked |
|---|---|---|---|---|
| Gemma 4 26B A4B instruct, GGUF quantization by Unsloth (`gemma-4-26B-A4B-it-UD-Q4_K_M.gguf`) | revision pinned in `llm_local.py` | Apache-2.0, per the model card | https://huggingface.co/unsloth (Google's Gemma 4 release) | Upstream: check the model card and its licence file before release |
| BAAI bge-small-en-v1.5 (ONNX), meaning-based search | as pinned | MIT, per the model card | https://huggingface.co/BAAI/bge-small-en-v1.5 | Upstream: the local copy has no licence file beside it |

## Website

| Component | Licence | Source | Checked |
|---|---|---|---|
| Atkinson Hyperlegible Next (`website/fonts/`) | SIL Open Font License 1.1 | https://github.com/googlefonts/atkinson-hyperlegible-next | Checked: `website/fonts/OFL.txt` |
| Nunito (`website-next/fonts/`) | SIL Open Font License 1.1 | https://github.com/googlefonts/nunito | Checked: `website-next/fonts/OFL.txt` |

## Library content

The manuals, videos, encyclopedias and map data in the library packs are not part of this repository. Each pack has a
Sources and permissions page with the publisher and terms of every item. The offline map uses OpenStreetMap data
(ODbL, © OpenStreetMap contributors) and US government data such as USGS, NOAA and USACE, as credited on the map.

## Edição brasileira experimental

A edição em `brasil/` reutiliza a bridge e o shell Linux do LastBook (MIT).
Os guias iniciais são resumos editoriais com referências e não cópias das páginas.
O pacote completo inclui python-libzim 3.13.1 e seus componentes GPL indicados na
lista acima. O código da adaptação está disponível no mesmo repositório, e as
licenças do wheel são preservadas em `/opt/ultimo-livro/lib/`.

O motor opcional usa llama.cpp (MIT), revisão
`dde879bc4f954b809892fd0d660515f42536394a`, compilável com `brasil/build_runtime.sh`.
Fonte exata: https://github.com/ggml-org/llama.cpp/tree/dde879bc4f954b809892fd0d660515f42536394a
A licença do motor acompanha os binários. O modelo Qwen3-0.6B-GGUF, Apache-2.0,
é baixado separadamente do repositório oficial Qwen, revisão
`23749fefcc72300e3a2ad315e1317431b06b590a`; não está embutido no instalador.
Model card e licença: https://huggingface.co/Qwen/Qwen3-0.6B-GGUF
Enciclopédias e mapas importados permanecem sob as licenças de seus fornecedores.
O aplicativo mostra as atribuições do mapa MBTiles e não redistribui os arquivos
importados. A extração de artigos em texto é uma limitação da versão alpha.

## Mapas vetoriais brasileiros (download separado)

Dados © contribuidores do OpenStreetMap, extraídos pelo Geofabrik em 16/11/2026;
recortes e nomes municipais do IBGE, malha 2025. A base derivada de mapas é
oferecida sob Open Database License 1.0 (ODbL), incluindo fonte e método de
construção em `tools/*mapas_br.py`. Isso não altera as licenças do código.
Licença: https://opendatacommons.org/licenses/odbl/1-0/
Origem e créditos: https://www.openstreetmap.org/copyright
Extrato: https://download.geofabrik.de/south-america/brazil.html
IBGE: https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/

O instalador não incorpora os gigabytes de mapas. O catálogo aponta para dados
separados, com tamanho e SHA-256, obtidos apenas por pedido da pessoa. Mapas
importados continuam sob a licença do fornecedor original.
