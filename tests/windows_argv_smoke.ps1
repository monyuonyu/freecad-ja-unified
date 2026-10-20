# Windows の FreeCADCmd に日本語のパスを渡す試験（release.yml・windows-argv-smoke.yml から使う）
#   pwsh tests/windows_argv_smoke.ps1 -FreeCADCmd <...\bin\freecadcmd.exe>
# 0.5.6 までは、'--' の後ろに日本語のパスを渡すとスクリプトが走る前に
# "Unknown exception while processing file" で止まっていた（引数を ANSI コードページのまま UTF-8 として読んでいた）。
# PowerShell から・cmd から・スクリプト自体が日本語のフォルダ・.jww を直接開く・-c の日本語、を確かめる。
# 'é' は英語版 Windows（CP1252）でも UTF-8 として読めないバイトになるので、CI でも元の不具合が再現する。
param([Parameter(Mandatory = $true)][string]$FreeCADCmd)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$base = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() }
$dir = Join-Path $base 'テスト_é 日本語のフォルダ'
if (Test-Path -LiteralPath $dir) { Remove-Item -LiteralPath $dir -Recurse -Force }
New-Item -ItemType Directory -Path $dir | Out-Null
$jww = Join-Path $dir '天板.jww'
Copy-Item -LiteralPath (Join-Path $here 'data\basic.jww') -Destination $jww
$script = Join-Path $base 'argv_check.py'
Copy-Item -LiteralPath (Join-Path $here 'argv_check.py') -Destination $script
$scriptJa = Join-Path $dir '確認.py'
Copy-Item -LiteralPath (Join-Path $here 'argv_check.py') -Destination $scriptJa
# 設定は使い捨ての場所に
$env:APPDATA = Join-Path $base 'fc-appdata'
$env:LOCALAPPDATA = Join-Path $base 'fc-localappdata'
$env:PYTHONIOENCODING = 'utf-8'

$failed = 0
function Check-Result([string]$name, [string]$output, [int]$code, [string]$script, [string]$json) {
    $ok = $true
    $why = ''
    if ($code -ne 0) { $ok = $false; $why += "exit code $code; " }
    if (-not (Test-Path -LiteralPath $json)) {
        $ok = $false; $why += 'no result file; '
    }
    else {
        $res = Get-Content -LiteralPath $json -Raw -Encoding utf8 | ConvertFrom-Json
        $want = @($script, $jww, $json)
        $got = @($res.argv)
        if ($got.Count -ne 3) { $ok = $false; $why += "argv has $($got.Count) items; " }
        for ($i = 0; $i -lt [Math]::Min(3, $got.Count); $i++) {
            # 区切りは / でも \ でもよい（スクリプトのパスは FreeCAD が / に直す）
            if (($got[$i] -replace '/', '\') -ne $want[$i]) { $ok = $false; $why += "argv[$i]=$($got[$i]) want $($want[$i]); " }
        }
        if (-not $res.exists) { $ok = $false; $why += 'os.path.isfile(argv[1]) is False; ' }
        if ($res.objects -le 0) { $ok = $false; $why += "the .jww gave $($res.objects) objects; " }
    }
    if ($ok) { Write-Host "  OK  $name" }
    else {
        Write-Host "  NG  $name ($why)"
        Write-Host "------ output ------"
        Write-Host $output
        Write-Host "--------------------"
        $script:failed++
    }
}

Write-Host "== $FreeCADCmd"

# 1. PowerShell から: & freecadcmd.exe script.py -- '...日本語...\天板.jww' result.json
$json = Join-Path $dir '結果1.json'
$out = & $FreeCADCmd $script -- $jww $json 2>&1 | Out-String
Check-Result 'PowerShell: script.py -- <日本語のパス>' $out $LASTEXITCODE $script $json

# 2. cmd から（パスは環境変数で渡す: バッチファイル自体の文字コードに左右されないように）
$json = Join-Path $dir '結果2.json'
$bat = Join-Path $base 'argv_check.cmd'
Set-Content -LiteralPath $bat -Encoding ascii -Value '@"%FC_CMD%" "%FC_SCRIPT%" -- "%FC_JWW%" "%FC_JSON%"'
$env:FC_CMD = $FreeCADCmd; $env:FC_SCRIPT = $script; $env:FC_JWW = $jww; $env:FC_JSON = $json
$out = & cmd.exe /d /c $bat 2>&1 | Out-String
Check-Result 'cmd: script.py -- <日本語のパス>' $out $LASTEXITCODE $script $json

# 3. スクリプト自体が日本語のフォルダにある
$json = Join-Path $dir '結果3.json'
$out = & $FreeCADCmd $scriptJa -- $jww $json 2>&1 | Out-String
Check-Result 'PowerShell: <日本語のフォルダ>\確認.py -- <日本語のパス>' $out $LASTEXITCODE $scriptJa $json

# 4. 日本語のパスの .jww をそのまま開く
$out = & $FreeCADCmd $jww 2>&1 | Out-String
$code = $LASTEXITCODE
if ($code -eq 0 -and $out -match 'Conversion successful' -and $out -notmatch 'xception') { Write-Host '  OK  PowerShell: freecadcmd <日本語のパス>.jww' }
else { Write-Host "  NG  PowerShell: freecadcmd <日本語のパス>.jww (exit code $code)"; Write-Host $out; $failed++ }

# 5. -c のコードに日本語
$txt = Join-Path $dir 'c.txt'
$out = & $FreeCADCmd -c "open(r'$txt', 'w', encoding='utf-8').write('天板')" 2>&1 | Out-String
$code = $LASTEXITCODE
$got = if (Test-Path -LiteralPath $txt) { Get-Content -LiteralPath $txt -Raw -Encoding utf8 } else { '<none>' }
if ($code -eq 0 -and $got -eq '天板') { Write-Host '  OK  PowerShell: freecadcmd -c "<日本語>"' }
else { Write-Host "  NG  PowerShell: freecadcmd -c `"<日本語>`" (exit code $code, wrote $got)"; Write-Host $out; $failed++ }

if ($failed -gt 0) { Write-Host "== $failed failed"; exit 1 }
Write-Host '== all passed'
exit 0
