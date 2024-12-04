from fastapi import APIRouter, File, UploadFile, HTTPException
from config.database import conn
from models.index import users, user_ids
from schemas.index import User
from sqlalchemy import select
from cryptography.fernet import Fernet
import csv
import io
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv

load_dotenv()  # Chargement des variables d'environnement

user = APIRouter()

# Gestion sécurisée de la clé de chiffrement
key = os.getenv('ENCRYPTION_KEY')
if key is None:
    raise ValueError("ENCRYPTION_KEY non trouvée dans le fichier .env. Veuillez la définir.")

cipher_suite = Fernet(key.encode())

def encrypt_data(data: str) -> str:
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    return cipher_suite.decrypt(data.encode()).decode()

@user.get("/")
async def read_data():
    query = select(users, user_ids.c.external_id).select_from(
        users.join(user_ids, users.c.id == user_ids.c.user_id)
    )
    result = conn.execute(query).fetchall()
    decrypted_result = [
        {**row._asdict(), 'email': decrypt_data(row.email), 'password': decrypt_data(row.password)}
        for row in result
    ]
    return decrypted_result

@user.get("/{id}")
async def read_data(id: int):
    query = select(users, user_ids.c.external_id).select_from(
        users.join(user_ids, users.c.id == user_ids.c.user_id)
    ).where(users.c.id == id)
    result = conn.execute(query).fetchall()
    decrypted_result = [
        {**row._asdict(), 'email': decrypt_data(row.email), 'password': decrypt_data(row.password)}
        for row in result
    ]
    return decrypted_result

@user.post("/")
async def write_data(user: User):
    encrypted_password = encrypt_data(user.password)
    encrypted_email = encrypt_data(user.email)
    result = conn.execute(users.insert().values(
        name=user.name,
        email=encrypted_email,
        password=encrypted_password
    ))
    user_id = result.inserted_primary_key[0]
    
    conn.execute(user_ids.insert().values(
        user_id=user_id,
        external_id=f"EXT-{user_id}"
    ))
    
    query = select(users, user_ids.c.external_id).select_from(
        users.join(user_ids, users.c.id == user_ids.c.user_id)
    )
    result = conn.execute(query).fetchall()
    return [row._asdict() for row in result]

@user.put("/{id}")
async def update_data(id: int, user: User):
    encrypted_password = encrypt_data(user.password)
    encrypted_email = encrypt_data(user.email)
    conn.execute(users.update().values(
        name=user.name,
        email=encrypted_email,
        password=encrypted_password
    ).where(users.c.id == id))
    
    query = select(users, user_ids.c.external_id).select_from(
        users.join(user_ids, users.c.id == user_ids.c.user_id)
    )
    result = conn.execute(query).fetchall()
    return [row._asdict() for row in result]

@user.delete("/{id}")
async def delete_data(id: int):
    conn.execute(user_ids.delete().where(user_ids.c.user_id == id))
    conn.execute(users.delete().where(users.c.id == id))
    
    query = select(users, user_ids.c.external_id).select_from(
        users.join(user_ids, users.c.id == user_ids.c.user_id)
    )
    result = conn.execute(query).fetchall()
    return [row._asdict() for row in result]

@user.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    contents = await file.read()
    csv_data = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.DictReader(csv_data)

    for row in csv_reader:
        encrypted_password = encrypt_data(row['password'])
        encrypted_email = encrypt_data(row['email'])
        result = conn.execute(users.insert().values(
            name=row['name'],
            email=encrypted_email,
            password=encrypted_password
        ))
        user_id = result.inserted_primary_key[0]
        
        conn.execute(user_ids.insert().values(
            user_id=user_id,
            external_id=row.get('external_id', f"EXT-{user_id}")
        ))

    query = select(users, user_ids.c.external_id).select_from(
        users.join(user_ids, users.c.id == user_ids.c.user_id)
    )
    result = conn.execute(query).fetchall()
    return [row._asdict() for row in result]

@user.post("/scrape")
async def extraire_donnees_tableau():
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)

    try:
        url = "https://webscraper.io/test-sites/tables"
        driver.get(url)

        wait = WebDriverWait(driver, 10)
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-bordered")))
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]
        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            prenom = cells[1].text
            nom = cells[2].text
            username = cells[3].text
            data.append({"prenom": prenom, "nom": nom, "username": username})

        for personne in data:
            encrypted_email = encrypt_data(personne['username'])
            encrypted_password = encrypt_data(personne['prenom'] + personne['nom'])
            result = conn.execute(users.insert().values(
                name=personne['prenom'],
                email=encrypted_email,
                password=encrypted_password
            ))
            user_id = result.inserted_primary_key[0]
            
            conn.execute(user_ids.insert().values(
                user_id=user_id,
                external_id=f"EXT-{user_id}"
            ))

    finally:
        driver.quit()

    query = select(users, user_ids.c.external_id).select_from(
        users.join(user_ids, users.c.id == user_ids.c.user_id)
    )
    result = conn.execute(query).fetchall()
    return [row._asdict() for row in result]