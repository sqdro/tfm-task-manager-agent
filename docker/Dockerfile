FROM python:3.12-slim

WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

ENTRYPOINT ["python", "-m", "app.main"]
CMD []