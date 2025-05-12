FROM python:3.10

# Alap csomagok telepítése
RUN apt-get update && apt-get install -y sudo iproute2

# Munkakönyvtár beállítása
WORKDIR /app

# Függőségek telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Másoljuk a szükséges fájlokat
COPY . .

# Alkalmazás indítása
CMD ["python3", "dashboard.py"]
