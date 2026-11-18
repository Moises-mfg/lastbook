import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from brasil.core import Store
from brasil import regiao_camadas as camadas


class RegiaoCamadasTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.store = Store(self.folder / 'dados')
        self.path = self.folder / 'camada.geojson'
        self.body = {'ibge': '3550308', 'tipo': 'saude', 'titulo': 'Unidades de saúde',
                     'fonte': 'https://dados.prefeitura.example/saude', 'data': '2026-11-18'}
        self.point = {'type': 'Feature', 'properties': {'nome': 'UBS Centro', 'telefone': 'não importar'},
                      'geometry': {'type': 'Point', 'coordinates': [-46.6, -23.5]}}
        self.ring = [[-46.6, -23.5], [-46.5, -23.5], [-46.5, -23.4], [-46.6, -23.5]]

    def write(self, features=None, **extra):
        document = {'type': 'FeatureCollection', 'features': features if features is not None else [self.point]}
        document.update(extra)
        self.path.write_text(json.dumps(document), encoding='utf-8')
        return self.path

    def test_import_persists_sanitized_geometry_and_informed_origin_without_network(self):
        self.write()
        with patch('urllib.request.urlopen', side_effect=AssertionError('Rede proibida')):
            result = camadas.importar(self.store, self.body, self.path)
        layer = result['camadas'][0]
        self.assertIn('fornecidas pelo usuário', result['mensagem'])
        self.assertEqual(set(layer), {'tipo', 'titulo', 'fonte', 'data', 'features'})
        self.assertEqual(layer['fonte'], self.body['fonte'])
        self.assertEqual(layer['data'], self.body['data'])
        self.assertEqual(layer['features'], [{'nome': 'UBS Centro', 'geometry': self.point['geometry']}])
        self.path.unlink()
        self.assertEqual(camadas.listar(Store(self.store.folder), '3550308'), [layer])

    def test_cancel_invalid_file_and_invalid_import_preserve_previous_layer(self):
        self.write()
        before = camadas.importar(self.store, self.body, self.path)['camadas']
        result = camadas.importar(self.store, {'ibge': '3550308'}, None)
        self.assertTrue(result['cancelado'])
        self.assertEqual(result['camadas'], before)
        for contents in (b'{invalid', b'\xff\xfe', b'[]', b'{}'):
            self.path.write_bytes(contents)
            with self.subTest(contents=contents), self.assertRaises(ValueError):
                camadas.importar(self.store, self.body, self.path)
            self.assertEqual(camadas.listar(self.store, '3550308'), before)
        with self.assertRaises(OSError):
            camadas.importar(self.store, self.body, self.folder / 'ausente')
        self.assertEqual(camadas.listar(self.store, '3550308'), before)

    def test_replacement_and_deletion_are_scoped_to_type_and_municipality(self):
        self.write()
        for city, kind in [('3550308', 'saude'), ('3550308', 'abrigos'), ('3304557', 'saude')]:
            camadas.importar(self.store, dict(self.body, ibge=city, tipo=kind), self.path)
        camadas.importar(self.store, dict(self.body, titulo='Revisada'), self.path)
        current = camadas.listar(self.store, '3550308')
        self.assertEqual(len(current), 2)
        self.assertEqual(next(layer['titulo'] for layer in current if layer['tipo'] == 'saude'), 'Revisada')
        result = camadas.excluir(self.store, {'ibge': '3550308', 'tipo': 'saude'})
        self.assertEqual([layer['tipo'] for layer in result['camadas']], ['abrigos'])
        self.assertEqual(len(camadas.listar(self.store, '3304557')), 1)
        self.assertEqual(camadas.excluir(self.store, {'ibge': '3550308', 'tipo': 'saude'})['camadas'], result['camadas'])

    def test_invalid_coordinates_and_mixed_types_are_rejected(self):
        coords = [[float('nan'), 0], [0, float('inf')], [float('-inf'), 0],
                  [181, 0], [0, -91], [True, 0], ['1', 0], [0, 0, 4], [0], None]
        for point in coords:
            feature = copy.deepcopy(self.point)
            feature['geometry']['coordinates'] = point
            self.write([feature])
            with self.subTest(coordinates=point), self.assertRaises(ValueError):
                camadas.importar(self.store, self.body, self.path)
        polygon = {'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Polygon', 'coordinates': [self.ring]}}
        self.write([self.point, polygon])
        for kind in camadas.TIPOS:
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                camadas.importar(self.store, dict(self.body, tipo=kind), self.path)
        self.assertEqual(camadas.listar(self.store, '3550308'), [])

    def test_risk_polygons_multipolygons_and_ring_validation(self):
        risk = dict(self.body, tipo='risco')
        geometries = [{'type': 'Polygon', 'coordinates': [self.ring]},
                      {'type': 'MultiPolygon', 'coordinates': [[self.ring], [self.ring]]}]
        for geometry in geometries:
            self.write([{'type': 'Feature', 'properties': None, 'geometry': geometry}])
            layer = camadas.importar(self.store, risk, self.path)['camadas'][0]
            self.assertEqual(layer['features'][0], {'nome': 'Área 1', 'geometry': geometry})
        invalid = [[], [[]], [self.ring[:-1]], [[[0, 0], [0, 0], [0, 0], [0, 0]]]]
        for coordinates in invalid:
            self.write([{'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': coordinates}}])
            with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                camadas.importar(self.store, risk, self.path)

    def test_origin_metadata_crs_and_names_are_validated(self):
        self.write()
        for key, value in [('ibge', '../x'), ('ibge', 3550308), ('tipo', 'outra'), ('tipo', []),
                           ('titulo', ''), ('titulo', 'x'*161), ('titulo', '\ud800'),
                           ('fonte', 'http://example.org'), ('fonte', 'https://nome:senha@example.org'),
                           ('fonte', 'https://example.org:inválida'), ('fonte', 'https://example.org/\n'),
                           ('fonte', 'https://example.org\\@outro.org'),
                           ('data', '2026-02-30'), ('data', '20261118')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                camadas.importar(self.store, dict(self.body, **{key:value}), self.path)
        self.write(crs={'type': 'name', 'properties': {'name': 'EPSG:3857'}})
        with self.assertRaises(ValueError):
            camadas.importar(self.store, self.body, self.path)
        self.write(crs={'type': 'name', 'properties': {'name': 'EPSG:4326'}})
        camadas.importar(self.store, self.body, self.path)
        bad = copy.deepcopy(self.point)
        bad['properties']['nome'] = {'html': '<script>'}
        self.write([bad])
        with self.assertRaises(ValueError):
            camadas.importar(self.store, self.body, self.path)

    def test_byte_feature_and_vertex_limits(self):
        self.write()
        with patch.object(camadas, 'MAX_BYTES', 10), self.assertRaises(ValueError):
            camadas.importar(self.store, self.body, self.path)
        self.write([self.point, self.point])
        with patch.object(camadas, 'MAX_FEATURES', 1), self.assertRaises(ValueError):
            camadas.importar(self.store, self.body, self.path)
        with patch.object(camadas, 'MAX_VERTICES', 1), self.assertRaises(ValueError):
            camadas.importar(self.store, self.body, self.path)
        self.assertEqual(camadas.listar(self.store, '3550308'), [])

    def test_database_failure_rolls_back_replacement(self):
        self.write()
        before = camadas.importar(self.store, self.body, self.path)['camadas']
        with self.store.db() as db:
            db.execute("CREATE TRIGGER fail_layer BEFORE INSERT ON regiao_camadas BEGIN SELECT RAISE(ABORT, 'falha'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            camadas.importar(self.store, dict(self.body, titulo='Nova'), self.path)
        self.assertEqual(camadas.listar(self.store, '3550308'), before)

    def test_listing_validates_stored_geometry(self):
        self.write()
        camadas.importar(self.store, self.body, self.path)
        with self.store.db() as db:
            db.execute("UPDATE regiao_camadas SET dados='{}'")
        with self.assertRaisesRegex(ValueError, 'Camada local inválida'):
            camadas.listar(self.store, '3550308')
        self.assertEqual(camadas.excluir(self.store, {'ibge': '3550308', 'tipo': 'saude'})['camadas'], [])


if __name__ == '__main__':
    unittest.main()
