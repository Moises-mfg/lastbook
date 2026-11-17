"""Coleta avisos e fontes das versões efetivamente usadas pelo empacotamento.

Não substitui licenças por uma tabela de nomes. Os textos são copiados da
instalação, do wheel/sdist ou do release oficial exato; os downloads ficam
identificados por URL e SHA-256 no manifesto entregue com o aplicativo.
"""
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import ssl
import sys
import sysconfig
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LLAMA_REV = 'dde879bc4f954b809892fd0d660515f42536394a'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def legal_file(name):
    name = PurePosixPath(name).name.lower()
    return name.startswith(('license', 'licence', 'copying', 'copyright', 'notice', 'authors')) or name in ('legal.txt', 'thirdpartynotices.txt', 'crtlicense.txt')


class Collector:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.directory = self.root / 'derived/desktop-licenses'
        self.cache = self.root / 'derived/desktop-source-cache'
        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.items = []
        self.sources = []

    def download(self, name, url, expected=None):
        path = self.cache / name
        receipt = path.with_name(path.name + '.download.json')
        if path.exists() and receipt.exists():
            saved = json.loads(receipt.read_text(encoding='utf-8'))
            if saved['url'] == url and digest(path) == saved['sha256'] and (not expected or expected == saved['sha256']):
                return path
        temporary = path.with_name(path.name + '.part')
        request = urllib.request.Request(url, headers={'User-Agent': 'UltimoLivro-source-collector/1'})
        with urllib.request.urlopen(request, timeout=180) as response, temporary.open('wb') as stream:
            shutil.copyfileobj(response, stream)
        actual = digest(temporary)
        if expected and actual != expected:
            temporary.unlink()
            raise ValueError(f'SHA-256 inesperado: {name}')
        temporary.replace(path)
        receipt.write_text(json.dumps({'url': url, 'sha256': actual}, indent=2), encoding='utf-8')
        return path

    def put(self, component, name, data):
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Caminho de aviso inválido.')
        path = self.directory / component / Path(*relative.parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path.relative_to(self.directory))

    def archive(self, component, version, url, filename, expected=None, require_license=True):
        source = self.download(filename, url, expected)
        notices = []
        if zipfile.is_zipfile(source):
            with zipfile.ZipFile(source) as archive:
                for item in archive.infolist():
                    if not item.is_dir() and legal_file(item.filename) and item.file_size < 2_000_000:
                        notices.append(self.put(component, item.filename, archive.read(item)))
        else:
            with tarfile.open(source, 'r:*') as archive:
                for item in archive:
                    if item.isfile() and legal_file(item.name) and item.size < 2_000_000:
                        with archive.extractfile(item) as stream:
                            notices.append(self.put(component, item.name, stream.read()))
        if require_license and not any('licen' in name.lower() or 'copying' in name.lower() for name in notices):
            raise ValueError(f'Fonte de {component} não contém licença reconhecida.')
        self.items.append({'componente': component, 'versao': version, 'url': url,
                           'sha256_fonte': digest(source), 'arquivo_fonte': source.name, 'avisos': notices})
        self.sources.append(source)
        return source

    def python_runtime(self):
        version = platform.python_version()
        source = self.archive('Python', version, f'https://www.python.org/ftp/python/{version}/Python-{version}.tar.xz', f'Python-{version}.tar.xz')
        candidates = [Path(sys.base_prefix) / 'LICENSE.txt', Path(sys.base_prefix) / 'LICENSE',
                      Path(sysconfig.get_path('stdlib')) / 'LICENSE.txt']
        license_path = next((p for p in candidates if p.is_file()), None)
        if license_path is None:
            with tarfile.open(source) as archive:
                with archive.extractfile(f'Python-{version}/LICENSE') as stream:
                    data = stream.read()
            origin = f'{source.name}:Python-{version}/LICENSE'
        else:
            data, origin = license_path.read_bytes(), str(license_path)
        if b'PYTHON SOFTWARE FOUNDATION LICENSE' not in data.upper():
            raise ValueError('O arquivo identificado não contém a licença PSF completa.')
        notice = self.put('Python', 'LICENSE-runtime.txt', data)
        self.items.append({'componente': 'Python instalado', 'versao': version,
                           'origem': origin, 'avisos': [notice]})
        if sys.platform == 'win32':
            # A receita do mesmo CPython identifica a libffi distribuída em DLL;
            # não inferir a versão da ABI "libffi-8.dll".
            with tarfile.open(source) as archive:
                with archive.extractfile(f'Python-{version}/PCbuild/python.props') as stream:
                    props = stream.read().decode('utf-8')
            match = re.search(r'<libffiDir\b[^>]*>[^<]*libffi-([0-9.]+)', props)
            if not match:
                raise ValueError('A receita do Python Windows não identifica libffi.')
            ffi = match.group(1)
            self.archive('libffi-Python-Windows', ffi, f'https://codeload.github.com/libffi/libffi/tar.gz/refs/tags/v{ffi}', f'libffi-{ffi}.tar.gz')

    def distributions(self, additional=()):
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name
        pending = ['libzim', 'pyinstaller', *additional]
        try:
            metadata.distribution('setuptools')
            pending.append('setuptools')
        except metadata.PackageNotFoundError:
            pass
        if sys.platform == 'darwin':
            pending += ['pyobjc-core', 'pyobjc-framework-Cocoa', 'pyobjc-framework-WebKit']
        elif sys.platform == 'win32':
            pending += ['pythonnet', 'clr_loader', 'cffi']
        done = set()
        while pending:
            name = pending.pop()
            normalized = canonicalize_name(name)
            if normalized in done:
                continue
            dist = metadata.distribution(name)
            done.add(normalized)
            version = dist.version
            component = 'python-' + normalized
            for file in dist.files or []:
                if legal_file(str(file)) and '..' not in PurePosixPath(str(file)).parts:
                    path = Path(dist.locate_file(file))
                    if path.is_file():
                        self.put(component, str(file), path.read_bytes())
            self.put(component, 'METADATA', dist.read_text('METADATA').encode('utf-8'))
            for requirement in dist.requires or []:
                requirement = Requirement(requirement)
                if requirement.marker is None or requirement.marker.evaluate({'extra': ''}):
                    pending.append(requirement.name)
            with urllib.request.urlopen(f'https://pypi.org/pypi/{normalized}/{version}/json', timeout=90) as response:
                info = json.load(response)
            sdists = [entry for entry in info['urls'] if entry['packagetype'] == 'sdist']
            if len(sdists) != 1:
                raise ValueError(f'Sdist oficial único não encontrado: {normalized} {version}')
            source = sdists[0]
            self.archive(component, version, source['url'], source['filename'], source['digests']['sha256'])
        self.put('', 'DISTRIBUICOES-PYTHON.json', json.dumps(sorted(done)).encode('utf-8'))
        return sorted(done)

    def native_zim(self):
        import libzim
        versions = dict(libzim.get_versions())
        self.put('libzim', 'VERSOES-NATIVAS.json', json.dumps(versions, indent=2).encode('utf-8'))
        repositories = {'libzim': ('openzim/libzim', ''), 'libzstd': ('facebook/zstd', 'v'),
                        'liblzma': ('tukaani-project/xz', 'v')}
        for name, version in versions.items():
            if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)+', version):
                raise ValueError(f'Versão nativa sem release identificável: {name} {version}')
            if name in repositories:
                repo, prefix = repositories[name]
                url = f'https://codeload.github.com/{repo}/tar.gz/refs/tags/{prefix}{version}'
            elif name == 'libicu':
                parts = version.split('.')
                while len(parts) > 2 and parts[-1] == '0':
                    parts.pop()
                url = 'https://codeload.github.com/unicode-org/icu/tar.gz/refs/tags/release-' + '-'.join(parts)
            elif name == 'libxapian':
                url = f'https://oligarchy.co.uk/xapian/{version}/xapian-core-{version}.tar.xz'
            else:
                raise ValueError(f'Falta identificar a fonte oficial de {name} {version}')
            suffix = '.tar.xz' if name == 'libxapian' else '.tar.gz'
            self.archive(name, version, url, name + '-' + version + suffix)

    def openssl(self):
        match = re.match(r'OpenSSL (\d+\.\d+\.\d+[a-z]?)\b', ssl.OPENSSL_VERSION)
        if not match:
            raise ValueError('Versão OpenSSL efetiva não identificável: ' + ssl.OPENSSL_VERSION)
        version = match.group(1)
        tag = 'OpenSSL_' + version.replace('.', '_') if version.startswith('1.') else 'openssl-' + version
        self.archive('OpenSSL', version, f'https://codeload.github.com/openssl/openssl/tar.gz/refs/tags/{tag}', f'openssl-{version}.tar.gz')

    def application(self):
        self.archive('llama.cpp', LLAMA_REV, f'https://codeload.github.com/ggml-org/llama.cpp/tar.gz/{LLAMA_REV}', f'llama.cpp-{LLAMA_REV}.tar.gz')
        revision = os.environ.get('GITHUB_SHA', '')
        repository = os.environ.get('GITHUB_REPOSITORY', 'Moises-mfg/lastbook')
        if not re.fullmatch(r'[0-9a-f]{40}', revision):
            raise ValueError('GITHUB_SHA deve identificar o código-fonte exato da entrega.')
        self.archive('O-Ultimo-Livro', revision, f'https://codeload.github.com/{repository}/tar.gz/{revision}', f'ultimo-livro-fonte-{revision}.tar.gz')

    def finish(self, version, source_archive=True):
        manifest = {'plataforma': sys.platform, 'arquitetura': platform.machine(),
                    'python': sys.version, 'componentes': self.items}
        self.put('', 'MANIFESTO.json', json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8'))
        text = (
            'LICENÇAS E FONTES — O ÚLTIMO LIVRO\n\n'
            'Cada componente conserva seus termos; o LICENSE MIT da adaptação não '
            'relicencia libzim ou outros componentes. Python-libzim é GPL-3.0-or-later; '
            'as permissões MIT do código próprio são compatíveis com sua distribuição.\n'
            'Os arquivos-fontes exatos e receitas originais acompanham esta release no '
            f'arquivo ultimo-livro_{version}_fontes-{sys.platform}-{platform.machine()}.zip. '
            'Esse arquivo deve permanecer disponível gratuitamente junto aos binários.\n'
            'MANIFESTO.json identifica versões efetivas, endereços e SHA-256. '
            'As receitas do aplicativo estão em brasil/build_desktop.py, desktop.spec, '
            'build_runtime.py e .github/workflows/brasil-desktop.yml no arquivo do fork. '
            'Os sdists python-libzim incluem setup.py e a receita de download do libzim; '
            'os releases nativos incluem suas receitas de compilação.\n'
            'Componentes Microsoft mantêm seus próprios termos; este arquivo não '
            'afirma fornecer código-fonte de componentes proprietários nem os '
            'relicencia sob BSD, MIT ou GPL. Consulte seus registros no manifesto.\n'
            'Python, modelos e componentes de terceiros não foram relicenciados. '
            'Modelos, enciclopédias e mapas não integram este pacote de fontes.\n'
        )
        self.put('', 'LEIA-ME.txt', text.encode('utf-8'))
        if not source_archive:
            return None
        out = self.root / 'derived/desktop-release'
        out.mkdir(parents=True, exist_ok=True)
        target = out / f'ultimo-livro_{version}_fontes-{sys.platform}-{platform.machine()}.zip'
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_STORED) as archive:
            for source in sorted(set(self.sources)):
                archive.write(source, 'fontes/' + source.name)
            for notice in sorted(self.directory.rglob('*')):
                if notice.is_file():
                    archive.write(notice, 'licencas/' + str(notice.relative_to(self.directory)).replace(os.sep, '/'))
        return target


def collect(version):
    collector = Collector()
    collector.python_runtime()
    collector.distributions()
    collector.native_zim()
    collector.openssl()
    collector.application()
    return collector
