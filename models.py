# Archivo: models.py
from extensions import db

# NOTA: El modelo 'User' se encuentra en 'users.py' (anteriormente admin.py)

class Client(db.Model):
    """
    Modelo para almacenar la información de los clientes recurrentes.
    Se identifican por un PIN único.
    """
    id = db.Column(db.Integer, primary_key=True)
    pin = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    last_name1 = db.Column(db.String(50), nullable=False)
    last_name2 = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(8), nullable=False)
    email = db.Column(db.String(100))
    
    # Relación con reservas
    reservations = db.relationship('Reservation', backref='client', lazy=True)

class Collaborator(db.Model):
    """
    Modelo para los colaboradores (choferes/transportistas).
    """
    id = db.Column(db.Integer, primary_key=True)
    photo = db.Column(db.String(255))
    name = db.Column(db.String(50))
    last_name1 = db.Column(db.String(50))
    last_name2 = db.Column(db.String(50))
    phone_fixed = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    email = db.Column(db.String(100))
    license_type = db.Column(db.String(50))
    ownership = db.Column(db.String(20)) 
    buses = db.relationship('Bus', backref='owner', lazy=True, cascade="all, delete-orphan")

class Bus(db.Model):
    """
    Modelo para las unidades de transporte.
    """
    id = db.Column(db.Integer, primary_key=True)
    collaborator_id = db.Column(db.Integer, db.ForeignKey('collaborator.id'))
    brand = db.Column(db.String(50))
    plate = db.Column(db.String(20))
    year = db.Column(db.Integer)
    capacity = db.Column(db.Integer)
    service_type = db.Column(db.String(50)) 

class Reservation(db.Model):
    """
    Modelo para las solicitudes de reserva.
    """
    id = db.Column(db.Integer, primary_key=True)
    # Relación con el Cliente
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    
    date = db.Column(db.String(20)) # Usado como Fecha de Salida
    origin = db.Column(db.String(255))
    origin_url = db.Column(db.String(500))
    departure_time = db.Column(db.String(10))
    needs_pickup = db.Column(db.Boolean)
    pickup_locations = db.Column(db.Text) 
    destination = db.Column(db.String(255))
    destination_url = db.Column(db.String(500))
    service_category = db.Column(db.String(50))
    capacity_needed = db.Column(db.Integer)
    comments = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pendiente')
    
    # Campos específicos: Estudiantes
    institution_name = db.Column(db.String(100))
    schedule_type = db.Column(db.String(50))
    
    # Campos específicos: Internacional (NUEVOS)
    country = db.Column(db.String(50))       # País destino
    return_date = db.Column(db.String(20))   # Fecha de regreso
    trip_duration = db.Column(db.Integer)    # Cantidad de días

class AboutUs(db.Model):
    """
    Modelo para la información de contacto y configuración de la empresa.
    """
    id = db.Column(db.Integer, primary_key=True)
    logo = db.Column(db.String(255))
    mission = db.Column(db.Text)
    vision = db.Column(db.Text)
    phone_admin = db.Column(db.String(8))
    mobile_admin = db.Column(db.String(8))
    mobile_service = db.Column(db.String(8))
    email = db.Column(db.String(100))
    description = db.Column(db.Text)