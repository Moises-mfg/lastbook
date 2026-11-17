from pathlib import Path
import json
import shutil
root=Path(__file__).resolve().parent
packages=json.loads((root.parent/'brasil/pacotes.json').read_text())['packages']
public={ident:{key:value for key,value in p.items() if key in ('id','kind','size','edition','license','ram_gib','context')} for ident,p in packages.items()}
mapfile=root.parent/'brasil/mapas_catalogo.json'
mapas=json.loads(mapfile.read_text())['packages'] if mapfile.exists() else {}
mapas={ident:{k:v for k,v in p.items() if k in ('id','name','size','scope','uf','code')} for ident,p in mapas.items()}
(root/'catalogo.js').write_text('// Gerado dos catálogos de brasil/. Não editar manualmente.\nwindow.ULTIMO_LIVRO_CATALOGO = '+json.dumps(public,ensure_ascii=False)+';\nwindow.ULTIMO_LIVRO_MAPAS = '+json.dumps(mapas,ensure_ascii=False,separators=(',',':'))+';\n')
(root/'dist').mkdir(exist_ok=True)
for name in ('index.html','style.css','app.js','catalogo.js'):
    shutil.copyfile(root/name,root/'dist'/name)
print('Site estático gerado em site-brasil/dist')
