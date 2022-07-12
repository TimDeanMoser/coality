# Coality configuration for Linux
SRC_ML="http://131.123.42.38/lmcrs/v1.0.0/srcml_1.0.0-1_ubuntu20.04.deb"
PROJECT_PATH=$(pwd)

# Next add project to path, takes first argument
export PYTHONPATH="${PYTHONPATH}:/$PROJECT_PATH"

# Necessary installations
pip install -r requirements.txt
python3 -m nltk.downloader punkt
wget $SRC_ML
dpkg -i srcml_1.0.0-1_ubuntu20.04.deb

# Make adjustment to comment_rater.py
# sed -i 's/quality_assessment\\data\\abbreviations\.csv/quality_assessment\/data\/abbreviations\.csv/g' quality_assessment/src/comment_rater.py
