# Archivo: extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Esta es la única fuente de verdad para db y bcrypt
# Al estar en un archivo independiente, evitamos que Flask cree instancias duplicadas
# y prevenimos errores de importación circular entre app.py y models.py
db = SQLAlchemy()
bcrypt = Bcrypt()