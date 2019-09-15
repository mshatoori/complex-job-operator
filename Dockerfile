FROM python:3.7
RUN pip install kopf
COPY src/python /src
CMD kopf run /src/complexjobsoperator.py
