$ErrorActionPreference = 'Stop'
$baseDir = Join-Path $env:APPDATA 'MetaQuotes\Terminal\Common\Files\ModeloD_Fechamento_Agosto'
$batchDir = Get-ChildItem -LiteralPath $baseDir -Directory | Where-Object { $_.Name -match '^MES111_\d+_\d+$' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $batchDir) { throw 'Nenhuma pasta MES111 encontrada. Rode Coletar_Agosto_Sem_Ordens no terminal principal da Genial.' }
$logPath = Join-Path $batchDir.FullName 'RESULTADO.txt'
if (-not (Test-Path -LiteralPath $logPath)) { throw 'Pasta sem RESULTADO.txt. Envie a mensagem da aba Experts.' }
if (-not (Select-String -LiteralPath $logPath -Pattern '^END;' -Quiet)) { throw 'Aguarde MES111;END antes de compactar. Se interrompeu, envie a pasta inteira manualmente.' }
$outputDir = Join-Path $baseDir ($batchDir.Name + '_ZIP')
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$allFiles = @(Get-ChildItem -LiteralPath $batchDir.FullName -File)
$totalBytes = ($allFiles | Measure-Object Length -Sum).Sum
if ($totalBytes -lt 25MB) {
    Compress-Archive -LiteralPath @($allFiles.FullName) -DestinationPath (Join-Path $outputDir ($batchDir.Name + '.zip')) -Force
} else {
    $datedPattern = '^(EVENTOS|MINUTOS)_\d{8}\.csv$|^M1_CONTRATO_\d{8}_(WINQ26|WINV26)\.csv$'
    $shared = @($allFiles | Where-Object { $_.Name -notmatch $datedPattern })
    Compress-Archive -LiteralPath @($shared.FullName) -DestinationPath (Join-Path $outputDir ($batchDir.Name + '_GERAL.zip')) -Force
    $dates = @($allFiles | Where-Object { $_.Name -match $datedPattern } | ForEach-Object { [regex]::Match($_.Name,'\d{8}').Value } | Sort-Object -Unique)
    foreach ($date in $dates) {
        $filesForDate = @($allFiles | Where-Object { $_.Name -match $datedPattern -and $_.Name.Contains($date) })
        Compress-Archive -LiteralPath @($filesForDate.FullName) -DestinationPath (Join-Path $outputDir ($batchDir.Name + '_' + $date + '.zip')) -Force
    }
}
Write-Host ('ZIP(s) criados em: ' + $outputDir)
Write-Host 'Envie TODOS os ZIPs desta execucao, inclusive GERAL se houver, e o log Experts do START ao END.'
Start-Process explorer.exe -ArgumentList ('"' + $outputDir + '"')
