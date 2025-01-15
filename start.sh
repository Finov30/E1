#!/bin/bash

# Générer le fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo "Generating .env file..."
    ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
    echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" > .env
    echo "DATABASE_URL=mysql+pymysql://root:root@mysql_db:3306/fastapi_db" >> .env
    echo "SECOND_DATABASE_URL=mysql+pymysql://root:root@mysql_db:3306/faker_db" >> .env
fi

# Générer le CSV exemple
python generate_sample_csv.py

# Démarrer l'application en arrière-plan
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

# Exécuter les tests
echo "🚀 Lancement des tests des routes..."
python test_routes.py

# Vérifier le résultat des tests
if [ $? -eq 0 ]; then
    echo "✅ Tests réussis - L'application continue de fonctionner"
else
    echo "❌ Tests échoués - Arrêt de l'application"
    pkill -f uvicorn
    exit 1
fi

# Attendre que le processus uvicorn se termine
wait 