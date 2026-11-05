$ErrorActionPreference = 'Stop'
try {
    $dadosXP = $PSScriptRoot
    $iniXP = Join-Path $dadosXP 'ModeloD_21101_XP_BRL.ini'
    $expertXP = Join-Path $dadosXP 'MQL5\Experts\ModeloD_Ensaio_Funcional_21101\EA_ModeloD_Ensaio_Funcional.ex5'
    if (!(Test-Path -LiteralPath $iniXP -PathType Leaf)) { throw 'INI ausente. Copie os arquivos do pacote para a pasta de dados da XP.' }
    if (!(Test-Path -LiteralPath $expertXP -PathType Leaf)) { throw 'Compile primeiro EA_ModeloD_Ensaio_Funcional.mq5 no MetaEditor da XP.' }
    $portableXP = $false
    $terminalXP = Join-Path $dadosXP 'terminal64.exe'
    if (Test-Path -LiteralPath $terminalXP -PathType Leaf) { $portableXP = $true }
    else {
        $origemXP = Join-Path $dadosXP 'origin.txt'
        if (!(Test-Path -LiteralPath $origemXP -PathType Leaf)) { throw 'origin.txt ausente. Envie a mensagem exibida para localizar o executavel da XP.' }
        $bytesXP = [IO.File]::ReadAllBytes($origemXP)
        if ($bytesXP.Length -ge 2 -and (($bytesXP[0] -eq 255 -and $bytesXP[1] -eq 254) -or $bytesXP[1] -eq 0)) {
            $textoXP = [Text.Encoding]::Unicode.GetString($bytesXP)
        } else { $textoXP = [Text.Encoding]::UTF8.GetString($bytesXP) }
        $instalacaoXP = $textoXP.Trim([char[]]@([char]0xFEFF,[char]0,[char]32,[char]13,[char]10,[char]34))
        if ([IO.Path]::GetFileName($instalacaoXP) -ieq 'terminal64.exe') { $terminalXP = $instalacaoXP }
        else { $terminalXP = Join-Path $instalacaoXP 'terminal64.exe' }
        if (!(Test-Path -LiteralPath $terminalXP -PathType Leaf)) { throw 'Nao encontrei terminal64.exe pelo origin.txt da XP. Envie esta mensagem.' }
    }
    $rodandoXP = @(Get-Process -Name terminal64 -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path -ieq $terminalXP })
    if ($rodandoXP.Count -gt 0) { throw 'Feche o MT5 da XP e execute este comando novamente. A Genial pode continuar aberta.' }
    Write-Host 'Teste 2.11.01 ALL FILTRADO HISTORICO no WINZ26 nativo da XP, de 30/10/2026, deposito simulado em BRL.'
    Write-Host 'Nenhum simbolo customizado ou importacao de ticks sera utilizado.'
    Write-Host ('Executavel identificado: ' + $terminalXP)
    [void](Read-Host 'Pressione Enter para iniciar o Testador da XP')
    $argumentosXP = @()
    if ($portableXP) { $argumentosXP += '/portable' }
    $argumentosXP += ('/config:"{0}"' -f $iniXP)
    Start-Process -FilePath $terminalXP -ArgumentList $argumentosXP
} catch {
    Write-Host ('ERRO: ' + $_.Exception.Message)
    [void](Read-Host 'Envie a mensagem acima. Pressione Enter para fechar')
    exit 1
}
