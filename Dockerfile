FROM python:3.7-slim

WORKDIR /app
RUN pip install -r  /app/requirements.txt

COPY mediator.py /app

CMD ["python", "mediator.py"]