FROM python:alpine

WORKDIR /docsmatic

COPY main.py /main.py
COPY adminbox.py /adminbox.py

ENTRYPOINT ["python", "main.py"]