param([string]$PastaFonte = '', [string]$PastaSaida = '')
$ErrorActionPreference = 'Stop'
try {
    if (-not $PastaFonte) {
        Add-Type -AssemblyName System.Windows.Forms
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = 'Selecione a pasta comum dos TRES meses descompactados (contendo TICK e EOD).'
        if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit 2 }
        $PastaFonte = $dialog.SelectedPath
        $dialog.Dispose()
    }
    $PastaFonte = (Resolve-Path -LiteralPath $PastaFonte).Path
    $arquivos = @(Get-ChildItem -LiteralPath $PastaFonte -Recurse -File -Filter '*.log')
    [string[]]$ticks = @($arquivos | Where-Object {
        $_.Name -match '^2026(08|09|10)\d{2}\.log$' -and $_.FullName -match '[\\/]TICK[\\/]BMF[\\/]'
    } | ForEach-Object { $_.FullName })
    [string[]]$eods = @($arquivos | Where-Object {
        $_.Name -match '^2026(08|09|10)\d{2}_bmf\.log$' -and $_.FullName -match '[\\/]EOD[\\/]'
    } | ForEach-Object { $_.FullName })
    if (-not $PastaSaida) {
        $desktop = [Environment]::GetFolderPath('Desktop')
        $PastaSaida = Join-Path $desktop ('CEDRO_WIN_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + $PID)
    }
    Add-Type -AssemblyName System.IO.Compression
    # .NET Framework do Windows PowerShell 5.1 usa referencia explicita; PS7 resolve pelo runtime.
    $fonte = Join-Path $PSScriptRoot 'Extrator.cs'
    if ($PSVersionTable.PSVersion.Major -le 5) {
        Add-Type -Path $fonte -ReferencedAssemblies 'System.IO.Compression.dll','System.dll','System.Core.dll'
    } else { Add-Type -Path $fonte }
    [CedroWin100]::Run($ticks, $eods, $PastaSaida, (24L * 1024 * 1024))
    Write-Host ''
    Write-Host 'Envie primeiro GERAL_CEDRO_WIN.zip. Os ZIPs WIN_... contem os dados diarios.' -ForegroundColor Green
    if ($env:OS -eq 'Windows_NT') { Start-Process explorer.exe -ArgumentList ('"' + $PastaSaida + '"') }
} catch {
    Write-Host ('ERRO: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'Os arquivos originais nao foram alterados. Envie uma foto desta mensagem.'
    exit 1
}
