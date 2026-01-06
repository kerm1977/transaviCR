# Archivo: rutas.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from extensions import db
from models import User, Collaborator, Bus, Reservation, AboutUs
from werkzeug.utils import secure_filename

# Crear un Blueprint para las rutas principales de la aplicación
main_bp = Blueprint('main', __name__)

# Configuración para subida de archivos (asegúrate de crear la carpeta 'static/uploads')
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
def home():
    """
    Ruta para la página de inicio.
    Renderiza la plantilla 'home.html'.
    """
    about = AboutUs.query.first()
    return render_template('home.html', about=about)

@main_bp.route('/reserve', methods=['POST'])
def create_reservation():
    """
    Ruta para crear una nueva reserva.
    Procesa los datos del formulario enviado por POST.
    """
    # Obtener la fecha seleccionada del formulario
    day = request.form.get('day')
    month = request.form.get('month')
    year = request.form.get('year')
    date_str = f"{day}-{month}-{year}"
    
    # Crear una nueva instancia de Reserva con los datos del formulario
    new_res = Reservation(
        date=date_str,
        origin=request.form.get('origin'),
        origin_url=request.form.get('origin_url'),
        departure_time=request.form.get('time'),
        needs_pickup=request.form.get('pickup') == 'si',
        pickup_locations=request.form.get('pickup_list'),
        destination=request.form.get('destination'),
        destination_url=request.form.get('destination_url'),
        service_category=request.form.get('service_type'),
        capacity_needed=int(request.form.get('capacity', 0)),
        comments=request.form.get('comments')
    )
    # Agregar la nueva reserva a la sesión de la base de datos
    db.session.add(new_res)
    # Confirmar los cambios en la base de datos
    db.session.commit()
    # Mostrar un mensaje de éxito al usuario
    flash("Reserva solicitada con éxito", "success")
    # Redirigir al usuario a la página de inicio
    return redirect(url_for('main.home'))

@main_bp.route('/dashboard')
def dashboard():
    """
    Ruta para el panel de control (Dashboard).
    Obtiene estadísticas y datos para mostrar en el dashboard.
    """
    # Calcular estadísticas básicas
    stats = {
        'reservations': Reservation.query.count(),
        'users': User.query.count(),
        'colabs': Collaborator.query.count()
    }
    # Obtener todos los colaboradores y la información 'About Us'
    colaboradores = Collaborator.query.all()
    about = AboutUs.query.first()
    # Renderizar la plantilla del dashboard con los datos obtenidos
    return render_template('dashboard.html', stats=stats, colabs=colaboradores, about=about)

@main_bp.route('/dashboard/export')
def export_data():
    """
    Ruta para exportar los datos de las reservas a un archivo de texto.
    """
    # Obtener todas las reservas de la base de datos
    res = Reservation.query.all()
    # Crear el contenido del reporte
    content = "REPORTE DE RESERVAS\n" + "="*20 + "\n"
    for r in res:
        content += f"ID: {r.id} | Destino: {r.destination} | Fecha: {r.date} | Estado: {r.status} | Comentarios: {r.comments}\n"
    
    # Escribir el contenido en un archivo llamado "reporte_reservas.txt"
    with open("reporte_reservas.txt", "w") as f:
        f.write(content)
    # Mostrar un mensaje informativo
    flash("Datos exportados a reporte_reservas.txt", "info")
    # Redirigir al dashboard
    return redirect(url_for('main.dashboard'))

@main_bp.route('/colaboradores/add', methods=['POST'])
def add_colab():
    """
    Ruta para agregar un nuevo colaborador.
    Procesa el formulario para crear un colaborador y sus buses asociados.
    """
    # Crear una nueva instancia de Colaborador
    new_c = Collaborator(
        name=request.form.get('name'),
        last_name1=request.form.get('last_name1'),
        last_name2=request.form.get('last_name2'),
        mobile=request.form.get('mobile'),
        email=request.form.get('email'),
        license_type=request.form.get('license'),
        ownership=request.form.get('ownership')
    )
    # Agregar el colaborador a la base de datos
    db.session.add(new_c)
    # Confirmar para obtener el ID del colaborador
    db.session.commit()
    
    # Procesar los buses asociados
    bus_count = int(request.form.get('bus_count', 1))
    for i in range(bus_count):
        # Crear una nueva instancia de Bus vinculada al colaborador
        bus = Bus(
            owner=new_c, # Relación con el colaborador recién creado
            brand=request.form.get(f'brand_{i}'),
            plate=request.form.get(f'plate_{i}'),
            year=request.form.get(f'year_{i}'),
            capacity=request.form.get(f'capacity_{i}'),
            service_type=request.form.get(f'services_{i}')
        )
        db.session.add(bus)
    
    # Confirmar la adición de los buses
    db.session.commit()
    flash("Colaborador agregado", "success")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/aboutus')
def view_about():
    """
    Ruta para ver la página 'Sobre Nosotros'.
    """
    info = AboutUs.query.first()
    return render_template('aboutus.html', info=info)

@main_bp.route('/aboutus/create', methods=['GET', 'POST'])
def create_about():
    """
    Ruta para crear o actualizar la información de 'Sobre Nosotros'.
    Maneja la carga de la imagen del logo.
    """
    if request.method == 'POST':
        # Si ya existe información, la actualizamos en lugar de borrar y crear nueva
        # para preservar el ID y simplificar la lógica
        about = AboutUs.query.first()
        if not about:
            about = AboutUs()
            db.session.add(about)

        about.mission = request.form.get('mission')
        about.vision = request.form.get('vision')
        about.phone_admin = request.form.get('phone_admin')
        about.mobile_admin = request.form.get('mobile_admin')
        about.mobile_service = request.form.get('mobile_service')
        about.email = request.form.get('email')
        about.description = request.form.get('description')

        # Manejo de la imagen (logo)
        if 'logo' in request.files:
            file = request.files['logo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Asegurar que el directorio de subida existe
                upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
                os.makedirs(upload_path, exist_ok=True)
                
                file.save(os.path.join(upload_path, filename))
                about.logo = f"uploads/{filename}" # Guardar ruta relativa para usar en HTML

        db.session.commit()
        flash("Información de empresa actualizada", "success")
        return redirect(url_for('main.view_about'))
    
    # GET request
    about = AboutUs.query.first()
    return render_template('aboutus_create.html', about=about)

@main_bp.route('/delete/<string:category>/<int:id>', methods=['POST'])
def erase_item(category, id):
    """
    Ruta para eliminar elementos (usuarios, colaboradores, reservas, aboutus).
    """
    if category == 'user':
        item = User.query.get_or_404(id)
    elif category == 'colab':
        item = Collaborator.query.get_or_404(id)
    elif category == 'res':
        item = Reservation.query.get_or_404(id)
    elif category == 'about':
        item = AboutUs.query.get_or_404(id)
    
    db.session.delete(item)
    db.session.commit()
    flash(f"Eliminado correctamente", "warning")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/manifest.json')
def manifest():
    """
    Ruta para servir el archivo manifest.json para PWA.
    """
    return send_from_directory('static', 'manifest.json')

@main_bp.route('/sw.js')
def sw():
    """
    Ruta para servir el Service Worker para PWA.
    """
    return send_from_directory('static', 'sw.js')