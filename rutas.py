from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from extensions import db
from models import User, Collaborator, Bus, Reservation, AboutUs

# Definición del Blueprint principal
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Vista principal con los formularios de reserva e información de contacto."""
    about = AboutUs.query.first()
    return render_template('home.html', about=about)

@main_bp.route('/reserve', methods=['POST'])
def create_reservation():
    """Procesa las solicitudes de transporte estándar."""
    day = request.form.get('day')
    month = request.form.get('month')
    year = request.form.get('year')
    date_str = f"{day}-{month}-{year}"
    
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
        comments=request.form.get('comments'),
        status='Pendiente'
    )
    db.session.add(new_res)
    db.session.commit()
    flash("Reserva solicitada con éxito. Nos pondremos en contacto pronto.", "success")
    return redirect(url_for('main.home'))

@main_bp.route('/dashboard')
def dashboard():
    """Panel de administración con estadísticas y gestión de registros."""
    stats = {
        'reservations': Reservation.query.count(),
        'users': User.query.count(),
        'colabs': Collaborator.query.count()
    }
    colaboradores = Collaborator.query.all()
    about = AboutUs.query.first()
    return render_template('dashboard.html', stats=stats, colabs=colaboradores, about=about)

@main_bp.route('/dashboard/update_whatsapp', methods=['POST'])
def update_whatsapp():
    """Actualiza los números de contacto de WhatsApp desde el Dashboard."""
    about = AboutUs.query.first()
    if not about:
        about = AboutUs()
        db.session.add(about)
    
    about.mobile_admin = request.form.get('mobile_admin')
    about.mobile_service = request.form.get('mobile_service')
    db.session.commit()
    flash("Números de WhatsApp actualizados correctamente.", "success")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard/export')
def export_data():
    """Exporta todas las reservas registradas a un archivo .txt."""
    res = Reservation.query.all()
    content = "REPORTE DETALLADO DE RESERVAS\n" + "="*30 + "\n"
    for r in res:
        content += f"ID: {r.id}\n"
        content += f"Fecha: {r.date} | Hora: {r.departure_time}\n"
        content += f"Destino: {r.destination}\n"
        content += f"Servicio: {r.service_category}\n"
        content += f"Comentarios: {r.comments if r.comments else 'Ninguno'}\n"
        content += f"Estado: {r.status}\n"
        content += "-"*30 + "\n"
    
    with open("reporte_reservas.txt", "w", encoding='utf-8') as f:
        f.write(content)
    flash("Datos exportados exitosamente a reporte_reservas.txt", "info")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/colaboradores/add', methods=['POST'])
def add_colab():
    """Registra un nuevo colaborador junto con sus busetas asociadas."""
    new_c = Collaborator(
        name=request.form.get('name'),
        last_name1=request.form.get('last_name1'),
        last_name2=request.form.get('last_name2'),
        mobile=request.form.get('mobile'),
        email=request.form.get('email'),
        license_type=request.form.get('license'),
        ownership=request.form.get('ownership')
    )
    db.session.add(new_c)
    db.session.commit()
    
    # Procesar busetas dinámicas
    bus_count = int(request.form.get('bus_count', 1))
    for i in range(bus_count):
        bus = Bus(
            owner=new_c,
            brand=request.form.get(f'brand_{i}'),
            plate=request.form.get(f'plate_{i}'),
            year=request.form.get(f'year_{i}'),
            capacity=request.form.get(f'capacity_{i}'),
            service_type=request.form.get(f'services_{i}')
        )
        db.session.add(bus)
    
    db.session.commit()
    flash("Colaborador y unidades registrados con éxito.", "success")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/aboutus')
def view_about():
    """Muestra la página informativa 'Sobre Nosotros'."""
    info = AboutUs.query.first()
    return render_template('aboutus.html', info=info)

@main_bp.route('/aboutus/create', methods=['GET', 'POST'])
def create_about():
    """Permite crear o editar la información institucional de la empresa."""
    if request.method == 'POST':
        existing = AboutUs.query.first()
        if existing: 
            # Actualizar campos existentes
            existing.mission = request.form.get('mission')
            existing.vision = request.form.get('vision')
            existing.phone_admin = request.form.get('phone_admin')
            existing.mobile_admin = request.form.get('mobile_admin')
            existing.mobile_service = request.form.get('mobile_service')
            existing.email = request.form.get('email')
            existing.description = request.form.get('description')
        else:
            # Crear nuevo registro
            new_info = AboutUs(
                mission=request.form.get('mission'),
                vision=request.form.get('vision'),
                phone_admin=request.form.get('phone_admin'),
                mobile_admin=request.form.get('mobile_admin'),
                mobile_service=request.form.get('mobile_service'),
                email=request.form.get('email'),
                description=request.form.get('description')
            )
            db.session.add(new_info)
        
        db.session.commit()
        flash("Información institucional actualizada.", "success")
        return redirect(url_for('main.view_about'))
    
    about = AboutUs.query.first()
    return render_template('aboutus_create.html', about=about)

@main_bp.route('/delete/<string:category>/<int:id>', methods=['POST'])
def erase_item(category, id):
    """Elimina registros de la base de datos con confirmación."""
    if category == 'user':
        item = User.query.get_or_404(id)
    elif category == 'colab':
        item = Collaborator.query.get_or_404(id)
    elif category == 'res':
        item = Reservation.query.get_or_404(id)
    elif category == 'about':
        item = AboutUs.query.get_or_404(id)
    else:
        flash("Categoría de eliminación no válida.", "danger")
        return redirect(url_for('main.dashboard'))
    
    db.session.delete(item)
    db.session.commit()
    flash(f"Registro de {category} eliminado satisfactoriamente.", "warning")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/manifest.json')
def manifest():
    """Sirve el archivo manifest para la instalación PWA."""
    return send_from_directory('static', 'manifest.json')

@main_bp.route('/sw.js')
def sw():
    """Sirve el Service Worker para habilitar capacidades offline (PWA)."""
    return send_from_directory('static', 'sw.js')