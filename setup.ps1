 # Coality configuration for Windows
$MODELS = "models/"
$OUTPUTS = "outputs/"
$SRC_ML_URL = "http://131.123.42.38/lmcrs/v1.0.0/srcml_1.0.0-1_win.exe"
$SRC_ML = "./" + $SRC_ML_URL.split("/")[-1]
[string]$PROJECT_PATH = Get-Location
# Necessary changes to directory and Path
mkdir $MODELS
mkdir $OUTPUTS
New-Item -Path $OUTPUTS -Name "example_output.json" -ItemType file
# Temporarily add to PATH for training purposes (permanently adding this via script is difficult and intrusive)
$env:PYTHONPATH += $env:PYTHONPATH+";"+$PROJECT_PATH
# Installations
pip install -r requirements.txt
python -m nltk.downloader stopwords
python -m nltk.downloader punkt
wget $SRC_ML_URL -OutFile $SRC_ML
& $SRC_ML
# Train models
python classification/src/trainer.py classification/data/data_sets_pooja_pascarella/no_pp.txt models/
# Example notes
"Please be sure to add the project to PYTHONPATH in the System Variables"

"Example command of how to generate output for a given project:"
"python .\quality_assessment\src\main.py C:\Full\Path\To\Example_Project .\outputs\example_output.json .\models\ -log debug"
Pause