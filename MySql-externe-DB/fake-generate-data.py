import os
import time
import random
import string
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from faker import Faker
from models.user import users, user_ids
from config.database import meta

DATABASE_URL = "mysql+pymysql://root:rootpassword@db:3609/fake-data"

def get_engine(max_retries=5, retry_interval=5):
    for attempt in range(max_retries):
        try:
            engine = create_engine(DATABASE_URL, echo=True)  # `echo=True` pour plus de logs
            # Tester la connexion
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))  # Utilisation correcte de `text`
            print("Connexion à la base de données établie avec succès.")
            return engine
        except OperationalError as e:
            print(f"Tentative {attempt + 1} échouée: {e}")
            if attempt < max_retries - 1:
                print(f"Nouvelle tentative dans {retry_interval} secondes...")
                time.sleep(retry_interval)
            else:
                print("Impossible de se connecter à la base de données après plusieurs tentatives.")
                raise

# Créer l'engine
engine = get_engine()

# Créer les tables si elles n'existent pas
meta.create_all(engine)

# Initialiser Faker
fake = Faker()

def generate_external_id():
    """Génère un identifiant externe aléatoire."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def insert_fake_data(num_users=100):
    """Insère des données fictives dans la base de données."""
    with engine.connect() as connection:
        for _ in range(num_users):
            # Insérer un utilisateur
            user = {
                'name': fake.name(),
                'email': fake.email(),
                'password': fake.password()
            }
            result = connection.execute(users.insert().values(**user))
            user_id = result.inserted_primary_key[0]

            # Insérer un identifiant externe pour cet utilisateur
            external_id = {
                'user_id': user_id,
                'external_id': generate_external_id()
            }
            connection.execute(user_ids.insert().values(**external_id))

    print(f"{num_users} utilisateurs et identifiants externes ont été insérés.")

if __name__ == "__main__":
    insert_fake_data()
