import csv
import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gerar_plano import candidates
from resumir_relatorios import checksum,load,summarize

SOURCE=(ROOT/'MQL5/Experts/ModeloD_Historico_Diagnostico/Diagnostico_Cobertura_Historica.mq5').read_text()
HEADER=re.search(r'return "(Task;[^"\n]+)";',SOURCE).group(1).split(';')


def record(task=0,status='PENDENTE_OU_DIVERGENTE'):
    row={k:'' for k in HEADER}
    row.update(Task=str(task),Data='2026.09.01',SimboloConsultado='WINV26',Rodada='TESTE_SINTETICO',
               TicksEstado=status,CandidatoTecnicoSemVinculos='NAO',DadosPrimeiroPiloto='PENDENTE')
    body=';'.join(row[k] for k in HEADER[:-1])
    return body+';'+checksum(body)


class ProtocolTests(unittest.TestCase):
    def test_plan_all_dates_and_no_false_proof(self):
        with (ROOT/'MQL5/Files/PLANO_HC100_877.csv').open(encoding='utf-8') as stream:
            rows=list(csv.DictReader(stream,delimiter=';'))
        self.assertEqual(len(rows),877)
        self.assertEqual(len({r['Data'] for r in rows}),877)
        self.assertTrue(all(len(r)==19 and not r['ContratoConfirmado'] and not r['AjusteB3'] and r['FusoBRTConfirmado']=='NAO' for r in rows))
        september=[r for r in rows if '2026.09.01'<=r['Data']<='2026.09.21']
        self.assertEqual(len(september),14)
        self.assertTrue(all(r['Candidato1']=='WINV26' and r['Candidato2']=='WINZ26' for r in september))
        self.assertEqual(rows[0]['Data'],'2023.03.01')
        self.assertEqual(rows[-1]['Data'],'2026.09.21')

    def test_nominal_candidates_are_auditable(self):
        self.assertEqual(candidates(date(2023,3,1))[0][0],'WINJ23')
        self.assertEqual(candidates(date(2026,9,21))[0][0],'WINV26')

    def test_resume_latest_complete_row_wins(self):
        self.assertEqual(len(HEADER),35)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sintetico_DIAS.csv'
            path.write_text(';'.join(HEADER)+'\n'+record()+'\n'+record(status='ESTAVEL_COM_NEGOCIOS_M1_COMPATIVEL')+'\n')
            summary,rows=summarize([path])
            self.assertEqual(len(rows),1)
            self.assertEqual(summary['tarefas_concluidas'],1)
            self.assertEqual(summary['candidatos_a_piloto_conforme_declaracoes'],0)
            self.assertEqual(rows[0]['TicksEstado'],'ESTAVEL_COM_NEGOCIOS_M1_COMPATIVEL')

    def test_truncation_and_changed_data_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sintetico_DIAS.csv'
            for value in (record()[:-3],record().replace('WINV26','WINZ26')):
                path.write_text(';'.join(HEADER)+'\n'+value+'\n')
                with self.assertRaises(ValueError):load(path)

    def test_reused_task_with_different_identity_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sintetico_DIAS.csv'
            altered=record().split(';')[:-1];altered[1]='2026.09.02';body=';'.join(altered)
            path.write_text(';'.join(HEADER)+'\n'+record()+'\n'+body+';'+checksum(body)+'\n')
            with self.assertRaises(ValueError):load(path)

    def test_unicode_checksum_handles_utf16_units(self):
        self.assertNotEqual(checksum('índice'),checksum('indice'))
        self.assertNotEqual(checksum('A😀'),checksum('A'))

    def test_source_has_no_order_transport(self):
        self.assertFalse(re.search(r'\b(OrderSend|OrderSendAsync|OrderCheck|WebRequest)\s*\(',SOURCE))
        self.assertNotIn('Trade.mqh',SOURCE)
        self.assertNotIn('ajuste_b3.txt',SOURCE)


if __name__=='__main__':unittest.main()
