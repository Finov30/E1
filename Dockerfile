# Image de base
FROM python:3.10-slim

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    dbus-x11 \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Définition des variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHROME_BIN=/usr/bin/chromium \
    CHROME_DRIVER=/usr/bin/chromedriver

# Création et définition du répertoire de travail
WORKDIR /app

# Copie des requirements avant le reste du code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code
COPY . .

# Convertir les fins de ligne et rendre le script exécutable
RUN dos2unix start.sh && \
    chmod +x start.sh

# Création d'un utilisateur non-root pour la sécurité
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chmod 777 /app  # Permet à l'utilisateur d'écrire le fichier .env

USER appuser

# Exposition du port
EXPOSE 8000

# Commande de démarrage
CMD ["./start.sh"]