FROM python:3.10

# Alap csomagok telepítése
RUN apt-get update && apt-get install -y sudo iproute2

# Másoljuk a szükséges fájlokat
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install debugpy

CMD ["python3", "./app/dashboard.py"]
