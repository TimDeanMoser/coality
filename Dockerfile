FROM ubuntu:20.04
WORKDIR /coality
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true
COPY projects ./projects
COPY quality_assessment ./quality_assessment
COPY app.py .
COPY requirements.txt .
COPY setup.sh .
RUN apt-get update && apt-get install -y \
dos2unix \
wget \
python3 \
python3-pip \
git \
libxml2 \
libcurl4 \
libarchive13
RUN find . -type f -print0 | xargs -0 dos2unix
RUN ./setup.sh
ENV PYTHONPATH="${PYTHONPATH}:/$PROJECT_PATH"
CMD ["python3", "app.py"]
#docker build -t coality:latest .
#docker run -d -p 5000:5000 --name=coality-container coality python3 app.py
#docker exec -it coality-container sh