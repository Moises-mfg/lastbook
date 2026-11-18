#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION=0.4.0~alpha9
FILE_VERSION=0.4.0-alpha9
OUT="$ROOT/derived/brasil-build"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
OPT="$STAGE/opt/ultimo-livro"
mkdir -p "$OPT/brasil" "$OPT/app" "$OPT/engine/setup" "$STAGE/DEBIAN" "$STAGE/usr/bin" "$STAGE/usr/share/applications" "$STAGE/usr/share/doc/ultimo-livro" "$OUT"
cp "$ROOT"/brasil/*.py "$ROOT/brasil/pacotes.json" "$OPT/brasil/"
if [ -f "$ROOT/brasil/mapas_catalogo.json" ]; then cp "$ROOT/brasil/mapas_catalogo.json" "$OPT/brasil/"; fi
cp -r "$ROOT/brasil/web" "$OPT/brasil/"
if [ -d "$ROOT/brasil/vendor" ]; then cp -r "$ROOT/brasil/vendor" "$OPT/lib"; fi
if [ -d "$ROOT/brasil/runtime" ]; then cp -r "$ROOT/brasil/runtime" "$OPT/brasil/"; fi
cp "$ROOT/app/bridge.py" "$ROOT/app/shell_linux.py" "$OPT/app/"
cp "$ROOT/engine/__init__.py" "$ROOT/engine/paths.py" "$OPT/engine/"
cp "$ROOT"/engine/setup/*.py "$ROOT/engine/setup/roots.pem" "$OPT/engine/setup/"
cp "$ROOT/LICENSE" "$ROOT/THIRD_PARTY_NOTICES.md" "$STAGE/usr/share/doc/ultimo-livro/"
printf '#!/bin/sh\nexec /usr/bin/python3 -I -B /opt/ultimo-livro/brasil/main.py "$@"\n' > "$STAGE/usr/bin/ultimo-livro"
chmod 755 "$STAGE/usr/bin/ultimo-livro"
cat > "$STAGE/usr/share/applications/ultimo-livro.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=O Último Livro
Comment=Biblioteca e preparação offline em português
Exec=ultimo-livro
Icon=accessories-dictionary
Terminal=false
Categories=Education;Utility;
DESKTOP
cat > "$STAGE/DEBIAN/control" <<CTRL
Package: ultimo-livro
Version: $VERSION
Architecture: amd64
Maintainer: Comunidade O Último Livro
Depends: python3 (>= 3.12), python3 (<< 3.15), libc6 (>= 2.39), python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1, gir1.2-soup-3.0, libgomp1, libstdc++6, libzstd1, zlib1g
Section: education
Priority: optional
Homepage: https://github.com/Moises-mfg/o-ultimo-livro
Description: Biblioteca e preparação offline em português brasileiro
 Aplicativo experimental baseado no LastBook. Guias locais, busca,
 checklist persistente e assistente opcional em CPU. Sem conta ou telemetria.
CTRL
find "$STAGE" -type d -exec chmod 755 {} +
find "$STAGE" -type f -exec chmod a+r,go-w {} +
dpkg-deb --root-owner-group --build "$STAGE" "$OUT/ultimo-livro_${FILE_VERSION}_amd64.deb"
(cd "$OUT" && sha256sum "ultimo-livro_${FILE_VERSION}_amd64.deb" > SHA256SUMS)
