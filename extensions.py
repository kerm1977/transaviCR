from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Esta es la única fuente de verdad para db y bcrypt
# Al estar en un archivo independiente, evitamos que Flask cree instancias duplicadas
db = SQLAlchemy()
bcrypt = Bcrypt()