# Archivo: profile.py
from flask import Blueprint, render_template, request, flash
from models import Client, Reservation

# Definimos el Blueprint para el perfil
profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/perfil', methods=['GET', 'POST'])
def my_requests():
    """
    Vista donde el cliente ingresa su PIN para ver sus solicitudes.
    """
    client = None
    reservations = []
    pin_searched = ""
    
    if request.method == 'POST':
        pin_searched = request.form.get('pin', '').strip().upper()
        
        if pin_searched:
            client = Client.query.filter_by(pin=pin_searched).first()
            if client:
                # Obtener reservas ordenadas por ID descendente (las más nuevas primero)
                reservations = Reservation.query.filter_by(client_id=client.id)\
                                                .order_by(Reservation.id.desc()).all()
                if not reservations:
                    flash("Hola " + client.name + ", aún no tienes solicitudes registradas.", "info")
            else:
                flash("No se encontró ningún cliente con ese PIN. Verifica e intenta de nuevo.", "danger")
        else:
            flash("Por favor ingresa un PIN.", "warning")
            
    return render_template('perfil.html', client=client, reservations=reservations, pin=pin_searched)