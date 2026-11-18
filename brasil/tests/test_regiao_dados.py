import csv
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from brasil.regiao_dados import historico, _base, ARQUIVO
from tools import build_historico_atlas as build


class HistoricoAtlasTests(unittest.TestCase):
    def csv(self, rows):
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=sorted(build.REQUIRED), delimiter=';')
        writer.writeheader()
        for index, row in enumerate(rows):
            value = {'Protocolo_S2iD': f'protocolo-{index}', 'Nome_Municipio': 'Município de teste',
                     'Sigla_UF': 'PA', 'Data_Evento': '01/01/2000', 'Cod_Cobrade': '12100', 'Cod_IBGE_Mun': '1501402'}
            value.update(row)
            writer.writerow(value)
        stream.seek(0)
        return stream

    def test_cobrade_categories_and_exclusions(self):
        rows = [{'Cod_Cobrade': code} for category in build.CATEGORIAS for code in category['cobrade']]
        rows.extend({'Cod_Cobrade': code} for code in ('14140', '13214', '23120', '13322', '24200'))
        result = build.agregar(self.csv(rows))
        self.assertEqual(result['registros_fonte'], 21)
        self.assertEqual(result['registros_recorte'], 16)
        self.assertEqual([value[0] for value in result['municipios']['1501402'][2]], [3, 8, 2, 2, 1])

    def test_aggregation_uses_ibge_and_event_year_and_normalizes_uf(self):
        result = build.agregar(self.csv([
            {'Data_Evento': '01/02/2025', 'Sigla_UF': 'pa'},
            {'Data_Evento': '31/12/1991', 'Nome_Municipio': 'Variação do nome'},
            {'Cod_IBGE_Mun': '1500800', 'Nome_Municipio': 'Outro município', 'Cod_Cobrade': '14120'},
            {'Cod_Cobrade': '13214', 'Data_Evento': '01/01/2005'},
        ]))
        self.assertEqual(result['municipios']['1501402'][1], 'PA')
        self.assertEqual(result['municipios']['1501402'][2][0], [2, 1991, 2025])
        self.assertEqual(result['municipios']['1500800'][2][2], [1, 2000, 2000])

    def test_import_rejects_ambiguous_or_invalid_rows(self):
        for rows in ([{'Protocolo_S2iD': 'duplicado'}] * 2,
                     [{'Cod_IBGE_Mun': '123'}], [{'Data_Evento': '31/02/2020'}],
                     [{'Data_Evento': '01/01/2026'}], [{'Cod_Cobrade': 'enchente'}],
                     [{'Sigla_UF': 'PA'}, {'Sigla_UF': 'SP'}], []):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                build.agregar(self.csv(rows))
        with self.assertRaises(ValueError):
            build.agregar(io.StringIO('municipio;data\nx;2020\n'))

    def test_importer_checks_hash_before_parsing(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'alterado.csv'
            source.write_text('outros dados')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                build.construir(source)

    def test_atomic_write_keeps_previous_file_on_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'atlas.json'
            output.write_text('anterior')
            with patch.object(build.os, 'replace', side_effect=OSError('falha')):
                with self.assertRaises(OSError):
                    build.escrever(output, {'municipios': {}})
            self.assertEqual(output.read_text(), 'anterior')
            self.assertFalse(list(Path(folder).glob('.atlas-*')))

    def test_packaged_dataset_matches_official_snapshot_totals(self):
        base = _base()
        self.assertEqual(base['sha256'], build.SOURCE_SHA256)
        self.assertEqual(base['registros_fonte'], 76190)
        self.assertEqual(base['registros_recorte'], 57224)
        self.assertEqual(len(base['municipios']), 5256)
        self.assertEqual(base['periodo'], {'inicio': 1991, 'fim': 2025})
        totals = [sum(m[2][index][0] for m in base['municipios'].values()) for index in range(5)]
        self.assertEqual(totals, [18428, 1771, 33493, 3419, 113])
        for municipality in base['municipios'].values():
            for count, first, last in municipality[2]:
                if count:
                    self.assertTrue(1991 <= first <= last <= 2025)
                else:
                    self.assertEqual((first, last), (None, None))
        self.assertLess(ARQUIVO.stat().st_size, 600000)

    def test_pure_lookup_reports_actual_summary_and_provenance(self):
        result = historico('4314902')
        self.assertTrue(result['disponivel'])
        self.assertEqual(result['municipio'], 'Porto Alegre')
        self.assertEqual(result['total_registros'], 10)
        self.assertEqual(result['categorias'][0]['registros'], 8)
        self.assertEqual(result['categorias'][0]['primeiro_ano'], 2015)
        self.assertEqual(result['categorias'][0]['ultimo_ano'], 2025)
        self.assertEqual(result['arquivo_url'], build.SOURCE_URL)
        self.assertIn('não é previsão', result['aviso'])
        same = historico(4314902)
        self.assertEqual(result, same)
        result['categorias'][0]['cobrade'].clear()
        result['periodo']['inicio'] = 0
        self.assertEqual(historico('4314902'), same)

    def test_missing_code_is_absence_not_risk_classification(self):
        for code in ('9999999', '../../arquivo', True, None, '123', [], 1.5):
            result = historico(code)
            self.assertFalse(result['disponivel'])
            self.assertEqual(result['total_registros'], 0)
            self.assertIsNone(result['municipio'])
            self.assertIn('não significa ausência de risco', result['aviso'])
            self.assertNotIn('risco', result)


if __name__ == '__main__':
    unittest.main()
