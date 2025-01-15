# Image de base
FROM python:3.10-slim

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    xvfb \
    dbus-x11 \
    dos2unix \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Ajout du repository Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# Installation de Chrome
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Installation de ChromeDriver
RUN wget -q "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /usr/bin/ \
    && chmod +x /usr/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# Définition des variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHROME_BIN=/usr/bin/google-chrome \
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