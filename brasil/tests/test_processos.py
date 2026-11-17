import unittest
from app.process_tree import window_processes

class WindowMemory(unittest.TestCase):
    def test_model_process_and_its_children_are_outside_renderer_budget(self):
        parents={11:10,12:11,13:10,14:13,99:1}
        names={10:'UltimoLivro.exe',11:'msedgewebview2.exe',12:'msedgewebview2.exe',13:'LLAMA-COMPLETION.EXE',14:'worker.exe',99:'other.exe'}
        self.assertEqual(window_processes(10,parents,names,{'lastbook-llm.exe','llama-completion.exe'}),{10,11,12})
        self.assertEqual(window_processes(10,parents,names,{'lastbook-llm.exe'}),{10,11,12,13,14})
    def test_renderer_descendants_remain_counted_and_cycles_terminate(self):
        self.assertEqual(window_processes(1,{1:2,2:1,3:2},{2:'renderer.exe',3:'gpu.exe'}),{1,2,3})
