from pathlib import Path
import json
import shutil
root=Path(__file__).resolve().parent
packages=json.loads((root.parent/'brasil/pacotes.json').read_text())['packages']
public={ident:{key:value for key,value in p.items() if key in ('id','kind','size','edition','license','ram_gib','context')} for ident,p in packages.items()}
(root/'catalogo.js').write_text('// Gerado de brasil/pacotes.json. Não editar manualmente.\nwindow.ULTIMO_LIVRO_CATALOGO = '+json.dumps(public,ensure_ascii=False)+';\n')
(root/'dist').mkdir(exist_ok=True)
for name in ('index.html','style.css','app.js','catalogo.js'):
    shutil.copyfile(root/name,root/'dist'/name)
print('Site estático gerado em site-brasil/dist')
