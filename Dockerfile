FROM python:3.14.0rc2
COPY src/python/requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
COPY src/python .
CMD kopf run complexjobsoperator.py
