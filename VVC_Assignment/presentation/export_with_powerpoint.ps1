# Export the deck to PDF and to one PNG per slide using the installed Microsoft PowerPoint (COM), i.e. the same
# renderer the audience will use. Opens the file read-only; does not modify the .pptx.
param([string]$Deck = "$PSScriptRoot\VVC_Experimental_Evaluation_Prof_Kiho.pptx",
      [string]$PngDir = "$PSScriptRoot\render")
$pdf = [IO.Path]::ChangeExtension($Deck, '.pdf')
New-Item -ItemType Directory -Force $PngDir | Out-Null
$pp = New-Object -ComObject PowerPoint.Application
try {
    $pres = $pp.Presentations.Open($Deck, -1, 0, 0)   # ReadOnly, Untitled = false, WithWindow = false
    $pres.SaveAs($pdf, 32)                             # 32 = ppSaveAsPDF
    foreach ($s in $pres.Slides) { $s.Export((Join-Path $PngDir ("slide-{0:D2}.png" -f $s.SlideIndex)), 'PNG', 1920, 1080) }
    "slides: $($pres.Slides.Count)"
    $pres.Close()
} finally { $pp.Quit() }
"pdf: $pdf ($((Get-Item $pdf).Length) bytes)"
Get-ChildItem $PngDir -Filter *.png | ForEach-Object { $_.FullName }
