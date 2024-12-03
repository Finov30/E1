from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.exc import OperationalError

URL_DATABASE = "mysql+pymysql://root@localhost:3306/test"

engine = create_engine(URL_DATABASE, echo=True)

meta = MetaData()

def create_tables():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    tables_to_create = [table for table in meta.tables.values() if table.name not in existing_tables]
    
    if not tables_to_create:
        print("Toutes les tables existent déjà.")
        return

    try:
        meta.create_all(engine, tables=tables_to_create)
        print(f"Tables créées avec succès : {', '.join(table.name for table in tables_to_create)}")
    except OperationalError as e:
        print(f"Erreur lors de la création des tables : {e}")

conn = engine.connect()