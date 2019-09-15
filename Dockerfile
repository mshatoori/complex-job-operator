FROM python:3.7
COPY src/python/requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
COPY src/python .
CMD kopf run complexjobsoperator.py
