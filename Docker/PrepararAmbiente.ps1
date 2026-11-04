$ErrorActionPreference = 'Stop'
$PastaProjeto = Split-Path -Parent $PSScriptRoot
$CaminhoDestino = Join-Path $PastaProjeto '.env.docker'

if (Test-Path -LiteralPath $CaminhoDestino) {
    Write-Output '.env.docker ja existe. Nenhuma configuracao foi substituida.'
    exit 0
}

function GerarSegredo {
    $Bytes = New-Object byte[] 48
    $Gerador = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $Gerador.GetBytes($Bytes)
        return [Convert]::ToBase64String($Bytes)
    }
    finally {
        $Gerador.Dispose()
    }
}

$CaminhoExemplo = Join-Path $PastaProjeto '.env.docker.example'
$Conteudo = [System.IO.File]::ReadAllText($CaminhoExemplo)
$Conteudo = $Conteudo.Replace('DJANGO_SECRET_KEY=', ('DJANGO_SECRET_KEY=' + (GerarSegredo)))
$Conteudo = $Conteudo.Replace('POSTGRES_PASSWORD=', ('POSTGRES_PASSWORD=' + (GerarSegredo)))
$Codificacao = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($CaminhoDestino, $Conteudo, $Codificacao)
Write-Output '.env.docker criado com segredos aleatorios. O .env do ambiente atual foi preservado.'
