param(
    [string]$Culture = "es-ES"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech

$installed = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
if ($installed.Count -eq 0) {
    Write-Output "__JARVIS_NO_RECOGNIZERS__"
    exit 2
}

$selected = $installed | Where-Object { $_.Culture.Name -eq $Culture } | Select-Object -First 1
if ($null -eq $selected) {
    $selected = $installed | Where-Object { $_.Culture.TwoLetterISOLanguageName -eq "es" } | Select-Object -First 1
}
if ($null -eq $selected) {
    $selected = $installed | Select-Object -First 1
}

$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine($selected.Culture)
try {
    $recognizer.SetInputToDefaultAudioDevice()
} catch {
    Write-Output "__JARVIS_MIC_ERROR__"
    Write-Output $_.Exception.Message
    exit 3
}

$dictation = New-Object System.Speech.Recognition.DictationGrammar
$recognizer.LoadGrammar($dictation)

Write-Output "__JARVIS_READY__$($selected.Culture.Name)"

while ($true) {
    $result = $recognizer.Recognize()
    if ($null -ne $result -and $result.Text) {
        Write-Output $result.Text
    }
}
