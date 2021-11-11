# Coality configuration for Mac/Linux
MODELS="models/"
OUTPUTS="outputs/"
OUTPUT_FILE="outputs/example_output.json"
SRC_ML="http://131.123.42.38/lmcrs/v1.0.0/srcml_1.0.0-1_ubuntu20.04.deb"
PROJECT_PATH=$(pwd)
mkdir $MODELS
mkdir $OUTPUTS
touch $OUTPUT_FILE
echo "Created the following:"
realpath -e $MODELS && realpath -e $OUTPUTS && realpath -e $OUTPUT_FILE

# Next add project to path, takes first argument
export PYTHONPATH="${PYTHONPATH}:/$PROJECT_PATH"

# Necessary installations
pip install -r requirements.txt
python3 -m nltk.downloader stopwords
python3 -m nltk.downloader punkt
wget $SRC_ML
sudo dpkg -i srcml_1.0.0-1_ubuntu20.04.deb

# Make adjustment to comment_rater.py
# sed -i 's/quality_assessment\\data\\abbreviations\.csv/quality_assessment\/data\/abbreviations\.csv/g' quality_assessment/src/comment_rater.py

# Train models
python3 classification/src/trainer.py classification/data/data_sets_pooja_pascarella/no_pp.txt models/
