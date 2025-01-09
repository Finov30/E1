from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String
from config.database import meta

user_ids = Table(
    'user_ids', meta,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), unique=True),
    Column('external_id', String(255), unique=True)
)

users = Table(
    'users', meta, 
    Column('id', Integer, primary_key=True),
    Column('name', String(255)),
    Column('email', String(255)),
    Column('password', String(255))
)

