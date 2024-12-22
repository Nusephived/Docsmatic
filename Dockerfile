FROM python:alpine

WORKDIR /docsmatic

COPY main.py main.py
COPY adminbox.py adminbox.py

RUN pip install requests
RUN pip install beautifulsoup4

ENTRYPOINT ["python", "main.py"]