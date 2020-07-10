FROM python:3.7-slim

WORKDIR /app
RUN pip install pika dotenv

COPY mediator.py /app

CMD ["python", "mediator.py"]