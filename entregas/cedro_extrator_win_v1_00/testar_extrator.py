"""Controles com dados sinteticos. Requer PowerShell (PWSH aponta para pwsh).
Nao usa os arquivos licenciados da Cedro nem calcula resultados da estrategia.
"""
import csv
import hashlib
import io
import os
from pathlib import Path
import random
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
PWSH = os.environ.get('PWSH', 'pwsh')


def run(source, output, success=True):
    proc = subprocess.run([PWSH, '-NoProfile', '-File', str(HERE / 'Extrair_WIN.ps1'),
                           '-PastaFonte', str(source), '-PastaSaida', str(output)],
                          capture_output=True, text=True)
    assert (proc.returncode == 0) == success, proc.stdout + proc.stderr
    return proc


with tempfile.TemporaryDirectory(prefix='cedro-controle-') as tmp:
    root = Path(tmp)
    source = root / 'entrada'
    expected = {}
    for month in ('08', '09', '10'):
        day = f'2026{month}03'
        line = f'WINQ26|2026-{month}-03 09:00:57.276|182810|1|107|85|I|5'
        rows = ['TF99|x|1|2|3|4|A|0', line, line,
                line.replace('09:00:57', '09:00:56'),
                line.replace('WINQ26', 'WINV26'), line[:-2]]
        path = source / 'TICK' / 'BMF' / f'2026{month}' / f'{day}.log'
        path.parent.mkdir(parents=True)
        path.write_bytes(('\ufeff' + '\r\n'.join(rows) + '\r\n').encode())
        expected[day] = [f'{n}|{v}' for n, v in enumerate(rows, 1) if v.startswith('WIN')]
        eod = source / 'EOD' / 'BMF' / f'{day}_bmf.log'
        eod.parent.mkdir(parents=True, exist_ok=True)
        eod.write_bytes(b'SYNTHETIC EOD\r\n')
    # Nao incluir BOV nem logs com outro nome, mesmo que contenham WIN.
    bov = source / 'TICK' / 'BOV' / '20260803.log'
    bov.parent.mkdir(parents=True)
    bov.write_text('WIN_FAKE|x\n')
    before = {p: p.read_bytes() for p in source.rglob('*') if p.is_file()}
    output = root / 'saida'
    run(source, output)
    assert (output / 'CONCLUIDO.txt').exists() and not (output / 'INCOMPLETO.txt').exists()
    for day, rows in expected.items():
        files = sorted(output.glob(f'WIN_{day}_parte*.zip'))
        got = []
        for path in files:
            with zipfile.ZipFile(path) as z:
                assert z.testzip() is None
                got.extend(z.read(z.namelist()[0]).decode().splitlines()[1:])
        assert got == rows  # inclui duplicadas e timestamps retrocedentes, sem ordenar
    with zipfile.ZipFile(output / 'GERAL_CEDRO_WIN.zip') as z:
        inventory = list(csv.DictReader(io.StringIO(z.read('CONTRATOS.csv').decode()), delimiter=';'))
        for row in inventory:
            if row['ativo'] == 'WINQ26':
                assert row['registros'] == '4'
                assert row['regressoes_timestamp'] == '1'
                assert row['empates_consecutivos'] == '1'
                assert row['campos_diferentes_de_8'] == '1'
        manifest = list(csv.DictReader(io.StringIO(z.read('ARQUIVOS.csv').decode()), delimiter=';'))
        for row in manifest:
            if row['tipo'] == 'TICK_FONTE':
                original = next(p for p in before if p.name == row['arquivo'] and 'BMF' in p.parts)
                assert row['sha256'] == hashlib.sha256(before[original]).hexdigest()
            elif row['tipo'] == 'WIN_ZIP':
                assert row['sha256'] == hashlib.sha256((output / row['arquivo']).read_bytes()).hexdigest()
        eod_names = [n for n in z.namelist() if n.endswith('_bmf.log')]
        assert len(eod_names) == 3
        assert all(z.read(n) == b'SYNTHETIC EOD\r\n' for n in eod_names)
    assert all(p.read_bytes() == data for p, data in before.items())
    run(source, output, success=False)  # nao sobrescrever
    missing = root / 'incompleto'
    path = missing / 'TICK' / 'BMF'
    path.mkdir(parents=True)
    (path / '20260803.log').write_text('WINQ26|x\n')
    run(missing, root / 'recusado', success=False)
    assert not (root / 'recusado').exists()
    duplicate = source / 'copia' / 'TICK' / 'BMF' / '20260803.log'
    duplicate.parent.mkdir(parents=True)
    duplicate.write_bytes(before[next(p for p in before if p.name == '20260803.log' and 'BMF' in p.parts)])
    run(source, root / 'duplicado', success=False)
    assert not (root / 'duplicado').exists()
    duplicate.unlink()
    # Leitura invalida falha sem certificar conclusao.
    bad = source / 'TICK' / 'BMF' / '202608' / '20260803.log'
    bad.write_bytes(b'WINQ26|\xff\n')
    run(source, root / 'encoding', success=False)
    assert (root / 'encoding' / 'INCOMPLETO.txt').exists()
    assert not (root / 'encoding' / 'CONCLUIDO.txt').exists()
    bad.write_bytes(before[bad])

    # Forcar varias partes com carga pouco compressivel; testar o mesmo motor,
    # com teto pequeno apenas neste controle (produto usa 24 MiB comprimidos).
    rng = random.Random(42)
    big = source / 'TICK' / 'BMF' / '202608' / '20260803.log'
    bigrows = ['WINQ26|2026-08-03 09:00:00.000|' + str(rng.getrandbits(160)) + '|1|2|3|I|5'
               for _ in range(12000)]
    big.write_text('\n'.join(bigrows) + '\n')
    harness = root / 'split.ps1'
    harness.write_text("Add-Type -Path $args[0]\n"
                       "[CedroWin100]::Run([string[]]($args[1],$args[2],$args[3]), [string[]]@(), $args[4], 65536)\n")
    sources = sorted(source.glob('TICK/BMF/*/*.log'))
    splitout = root / 'split'
    proc = subprocess.run([PWSH, '-NoProfile', '-File', str(harness), str(HERE / 'Extrator.cs'),
                           *map(str, sources), str(splitout)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    parts = sorted(splitout.glob('WIN_20260803_*.zip'))
    assert len(parts) > 1
    got = []
    for part in parts:
        with zipfile.ZipFile(part) as z:
            assert z.testzip() is None
            got += z.read(z.namelist()[0]).decode().splitlines()[1:]
    assert got == [f'{n}|{v}' for n, v in enumerate(bigrows, 1)]
    print('PASS: preservacao, duplicadas, empates, ordem, inventario, SHA256, EOD, filtros,')
    print('meses ausentes, destino existente, dia duplicado, UTF8 invalido e divisao em ZIPs.')
