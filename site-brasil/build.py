from pathlib import Path
import shutil
root=Path(__file__).resolve().parent
(root/'dist').mkdir(exist_ok=True)
for name in ('index.html','style.css','app.js'):
    shutil.copyfile(root/name,root/'dist'/name)
print('Site estático gerado em site-brasil/dist')
