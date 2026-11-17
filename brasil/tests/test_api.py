import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'app'))
import bridge
from brasil import main
from brasil.core import Store

class BridgeAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=bridge.Bridge(main,'buffer',bridge.ORIGIN_WINDOWS)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        main.STORE=Store(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def call(self,method,path,body=None,key=True):
        data=json.dumps(body).encode() if body is not None else None
        headers={bridge.KEY_HEADER:self.b.key} if key else {}
        if data: headers['Content-Type']='application/json'
        done=threading.Event();box=[]
        self.b.fetch(method,self.b.origin+path,headers,data,lambda r:(box.append(r),done.set()))
        self.assertTrue(done.wait(5),'bridge não respondeu')
        r=box[0];out=(r.status,r.body);r.release();return out

    def test_home_and_state_are_local(self):
        status,body=self.call('GET','/')
        self.assertEqual(status,200)
        self.assertIn('pt-BR'.encode(),body)
        status,body=self.call('GET','/api/brasil/state')
        self.assertEqual(status,200)
        self.assertEqual(len(json.loads(body)['estados']),27)

    def test_post_requires_bridge_secret_and_validated_choices(self):
        status,_=self.call('POST','/api/brasil/choices',{'perfil':'leve'},key=False)
        self.assertEqual(status,403)
        status,body=self.call('POST','/api/brasil/choices',{'perfil':'leve'})
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['modelo'],'qwen3-0.6b')
        status,_=self.call('POST','/api/brasil/choices',{'estados':['US']})
        self.assertEqual(status,400)

    def test_refuses_static_traversal(self):
        status,_=self.call('GET','/ui/../../brasil/core.py')
        self.assertIn(status,(400,403,404))

if __name__=='__main__':unittest.main()
