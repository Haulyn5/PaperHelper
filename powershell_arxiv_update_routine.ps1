conda activate paper_helper
Set-Location D:\Projects\PaperHelper  # Change this to the path of Paper helper.
python ./arxiv_fetcher.py --num 50
python ./compute_feature.py

Write-Host -NoNewLine 'Press any key to continue...';
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown');