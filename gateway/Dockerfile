FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN  apt-get update && apt-get install -y build-essential python3-dev

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install email_validator

COPY . .

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
