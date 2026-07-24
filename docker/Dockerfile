FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git patch && rm -rf /var/lib/apt/lists/*

CMD ["pytest"]
