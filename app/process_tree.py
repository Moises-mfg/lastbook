"""Seleção dos processos da janela, separada dos motores locais de IA."""
def window_processes(root,parents,names,excluded_names=()):
    excluded={name.casefold() for name in excluded_names}
    children={}
    for pid,parent in parents.items():children.setdefault(parent,[]).append(pid)
    found={root};pending=[root]
    while pending:
        for pid in children.get(pending.pop(),[]):
            if pid in found or names.get(pid,'').casefold() in excluded:continue
            found.add(pid);pending.append(pid)
    return found
