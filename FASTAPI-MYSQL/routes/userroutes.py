from fastapi import APIRouter, File, UploadFile, HTTPException
from config.database import conn
from models.indexmodels import users, user_ids
from schemas.index import users as user_schema, address_table
from sqlalchemy import select
from cryptography.fernet import Fernet
from pydantic import BaseModel
from typing import List
import csv
import io
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
from faker import Faker

load_dotenv()  # Chargement des variables d'environnement

user = APIRouter()
fake = Faker()

# Gestion sécurisée de la clé de chiffrement
key = os.getenv('ENCRYPTION_KEY')
if key is None:
    raise ValueError("ENCRYPTION_KEY non trouvée dans le fichier .env. Veuillez la définir.")

cipher_suite = Fernet(key.encode())

def encrypt_data(data: str) -> str:
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    return cipher_suite.decrypt(data.encode()).decode()

# Modèles pour les adresses
class AddressBase(BaseModel):
    street: str
    zipcode: str
    country: str
    user_id: int

class AddressCreate(AddressBase):
    pass

class Address(AddressBase):
    id: int

    class Config:
        orm_mode = True

# Routes existantes
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

# Nouvelles routes pour gestion des utilisateurs et adresses
@user.post("/fetch-external-users")
async def fetch_external_users():
    try:
        users_data = []
        for _ in range(10):
            user_data = {
                "name": fake.name(),
                "email": encrypt_data(fake.email()),
                "password": encrypt_data(fake.password())
            }
            user_query = users.insert().values(**user_data)
            result = conn.execute(user_query)
            user_id = result.inserted_primary_key[0]
            users_data.append({**user_data, "id": user_id})

            # Generate and insert corresponding address
            address_data = {
                "user_id": user_id,
                "street": fake.street_address(),
                "zipcode": fake.postcode(),
                "country": fake.country()
            }
            address_query = address_table.insert().values(**address_data)
            conn.execute(address_query)

        return {"message": "Users and addresses created successfully", "users": users_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user.post("/addresses/", response_model=Address)
async def create_address(address: AddressCreate):
    user_query = select(users).where(users.c.id == address.user_id)
    user_result = conn.execute(user_query).first()
    if not user_result:
        raise HTTPException(status_code=404, detail="User not found")

    query = address_table.insert().values(**address.dict())
    result = conn.execute(query)
    return {**address.dict(), "id": result.inserted_primary_key[0]}

@user.get("/addresses/", response_model=List[Address])
async def read_addresses():
    query = select(address_table)
    result = conn.execute(query).fetchall()
    return [dict(row._asdict()) for row in result]  # Correction ici

@user.get("/addresses/{address_id}", response_model=Address)
async def read_address(address_id: int):
    query = select(address_table).where(address_table.c.id == address_id)
    result = conn.execute(query).first()
    if not result:
        raise HTTPException(status_code=404, detail="Address not found")
    return dict(result._asdict())  # Correction ici pour retourner un dict correctement

@user.put("/addresses/{address_id}", response_model=Address)
async def update_address(address_id: int, address: AddressCreate):
    user_query = select(users).where(users.c.id == address.user_id)
    user_result = conn.execute(user_query).first()
    if not user_result:
        raise HTTPException(status_code=404, detail="User not found")

    query = address_table.update().where(
        address_table.c.id == address_id
    ).values(**address.dict())
    result = conn.execute(query)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Address not found")
    return {**address.dict(), "id": address_id}

@user.delete("/addresses/{address_id}")
async def delete_address(address_id: int):
    query = address_table.delete().where(address_table.c.id == address_id)
    result = conn.execute(query)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Address not found")
    return {"message": "Address deleted successfully"}

@user.get("/users/{user_id}/addresses", response_model=List[Address])
async def get_user_addresses(user_id: int):
    query = select(address_table).where(address_table.c.user_id == user_id)
    result = conn.execute(query).fetchall()
    addresses = [dict(row._asdict()) for row in result]  # Correction ici
    if not addresses:
        raise HTTPException(status_code=404, detail="No addresses found for this user")
    return addresses

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
