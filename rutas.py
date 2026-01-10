# Archivo: rutas.py
import os
import random
import string
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app, session, jsonify
from extensions import db
# Importamos todos los modelos necesarios, incluyendo el nuevo Client
from models import Collaborator, Bus, Reservation, AboutUs, Client
# Importamos la seguridad desde users.py
from users import User, login_required
from werkzeug.utils import secure_filename

main_bp = Blueprint('main', __name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_pin():
    """
    Genera un PIN ALFANUMÉRICO de 8 caracteres (Letras Mayúsculas y Números).
    Ejemplo: A1B2C3D4
    """
    characters = string.ascii_uppercase + string.digits
    while True:
        pin = ''.join(random.choices(characters, k=8))
        if not Client.query.filter_by(pin=pin).first():
            return pin

@main_bp.route('/')
def home():
    """Ruta principal: Carga la página de inicio."""
    about = AboutUs.query.first()
    return render_template('home.html', about=about)

@main_bp.route('/api/get_client/<pin>', methods=['GET'])
def get_client_info(pin):
    """
    API JSON: Busca un cliente por su PIN para autocompletar.
    """
    pin = pin.upper()
    client = Client.query.filter_by(pin=pin).first()
    if client:
        return jsonify({
            'success': True,
            'name': client.name,
            'last_name1': client.last_name1,
            'last_name2': client.last_name2,
            'phone': client.phone,
            'email': client.email
        })
    return jsonify({'success': False})

@main_bp.route('/api/recover_pin', methods=['POST'])
def recover_pin():
    """
    API para recuperar el PIN validando teléfono y email.
    """
    data = request.get_json()
    phone = data.get('phone')
    email = data.get('email')
    
    if not phone or not email:
        return jsonify({'success': False, 'message': 'Por favor ingrese ambos datos.'})
    
    # Buscar cliente que coincida exactamente con ambos datos
    client = Client.query.filter_by(phone=phone, email=email).first()
    
    if client:
        return jsonify({'success': True, 'pin': client.pin, 'name': client.name})
    else:
        return jsonify({'success': False, 'message': 'No encontramos un registro que coincida con ese Teléfono y Email.'})

@main_bp.route('/reserve', methods=['POST'])
def create_reservation():
    """
    Procesa el formulario de reserva.
    Maneja validación de duplicados y creación de clientes.
    """
    # ---------------------------------------------------------
    # 1. GESTIÓN DEL CLIENTE (Datos Personales y PIN)
    # ---------------------------------------------------------
    pin_ingresado = request.form.get('client_pin')
    if pin_ingresado:
        pin_ingresado = pin_ingresado.upper() # Normalizar

    client = None
    is_new_client = False # Bandera para saber si debemos mostrar el modal
    new_pin_generated = None
    
    # Capturar datos del formulario
    name = request.form.get('client_name')
    lname1 = request.form.get('client_lastname1')
    lname2 = request.form.get('client_lastname2')
    phone = request.form.get('client_phone')
    email = request.form.get('client_email')

    # A. Intentar buscar si existe por PIN
    if pin_ingresado:
        client = Client.query.filter_by(pin=pin_ingresado).first()
    
    if client:
        # Si existe, actualizamos sus datos (por si cambiaron teléfono/email)
        client.name = name
        client.last_name1 = lname1
        client.last_name2 = lname2
        client.phone = phone
        client.email = email
    else:
        # B. Intento de registro NUEVO -> VALIDAR DUPLICADOS
        
        # 1. Validar Teléfono existente
        existing_phone = Client.query.filter_by(phone=phone).first()
        if existing_phone:
            flash(f"El número de teléfono {phone} ya está registrado. Por favor use la opción '¿Olvidó su PIN?'", "danger")
            return redirect(url_for('main.home'))
            
        # 2. Validar Email existente
        existing_email = Client.query.filter_by(email=email).first()
        if existing_email:
            flash(f"El correo electrónico {email} ya está registrado. Por favor use la opción '¿Olvidó su PIN?'", "danger")
            return redirect(url_for('main.home'))

        # Si no existen duplicados, creamos un nuevo cliente
        new_pin_generated = generate_pin()
        client = Client(
            pin=new_pin_generated,
            name=name,
            last_name1=lname1,
            last_name2=lname2,
            phone=phone,
            email=email
        )
        db.session.add(client)
        db.session.commit() # Commit necesario para obtener el ID y asegurar el PIN
        is_new_client = True

    # ---------------------------------------------------------
    # 2. PROCESAMIENTO DE DATOS SEGÚN TIPO DE SERVICIO
    # ---------------------------------------------------------
    service_type = request.form.get('service_type')
    
    # Variables por defecto para campos que varían según el form
    date_str = "Pendiente"
    destination_val = request.form.get('destination')
    
    if service_type == 'Viajes Internacionales':
        # Para internacional, la fecha principal es la de salida específica
        date_str = request.form.get('int_departure_date')
        # El destino es la descripción detallada
        destination_val = request.form.get('int_description')
    else:
        # Para otros servicios, construimos la fecha con los dropdowns
        day = request.form.get('day')
        month = request.form.get('month')
        year = request.form.get('year')
        if day and month and year:
            date_str = f"{day}-{month}-{year}"

    # ---------------------------------------------------------
    # 3. CREACIÓN DE LA RESERVA
    # ---------------------------------------------------------
    new_res = Reservation(
        client=client,  # Relación con el objeto Cliente
        
        # Datos Generales
        date=date_str,
        origin=request.form.get('origin'),
        origin_url=request.form.get('origin_url'),
        departure_time=request.form.get('time'),
        needs_pickup=request.form.get('pickup') == 'si',
        pickup_locations=request.form.get('pickup_list'),
        destination=destination_val,
        destination_url=request.form.get('destination_url'),
        service_category=service_type,
        capacity_needed=int(request.form.get('capacity', 0) or 0),
        comments=request.form.get('comments'),
        
        # Datos Específicos: Estudiantes
        institution_name=request.form.get('institution_name'),
        schedule_type=request.form.get('schedule_type'),
        
        # Datos Específicos: Internacional
        country=request.form.get('int_country'),
        return_date=request.form.get('int_return_date'),
        trip_duration=int(request.form.get('int_days', 0) or 0)
    )
    
    db.session.add(new_res)
    db.session.commit()
    
    # Manejo de Mensajes y Modals
    if is_new_client and new_pin_generated:
        # Usamos una categoría especial 'new_pin_modal' para que el frontend lo detecte
        flash(f"{new_pin_generated}", "new_pin_modal") 
    else:
        flash("Solicitud enviada correctamente. Puedes ver el estado en la sección 'Mis Solicitudes' con tu PIN.", "success")

    return redirect(url_for('main.home'))

# --- RUTA PARA CANCELAR RESERVA (CLIENTE) ---
@main_bp.route('/cancel_reservation/<int:id>', methods=['POST'])
def cancel_reservation(id):
    """
    Marca la reserva como 'Cancelada' y guarda la fecha/hora.
    """
    res = Reservation.query.get_or_404(id)
    
    # Solo permitimos cancelar si está pendiente
    if res.status == 'Pendiente':
        # Generar timestamp legible
        now = datetime.now().strftime("%d/%m/%Y %I:%M %p")
        
        res.status = 'Cancelada'
        res.cancelled_at = now
        
        db.session.commit()
        flash("Tu solicitud ha sido cancelada y registrada en tu historial.", "warning")
    else:
        flash("No se puede cancelar esta solicitud en su estado actual.", "danger")
        
    return redirect(url_for('main.home'))

# --- RUTA PARA REVISAR RESERVA (ADMIN) ---
@main_bp.route('/review_reservation/<int:id>', methods=['POST'])
@login_required
def review_reservation(id):
    """
    Permite al administrador marcar una solicitud como 'Revisado'.
    """
    # Verificar que sea admin
    if session.get('role') != 'admin':
        flash("No tienes permisos para realizar esta acción.", "danger")
        return redirect(url_for('main.home'))

    res = Reservation.query.get_or_404(id)
    return_pin = request.form.get('return_pin') # Capturamos el PIN para volver a la misma pantalla

    if res.status == 'Pendiente':
        res.status = 'Revisado'
        db.session.commit()
        flash(f"Solicitud #{id} marcada como REVISADA.", "success")
    
    # Truco para volver a mostrar la vista de perfil del usuario sin que el admin tenga que buscarlo de nuevo
    if return_pin:
        client = Client.query.filter_by(pin=return_pin).first()
        if client:
            reservations = Reservation.query.filter_by(client_id=client.id).order_by(Reservation.id.desc()).all()
            return render_template('perfil.html', client=client, reservations=reservations, pin=return_pin)
    
    return redirect(url_for('main.dashboard'))

# --- RUTA PARA EDITAR RESERVA (CLIENTE) ---
@main_bp.route('/edit_reservation/<int:id>', methods=['GET', 'POST'])
def edit_reservation(id):
    """
    Permite al usuario modificar todos los datos de su solicitud si está Pendiente.
    """
    res = Reservation.query.get_or_404(id)
    
    # Validación: Solo editar si está pendiente
    if res.status != 'Pendiente':
        flash("Solo se pueden editar solicitudes que estén pendientes.", "warning")
        if res.client:
            return render_template('perfil.html', client=res.client, reservations=Reservation.query.filter_by(client_id=res.client.id).order_by(Reservation.id.desc()).all(), pin=res.client.pin)
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        # 1. Actualizar Datos del Cliente
        if res.client:
            res.client.name = request.form.get('client_name')
            res.client.last_name1 = request.form.get('client_lastname1')
            res.client.last_name2 = request.form.get('client_lastname2')
            res.client.phone = request.form.get('client_phone')
            res.client.email = request.form.get('client_email')

        # 2. Actualizar Datos de Reserva
        service_type = request.form.get('service_type')
        res.service_category = service_type
        
        # Lógica de fechas según servicio
        if service_type == 'Viajes Internacionales':
            res.date = request.form.get('int_departure_date')
            res.destination = request.form.get('int_description') # Descripción en internacional
            res.country = request.form.get('int_country')
            res.return_date = request.form.get('int_return_date')
            res.trip_duration = int(request.form.get('int_days', 0) or 0)
            # Limpiar campos de otros servicios
            res.institution_name = None
            res.schedule_type = None
        elif service_type == 'Transporte de Estudiantes':
            # Construir fecha si se enviaron partes
            day = request.form.get('day')
            month = request.form.get('month')
            year = request.form.get('year')
            if day and month and year:
                res.date = f"{day}-{month}-{year}"
            
            res.institution_name = request.form.get('institution_name')
            res.schedule_type = request.form.get('schedule_type')
            # Limpiar campos internacional
            res.country = None
            res.return_date = None
            res.trip_duration = None
        else: # Servicios Especiales
            day = request.form.get('day')
            month = request.form.get('month')
            year = request.form.get('year')
            if day and month and year:
                res.date = f"{day}-{month}-{year}"
            
            res.destination = request.form.get('destination')
            # Limpiar otros
            res.institution_name = None
            res.country = None

        # Datos comunes
        res.origin = request.form.get('origin')
        res.origin_url = request.form.get('origin_url')
        res.destination_url = request.form.get('destination_url')
        res.departure_time = request.form.get('time')
        res.capacity_needed = int(request.form.get('capacity', 0) or 0)
        res.comments = request.form.get('comments')
        res.needs_pickup = request.form.get('pickup') == 'si'
        res.pickup_locations = request.form.get('pickup_list')

        db.session.commit()
        flash("Solicitud actualizada correctamente.", "success")
        
        # Redirigir al perfil simulando el PIN
        return render_template('perfil.html', client=res.client, reservations=Reservation.query.filter_by(client_id=res.client.id).order_by(Reservation.id.desc()).all(), pin=res.client.pin)

    return render_template('perfil_edit.html', res=res, client=res.client)

# ---------------------------------------------------------
# RUTAS ADMINISTRATIVAS (DASHBOARD)
# ---------------------------------------------------------

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Panel de control protegido."""
    stats = {
        'reservations_count': Reservation.query.count(),
        'users_count': User.query.count(),
        'colabs_count': Collaborator.query.count()
    }
    colaboradores = Collaborator.query.all()
    reservas = Reservation.query.all()
    about = AboutUs.query.first()
    return render_template('dashboard.html', stats=stats, colabs=colaboradores, reservas=reservas, about=about)

@main_bp.route('/dashboard/export')
@login_required
def export_data():
    """Genera un archivo de texto con el reporte de reservas."""
    res = Reservation.query.all()
    content = "REPORTE DE RESERVAS\n" + "="*20 + "\n"
    
    for r in res:
        cliente_nombre = f"{r.client.name} {r.client.last_name1}" if r.client else "Sin Cliente"
        extra_info = ""
        if r.service_category == 'Viajes Internacionales':
             extra_info = f" | País: {r.country} | Regreso: {r.return_date} ({r.trip_duration} días)"
        
        status_str = r.status
        if r.status == 'Cancelada' and r.cancelled_at:
            status_str += f" ({r.cancelled_at})"
            
        content += f"ID: {r.id} | Cliente: {cliente_nombre} | Destino: {r.destination} | Salida: {r.date} | Estado: {status_str}{extra_info}\n"
    
    with open("reporte_reservas.txt", "w") as f:
        f.write(content)
        
    flash("Datos exportados a reporte_reservas.txt", "info")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard/update_status/<int:id>/<string:new_status>', methods=['POST'])
@login_required
def update_status(id, new_status):
    """Cambia el estado de una reserva (ej: Pendiente -> Aprobada)."""
    res = Reservation.query.get_or_404(id)
    res.status = new_status
    db.session.commit()
    flash(f"Reserva #{id} actualizada a {new_status}", "success")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard/update_whatsapp', methods=['POST'])
@login_required
def update_whatsapp():
    """Actualiza los números de contacto."""
    about = AboutUs.query.first()
    if not about:
        about = AboutUs()
        db.session.add(about)
    about.mobile_admin = request.form.get('mobile_admin')
    about.mobile_service = request.form.get('mobile_service')
    db.session.commit()
    flash("Números de contacto actualizados", "success")
    return redirect(url_for('main.dashboard'))

# ---------------------------------------------------------
# GESTIÓN DE COLABORADORES
# ---------------------------------------------------------

@main_bp.route('/colaboradores/add', methods=['POST'])
@login_required
def add_colab():
    """Agrega un nuevo colaborador y sus buses."""
    new_c = Collaborator(
        name=request.form.get('name'),
        last_name1=request.form.get('last_name1'),
        last_name2=request.form.get('last_name2'),
        mobile=request.form.get('mobile'),
        email=request.form.get('email'),
        license_type=request.form.get('license'),
        ownership=request.form.get('ownership')
    )
    
    # Manejo de foto
    if 'photo' in request.files:
        file = request.files['photo']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            new_c.photo = f"uploads/{filename}"

    db.session.add(new_c)
    db.session.commit()
    
    # Agregar buses asociados
    bus_count = int(request.form.get('bus_count', 1))
    for i in range(bus_count):
        brand = request.form.get(f'brand_{i}')
        if brand:
            bus = Bus(
                owner=new_c,
                brand=brand,
                plate=request.form.get(f'plate_{i}'),
                year=request.form.get(f'year_{i}'),
                capacity=request.form.get(f'capacity_{i}'),
                service_type=request.form.get(f'services_{i}')
            )
            db.session.add(bus)
            
    db.session.commit()
    flash("Colaborador agregado", "success")
    return redirect(url_for('main.dashboard'))

# ---------------------------------------------------------
# OTRAS RUTAS (About Us, Delete, PWA)
# ---------------------------------------------------------

@main_bp.route('/aboutus')
def view_about():
    info = AboutUs.query.first()
    return render_template('aboutus.html', info=info)

@main_bp.route('/aboutus/create', methods=['GET', 'POST'])
@login_required
def create_about():
    if request.method == 'POST':
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

        if 'logo' in request.files:
            file = request.files['logo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                about.logo = f"uploads/{filename}"

        db.session.commit()
        flash("Información de empresa actualizada", "success")
        return redirect(url_for('main.view_about'))
    
    about = AboutUs.query.first()
    return render_template('aboutus_create.html', about=about)

@main_bp.route('/delete/<string:category>/<int:id>', methods=['POST'])
@login_required
def erase_item(category, id):
    item = None
    if category == 'user':
        if id == session.get('user_id'):
            flash("No puedes eliminar tu propia cuenta.", "warning")
            return redirect(url_for('main.dashboard'))
        item = User.query.get_or_404(id)
    elif category == 'colab':
        item = Collaborator.query.get_or_404(id)
    elif category == 'res':
        item = Reservation.query.get_or_404(id)
    elif category == 'about':
        item = AboutUs.query.get_or_404(id)
    
    if item:
        db.session.delete(item)
        db.session.commit()
        flash(f"Elemento eliminado correctamente", "warning")
    
    return redirect(url_for('main.dashboard'))

@main_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@main_bp.route('/sw.js')
def sw():
    return send_from_directory('static', 'sw.js')