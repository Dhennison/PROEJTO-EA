# Preparacao local no Windows do usuario. Nao modifica a instalacao original.
# Sem download de executaveis, copia de credenciais ou desativacao de verificacao.
$ErrorActionPreference = 'Stop'

# Identifica o programa aberto; nao le memoria, conta, senha ou arquivos de login.
$mdProgramPaths = @(Get-Process -Name terminal64 -ErrorAction SilentlyContinue |
    ForEach-Object { $_.Path } | Where-Object { $_ } | Select-Object -Unique)
if ($mdProgramPaths.Count -ne 1) {
    throw 'Deixe aberta somente a instalacao MT5 usada no teste. Nao foi identificado um unico executavel de origem.'
}
$mdSourceProgram = $mdProgramPaths[0]
$mdSourceFolder = [System.IO.Path]::GetDirectoryName($mdSourceProgram)
$mdBinaryNames = @('terminal64.exe', 'metaeditor64.exe', 'metatester64.exe')
$mdVerifiedBinaries = @()
foreach ($mdName in $mdBinaryNames) {
    $mdSourcePath = Join-Path $mdSourceFolder $mdName
    if (-not (Test-Path -LiteralPath $mdSourcePath -PathType Leaf)) {
        throw "Arquivo esperado nao encontrado: $mdSourcePath. Nenhuma instalacao foi alterada."
    }
    $mdSignature = Get-AuthenticodeSignature -LiteralPath $mdSourcePath
    if ($mdSignature.Status -ne 'Valid') {
        throw "Assinatura de $mdName nao validada ($($mdSignature.Status)). Nao prosseguir desativando verificacao."
    }
    $mdVerifiedBinaries += [pscustomobject]@{
        Name = $mdName
        Source = $mdSourcePath
        SHA256 = (Get-FileHash -LiteralPath $mdSourcePath -Algorithm SHA256).Hash
        Version = (Get-Item -LiteralPath $mdSourcePath).VersionInfo.FileVersion
    }
}

