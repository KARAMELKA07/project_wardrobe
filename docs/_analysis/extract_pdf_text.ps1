$ErrorActionPreference = "Stop"

$pdfPath = "C:\Users\zakir\ВКР\1 глава v2.pdf"
$outPath = "C:\Users\zakir\github projects\project_wardrobe\docs\_analysis\chapter1_from_word.txt"

$word = New-Object -ComObject Word.Application
$word.Visible = $false

try {
    $doc = $word.Documents.Open($pdfPath, $false, $true)
    $doc.SaveAs([ref] $outPath, [ref] 2)
    $doc.Close()
}
finally {
    $word.Quit()
}

Write-Output $outPath
