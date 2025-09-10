FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

COPY ./src ./src
WORKDIR /app/src

EXPOSE 80

CMD ["python", "main.py"]