# Localiza apenas o diagnostico que o usuario ja compilou. Nunca copia perfil,
# bases, config, contas, licencas, graficos ou arquivos do EA operacional.
$mdRelativeDiagnostic = 'MQL5\Experts\ModeloD_Diagnostico_Agente\Diagnostico_Dados_WINZ26.ex5'
$mdTerminalRoot = Join-Path $env:APPDATA 'MetaQuotes\Terminal'
$mdCandidates = @()
if (Test-Path -LiteralPath $mdTerminalRoot -PathType Container) {
    foreach ($mdDataDirectory in (Get-ChildItem -LiteralPath $mdTerminalRoot -Directory)) {
        $mdCompiledPath = Join-Path $mdDataDirectory.FullName $mdRelativeDiagnostic
        if (Test-Path -LiteralPath $mdCompiledPath -PathType Leaf) {
            $mdOrigin = Join-Path $mdDataDirectory.FullName 'origin.txt'
            $mdMatchesProgram = $false
            if (Test-Path -LiteralPath $mdOrigin -PathType Leaf) {
                # origin.txt contem somente o diretorio de instalacao do terminal.
                $mdOriginFolder = (Get-Content -LiteralPath $mdOrigin -Raw).Trim().TrimEnd('\')
                $mdMatchesProgram = $mdOriginFolder -ieq $mdSourceFolder.TrimEnd('\')
            }
            $mdCandidates += [pscustomobject]@{
                Path = $mdCompiledPath
                MatchesProgram = $mdMatchesProgram
            }
        }
    }
}
$mdMatchingCandidates = @($mdCandidates | Where-Object { $_.MatchesProgram })
if ($mdMatchingCandidates.Count -eq 1) {
    $mdDiagnosticSource = $mdMatchingCandidates[0].Path
} elseif ($mdMatchingCandidates.Count -gt 1 -or $mdCandidates.Count -ne 1) {
    throw 'Nao foi possivel identificar sem ambiguidade o diagnostico compilado. Nenhuma pasta foi criada. Envie esta mensagem.'
} else {
    $mdDiagnosticSource = $mdCandidates[0].Path
}

$mdUniqueName = 'ModeloD_MT5_Isolado_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' +
    ([guid]::NewGuid().ToString('N').Substring(0, 8))
$mdNewFolder = Join-Path $env:LOCALAPPDATA $mdUniqueName
if (Test-Path -LiteralPath $mdNewFolder) {
    throw 'Destino ja existe. Nenhum arquivo sera sobrescrito.'
}
New-Item -ItemType Directory -Path $mdNewFolder | Out-Null
foreach ($mdBinary in $mdVerifiedBinaries) {
    $mdTarget = Join-Path $mdNewFolder $mdBinary.Name
    Copy-Item -LiteralPath $mdBinary.Source -Destination $mdTarget
    if ((Get-FileHash -LiteralPath $mdTarget -Algorithm SHA256).Hash -ne $mdBinary.SHA256) {
        throw "Hash divergente na copia de $($mdBinary.Name). Pasta nova preservada; nao iniciar."
    }
}
$mdDiagnosticDestination = Join-Path $mdNewFolder $mdRelativeDiagnostic
New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($mdDiagnosticDestination)) | Out-Null
$mdDiagnosticHash = (Get-FileHash -LiteralPath $mdDiagnosticSource -Algorithm SHA256).Hash
Copy-Item -LiteralPath $mdDiagnosticSource -Destination $mdDiagnosticDestination
if ((Get-FileHash -LiteralPath $mdDiagnosticDestination -Algorithm SHA256).Hash -ne $mdDiagnosticHash) {
    throw 'Hash divergente na copia do diagnostico. Nao iniciar.'
}
$mdManifest = [pscustomobject]@{
    Purpose = 'Copia isolada para diagnostico WINZ26, nao instalacao operacional'
    Created = (Get-Date -Format 'o')
    SourceProgram = $mdSourceProgram
    Destination = $mdNewFolder
    Binaries = $mdVerifiedBinaries
    DiagnosticSHA256 = $mdDiagnosticHash
    LaunchArgument = '/portable'
}
$mdManifest | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $mdNewFolder 'MODELOD_PREPARACAO.json') -Encoding UTF8
@'
Abrir terminal64.exe DESTA PASTA com o argumento /portable.
No MT5 novo, Arquivo > Abrir Pasta de Dados deve abrir ESTA PASTA.
Conectar manualmente a conta Genial existente no servidor original; nao abrir
conta nova nem enviar credenciais em chat. Negociacao nao e necessaria.
Testar somente ModeloD_Diagnostico_Agente/Diagnostico_Dados_WINZ26:
WINZ26, M5, 30/10/2026 a 31/10/2026, ticks reais, sem otimizacao e sem visual.
Usar agente local e mesma configuracao de conta/saldo. Encerra as 09:02.
Common/Files pode ser compartilhado com o MT5 original; preservar os TXT.
Nao copiar perfil, bases ou configuracoes antigas para esta pasta.
'@ | Set-Content -LiteralPath (Join-Path $mdNewFolder 'LEIA_ANTES_DO_TESTE.txt') -Encoding UTF8
# Atalho explicito evita perder /portable ao abrir novamente a copia.
$mdShell = New-Object -ComObject WScript.Shell
$mdShortcut = $mdShell.CreateShortcut((Join-Path $mdNewFolder 'ABRIR_MT5_ISOLADO.lnk'))
$mdShortcut.TargetPath = Join-Path $mdNewFolder 'terminal64.exe'
$mdShortcut.Arguments = '/portable'
$mdShortcut.WorkingDirectory = $mdNewFolder
$mdShortcut.Save()
Write-Host "Copia preparada em: $mdNewFolder"
Write-Host 'Hashes conferidos. Originais preservados. Abrindo copia em modo portable.'
Start-Process -FilePath (Join-Path $mdNewFolder 'terminal64.exe') -ArgumentList '/portable' -WorkingDirectory $mdNewFolder
