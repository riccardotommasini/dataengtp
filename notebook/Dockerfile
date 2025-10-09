FROM quay.io/jupyter/datascience-notebook

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

WORKDIR /home/jovyan/work

ENTRYPOINT ["jupyter","notebook","--NotebookApp.token=''"]
