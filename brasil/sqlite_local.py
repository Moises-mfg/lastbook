"""Conexões curtas que liberam os arquivos ao terminar cada operação."""
import sqlite3

class Connection(sqlite3.Connection):
    def __exit__(self,kind,value,traceback):
        try:return super().__exit__(kind,value,traceback)
        finally:self.close()
