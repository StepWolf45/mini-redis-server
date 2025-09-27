FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/ ./src/

COPY entrypoint.py .

EXPOSE 6379

CMD ["python", "entrypoint.py"]