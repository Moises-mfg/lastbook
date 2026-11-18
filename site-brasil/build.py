from pathlib import Path
import json
import shutil
import sys
root=Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent))
from brasil.fontes import RECURSOS
from brasil.catalogo import GUIAS, COMPRAS
from brasil.guias_pdf import catalog as pdf_catalog
from brasil.situacoes import SITUACOES
acervo = {'pdfs': [{k: g[k] for k in ('id', 'titulo', 'descricao')} for g in pdf_catalog()],
          'guias': [{k: g[k] for k in ('id', 'titulo')} for g in GUIAS],
          'checklist': len(COMPRAS),
          'situacoes': [{k: g[k] for k in ('id', 'titulo', 'resumo')} for g in SITUACOES]}
packages=json.loads((root.parent/'brasil/pacotes.json').read_text(encoding='utf-8'))['packages']
public={ident:{key:value for key,value in p.items() if key in ('id','kind','size','edition','license','ram_gib','context')} for ident,p in packages.items()}
mapfile=root.parent/'brasil/mapas_catalogo.json'
mapas=json.loads(mapfile.read_text(encoding='utf-8'))['packages'] if mapfile.exists() else {}
recursos=RECURSOS
mapas={ident:{k:v for k,v in p.items() if k in ('id','name','size','scope','uf','code')} for ident,p in mapas.items()}
(root/'catalogo.js').write_text('// Gerado dos catálogos de brasil/. Não editar manualmente.\nwindow.ULTIMO_LIVRO_CATALOGO = '+json.dumps(public,ensure_ascii=False)+';\nwindow.ULTIMO_LIVRO_MAPAS = '+json.dumps(mapas,ensure_ascii=False,separators=(',',':'))+';\nwindow.ULTIMO_LIVRO_FONTES = '+json.dumps(recursos,ensure_ascii=False)+';\nwindow.ULTIMO_LIVRO_ACERVO = '+json.dumps(acervo,ensure_ascii=False)+';\n', encoding='utf-8')
(root/'dist').mkdir(exist_ok=True)
for name in ('index.html','style.css','app.js','catalogo.js','downloads.js','plano-familiar.html','plano-familiar.css','plano-familiar.js'):
    shutil.copyfile(root/name,root/'dist'/name)
print('Site estático gerado em site-brasil/dist')
