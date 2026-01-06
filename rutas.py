from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from extensions import db
from models import User, Collaborator, Bus, Reservation, AboutUs

# Definición del Blueprint para organizar las rutas
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Vista principal con el formulario de reserva."""
    return render_template('home.html')

@main_bp.route('/reserve', methods=['POST'])
def create_reservation():
    """Procesa la solicitud de reserva desde el formulario principal."""
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
        comments=request.form.get('comments')
    )
    db.session.add(new_res)
    db.session.commit()
    flash("Reserva solicitada con éxito", "success")
    return redirect(url_for('main.home'))

@main_bp.route('/dashboard')
def dashboard():
    """Panel de administración con estadísticas y gestión de datos."""
    stats = {
        'reservations': Reservation.query.count(),
        'users': User.query.count(),
        'colabs': Collaborator.query.count()
    }
    colaboradores = Collaborator.query.all()
    about = AboutUs.query.first()
    return render_template('dashboard.html', stats=stats, colabs=colaboradores, about=about)

@main_bp.route('/dashboard/export')
def export_data():
    """Exporta las reservas actuales a un archivo de texto."""
    res = Reservation.query.all()
    content = "REPORTE DE RESERVAS\n" + "="*20 + "\n"
    for r in res:
        content += f"ID: {r.id} | Destino: {r.destination} | Fecha: {r.date} | Estado: {r.status} | Comentarios: {r.comments}\n"
    
    # Ruta relativa al servidor
    with open("reporte_reservas.txt", "w") as f:
        f.write(content)
    flash("Datos exportados a reporte_reservas.txt", "info")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/colaboradores/add', methods=['POST'])
def add_colab():
    """Agrega un nuevo colaborador y sus unidades de transporte."""
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
    
    # Manejo dinámico de busetas
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
    flash("Colaborador agregado correctamente", "success")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/aboutus')
def view_about():
    """Vista pública de la información de la empresa."""
    info = AboutUs.query.first()
    return render_template('aboutus.html', info=info)

@main_bp.route('/aboutus/create', methods=['GET', 'POST'])
def create_about():
    """Formulario para que los dueños editen la información de contacto."""
    if request.method == 'POST':
        existing = AboutUs.query.first()
        if existing: db.session.delete(existing)
        
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
        flash("Información de empresa actualizada", "success")
        return redirect(url_for('main.view_about'))
    return render_template('aboutus_create.html')

@main_bp.route('/delete/<string:category>/<int:id>', methods=['POST'])
def erase_item(category, id):
    """Lógica para borrar registros (usuarios, colaboradores, reservas o info)."""
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
    flash(f"Registro eliminado correctamente", "warning")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/manifest.json')
def manifest():
    """Archivo para la funcionalidad PWA."""
    return send_from_directory('static', 'manifest.json')

@main_bp.route('/sw.js')
def sw():
    """Service Worker para la funcionalidad PWA."""
    return send_from_directory('static', 'sw.js')