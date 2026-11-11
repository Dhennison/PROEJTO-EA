$ErrorActionPreference = 'Stop'
$baseDir = Join-Path $env:APPDATA 'MetaQuotes\Terminal\Common\Files\ModeloD_Fechamento_Setembro'
$batchDir = Get-ChildItem -LiteralPath $baseDir -Directory | Where-Object { $_.Name -like 'MES100_*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $batchDir) { throw 'Nenhuma pasta MES100 encontrada.' }
$logPath = Join-Path $batchDir.FullName 'RESULTADO.txt'
if (-not (Test-Path -LiteralPath $logPath)) { throw 'A pasta mais recente nao tem RESULTADO.txt. Envie a mensagem da aba Experts.' }
if (-not (Select-String -LiteralPath $logPath -SimpleMatch 'END;' -Quiet)) { throw 'Coleta ainda nao terminou. Aguarde MES100;END antes de compactar.' }
$outputDir = Join-Path $baseDir ($batchDir.Name + '_ZIP')
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$allFiles = @(Get-ChildItem -LiteralPath $batchDir.FullName -File)
$totalBytes = ($allFiles | Measure-Object Length -Sum).Sum
if ($totalBytes -lt 25MB) {
    Compress-Archive -LiteralPath @($allFiles.FullName) -DestinationPath (Join-Path $outputDir ($batchDir.Name + '.zip')) -Force
} else {
    $shared = @($allFiles | Where-Object { $_.Name -notmatch '^(EVENTOS|MINUTOS)_\d{8}\.csv$' })
    $dates = @($allFiles | Where-Object { $_.Name -match '^EVENTOS_(\d{8})\.csv$' } | ForEach-Object { [regex]::Match($_.Name,'\d{8}').Value } | Sort-Object -Unique)
    foreach ($date in $dates) {
        $parts = @($shared.FullName) + @((Join-Path $batchDir.FullName ('EVENTOS_' + $date + '.csv')), (Join-Path $batchDir.FullName ('MINUTOS_' + $date + '.csv')))
        Compress-Archive -LiteralPath $parts -DestinationPath (Join-Path $outputDir ($batchDir.Name + '_' + $date + '.zip')) -Force
    }
}
Write-Host ('ZIP(s) criados em: ' + $outputDir)
Start-Process explorer.exe -ArgumentList ('"' + $outputDir + '"')
