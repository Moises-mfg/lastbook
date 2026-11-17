import hashlib
import http.server
from pathlib import Path
import ssl
import tempfile
import threading
import unittest
from unittest.mock import patch
from brasil import pacotes

from app.tests.test_setup import certificate
from engine.setup import download
from tools.empacotar_mapas_br import pack

class RangeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        data=self.server.data;header=self.headers.get('Range');self.server.ranges.append(header)
        if header and self.server.mode!='ignore':
            start,end=map(int,header.removeprefix('bytes=').split('-'))
            segment=data[start:end+1]
            self.send_response(206)
            self.send_header('Content-Range',f'bytes {start+(1 if self.server.mode=="wrong" else 0)}-{end}/{len(data)}')
        else:
            segment=data;self.send_response(200)
        self.send_header('ETag','"snapshot-1"');self.send_header('Content-Length',str(len(segment)));self.end_headers()
        try:self.wfile.write(segment)
        except OSError:pass

class BoundedRange(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        key,crt=certificate(self.root)
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),RangeHandler)
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(crt,key)
        self.server.socket=ctx.wrap_socket(self.server.socket,server_side=True)
        self.ctx=ssl.create_default_context(cafile=str(crt));self.server.mode='ok';self.server.ranges=[]
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.url=f'https://127.0.0.1:{self.server.server_address[1]}/maps'
        self.segment=b'Mapa de um municipio\n'*40000
        self.offset=12345;self.server.data=b'x'*self.offset+self.segment+b'z'*17000
    def tearDown(self):self.server.shutdown();self.server.server_close();self.tmp.cleanup()
    def downloader(self,control,progress=lambda *args:None):
        return download.Download(self.url,self.root/'city.ulmap',len(self.segment),hashlib.sha256(self.segment).hexdigest(),control,progress,
            allowed={'127.0.0.1'},context=self.ctx,offset=self.offset,container_size=len(self.server.data))
    def test_only_selected_segment_is_downloaded_and_can_resume(self):
        control=download.Control()
        def pause(done,total,phase):
            if done:control.stop('paused')
        with self.assertRaises(download.Stopped):self.downloader(control,pause).run()
        self.downloader(download.Control()).run()
        self.assertEqual((self.root/'city.ulmap').read_bytes(),self.segment)
        self.assertTrue(all(h and h.endswith('-'+str(self.offset+len(self.segment)-1)) for h in self.server.ranges))
        self.assertGreater(int(self.server.ranges[-1].split('=')[1].split('-')[0]),self.offset)
    def test_ignored_or_wrong_range_never_activates_map(self):
        for mode in ('ignore','wrong'):
            with self.subTest(mode=mode):
                self.server.mode=mode
                with self.assertRaises(download.Failed):self.downloader(download.Control()).run()
                self.assertFalse((self.root/'city.ulmap').exists())
    def test_large_map_parts_are_verified_reassembled_and_resumable(self):
        content=b'mapa nacional teste'*10000;source=self.root/'full.ulmap';source.write_bytes(content)
        output=self.root/'multi';manifest=pack([{'id':'map-full','file':source.name,'kind':'map','path':str(source)}],output,limit=65536)
        item=manifest['packages']['map-full'];self.assertGreater(len(item['parts']),1)
        # Servidor de teste entrega os volumes reais gerados pelo empacotador.
        original=download.Download
        def local(url,*args,**kwargs):
            part=next(p for p in item['parts'] if p['url']==url)
            self.server.data=(output/part['container_file']).read_bytes()
            return original(self.url,*args,allowed={'127.0.0.1'},context=self.ctx,**kwargs)
        target=self.root/'installed.ulmap';control=download.Control()
        def pause(done,total,phase):
            if done>65536:control.stop('paused')
        with patch('brasil.pacotes.download.Download',local):
            with self.assertRaises(download.Stopped):pacotes.obtain(item,target,control,pause)
            self.assertFalse(target.exists());self.assertGreater(pacotes.partial_bytes(target,item),0)
            pacotes.obtain(item,target,download.Control(),lambda *a:None)
        self.assertEqual(target.read_bytes(),content)
        self.assertFalse(list(self.root.glob('installed.ulmap.seg-*')))
        self.assertTrue(all(c['size']<=65536 for c in manifest['containers'].values()))

    def test_archive_manifest_offsets_match_bytes(self):
        one=self.root/'one.ulmap';one.write_bytes(b'first'*5000)
        two=self.root/'two.ulmap';two.write_bytes(b'second'*4000)
        result=pack([{'id':'map-a','file':one.name,'kind':'map','path':str(one)}, {'id':'map-b','file':two.name,'kind':'map','path':str(two)}],self.root/'pack',limit=65536)
        for item in result['packages'].values():
            with (self.root/'pack'/item['container_file']).open('rb') as f:
                f.seek(item['offset']);data=f.read(item['size'])
            self.assertEqual(hashlib.sha256(data).hexdigest(),item['sha256'])
        self.assertTrue(all(c['size']<=65536 for c in result['containers'].values()))

if __name__=='__main__':unittest.main()
