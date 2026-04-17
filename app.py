import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
from tienda_db import TiendaDB
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'camila-joyeria-2026'
db = TiendaDB()

UPLOAD_FOLDER = os.path.join('static', 'img')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_USER = 'camila'
ADMIN_PASS = 'joyeria2026'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_requerido(f):
    from functools import wraps
    @wraps(f)
    def decorador(*args, **kwargs):
        if not session.get('admin'):
            flash('Necesitas iniciar sesión como administrador.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorador

# ── LOGIN ADMIN / LOGOUT ─────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contrasena = request.form.get('contrasena')
        if usuario == ADMIN_USER and contrasena == ADMIN_PASS:
            session['admin'] = True
            flash('Bienvenida, Camila 💛')
            return redirect(url_for('admin_productos'))
        else:
            flash('Usuario o contraseña incorrectos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Sesión cerrada.')
    return redirect(url_for('index'))

# ── REGISTRO / LOGIN CLIENTE ─────────────────────────────────────────
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre     = request.form.get('nombre')
        email      = request.form.get('email')
        contrasena = request.form.get('contrasena')
        if db.obtener_usuario_por_email(email):
            flash('Ya existe una cuenta con ese correo.')
            return redirect(url_for('registro'))
        db.registrar_usuario(nombre, email, contrasena)
        flash('Cuenta creada con éxito. Ya puedes iniciar sesión.')
        return redirect(url_for('login_cliente'))
    return render_template('registro.html')

@app.route('/login-cliente', methods=['GET', 'POST'])
def login_cliente():
    if request.method == 'POST':
        email      = request.form.get('email')
        contrasena = request.form.get('contrasena')
        usuario    = db.obtener_usuario_por_email(email)
        if usuario and usuario['contrasena'] == contrasena:
            session['usuario'] = {'id': usuario['id'], 'nombre': usuario['nombre']}
            flash(f'Bienvenida, {usuario["nombre"]} 💛')
            return redirect(url_for('index'))
        else:
            flash('Correo o contraseña incorrectos.')
    return render_template('login_cliente.html')

@app.route('/logout-cliente')
def logout_cliente():
    session.pop('usuario', None)
    flash('Sesión cerrada.')
    return redirect(url_for('index'))

# ── TIENDA (CLIENTE) ────────────────────────────────────────────
@app.route('/')
def index():
    productos = db.obtener_productos()
    avisos    = db.obtener_avisos_activos()
    return render_template('index.html', productos=productos, avisos=avisos)

@app.route('/producto/<int:producto_id>')
def producto(producto_id):
    p = db.obtener_producto(producto_id)
    return render_template('producto.html', p=p)

@app.route('/carrito')
def carrito():
    carrito_session = session.get('carrito', {})
    productos = db.obtener_productos()
    items, total = [], 0
    for prod_id, qty in carrito_session.items():
        p = next((x for x in productos if str(x['id']) == str(prod_id)), None)
        if p:
            subtotal = p['precio'] * qty
            total   += subtotal
            items.append({'p': p, 'qty': qty, 'subtotal': subtotal})
    return render_template('carrito.html', items=items, total=total)

@app.route('/carrito/agregar', methods=['POST'])
def carrito_agregar():
    prod_id  = request.form.get('producto_id')
    cantidad = int(request.form.get('cantidad', 1))
    carrito_session = session.get('carrito', {})
    carrito_session[prod_id] = carrito_session.get(prod_id, 0) + cantidad
    session['carrito'] = carrito_session
    flash('Producto agregado al carrito 💛')
    return redirect(url_for('index'))

@app.route('/carrito/quitar', methods=['POST'])
def carrito_quitar():
    prod_id = request.form.get('producto_id')
    carrito_session = session.get('carrito', {})
    if prod_id in carrito_session:
        del carrito_session[prod_id]
    session['carrito'] = carrito_session
    return redirect(url_for('carrito'))

# ── CHECKOUT con verificación y descuento de stock ──────────────
@app.route('/verificar', methods=['POST'])
def verificar():
    """Muestra resumen del pedido antes de confirmar."""
    nombre = request.form.get('nombre', '')
    email  = request.form.get('email', '')
    carrito_session = session.get('carrito', {})
    productos = db.obtener_productos()
    items, total = [], 0
    for prod_id, qty in carrito_session.items():
        p = next((x for x in productos if str(x['id']) == str(prod_id)), None)
        if p:
            subtotal = p['precio'] * qty
            total   += subtotal
            items.append({'p': p, 'qty': qty, 'subtotal': subtotal})
    return render_template('verificar.html', items=items, total=total,
                           nombre=nombre, email=email)

@app.route('/checkout', methods=['POST'])
def checkout():
    nombre     = request.form.get('nombre', 'Cliente')
    email      = request.form.get('email', '')
    carrito_session = session.get('carrito', {})
    productos  = db.obtener_productos()
    items, total = [], 0
    for prod_id, qty in carrito_session.items():
        p = next((x for x in productos if str(x['id']) == str(prod_id)), None)
        if p:
            subtotal = p['precio'] * qty
            total   += subtotal
            items.append({'p': p, 'qty': qty, 'subtotal': subtotal})
    usuario_id = session.get('usuario', {}).get('id')
    pedido_id  = db.guardar_pedido(nombre, email, total, items, usuario_id)
    session['carrito'] = {}
    return render_template('checkout_ok.html', nombre=nombre, pedido_id=pedido_id)

# ── ADMIN ───────────────────────────────────────────────────────
@app.route('/admin')
@admin_requerido
def admin_productos():
    productos = db.obtener_productos()
    return render_template('admin/productos.html', productos=productos)

@app.route('/admin/agregar', methods=['GET', 'POST'])
@admin_requerido
def admin_agregar():
    if request.method == 'POST':
        nombre      = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio      = float(request.form.get('precio', 0))
        stock       = int(request.form.get('stock', 0))
        imagen      = None
        archivo = request.files.get('imagen')
        if archivo and allowed_file(archivo.filename):
            filename = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagen = filename
        db.agregar_producto(nombre, descripcion, precio, stock, imagen)
        flash(f'Producto "{nombre}" agregado ✨')
        return redirect(url_for('admin_productos'))
    return render_template('admin/form_producto.html', producto=None, accion='Agregar')

@app.route('/admin/editar/<int:producto_id>', methods=['GET', 'POST'])
@admin_requerido
def admin_editar(producto_id):
    p = db.obtener_producto(producto_id)
    if request.method == 'POST':
        nombre      = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio      = float(request.form.get('precio', 0))
        stock       = int(request.form.get('stock', 0))
        imagen      = None
        archivo = request.files.get('imagen')
        if archivo and allowed_file(archivo.filename):
            filename = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagen = filename
        db.editar_producto(producto_id, nombre, descripcion, precio, stock, imagen)
        flash(f'Producto "{nombre}" actualizado ✨')
        return redirect(url_for('admin_productos'))
    return render_template('admin/form_producto.html', producto=p, accion='Editar')

@app.route('/admin/eliminar/<int:producto_id>', methods=['POST'])
@admin_requerido
def admin_eliminar(producto_id):
    db.eliminar_producto(producto_id)
    flash('Producto eliminado.')
    return redirect(url_for('admin_productos'))

@app.route('/admin/pedidos', methods=['GET', 'POST'])
@admin_requerido
def admin_pedidos():
    if request.method == 'POST':
        # Actualizar estados de pedidos via checkboxes
        pedidos_todos = db.obtener_pedidos()
        for pedido in pedidos_todos:
            estado = request.form.get(f'estado_{pedido["id"]}', 'pendiente')
            db.actualizar_estado_pedido(pedido['id'], estado)
        flash('Pedidos actualizados.')
        return redirect(url_for('admin_pedidos'))

    pedidos = db.obtener_pedidos()
    pedidos_con_items = []
    for pedido in pedidos:
        items = db.obtener_items_pedido(pedido['id'])
        pedidos_con_items.append({'pedido': pedido, 'items': items})
    return render_template('admin/pedidos.html', pedidos=pedidos_con_items)

@app.route('/admin/reporte')
@admin_requerido
def admin_reporte():
    ventas = db.obtener_ventas_hoy()
    total_dia = sum(v['total'] for v in ventas)
    ganancia_dia = db.obtener_ganancia_hoy()
    return render_template('admin/reporte.html', ventas=ventas,
                           total_dia=total_dia, ganancia_dia=ganancia_dia)

# ── ADMIN COSTOS ────────────────────────────────────────────────
@app.route('/admin/costos', methods=['GET', 'POST'])
@admin_requerido
def admin_costos():
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('costo_'):
                producto_id = int(key.replace('costo_', ''))
                try:
                    costo = float(value)
                    db.actualizar_costo_proveedor(producto_id, costo)
                except ValueError:
                    pass
        flash('Costos de proveedor actualizados ✨')
        return redirect(url_for('admin_costos'))
    productos = db.obtener_productos()
    return render_template('admin/costos.html', productos=productos)

# ── ADMIN AVISOS ────────────────────────────────────────────────
@app.route('/admin/avisos', methods=['GET', 'POST'])
@admin_requerido
def admin_avisos():
    if request.method == 'POST':
        titulo  = request.form.get('titulo')
        mensaje = request.form.get('mensaje')
        db.agregar_aviso(titulo, mensaje)
        flash('Aviso publicado.')
        return redirect(url_for('admin_avisos'))
    avisos = db.obtener_todos_avisos()
    return render_template('admin/avisos.html', avisos=avisos)

@app.route('/admin/avisos/eliminar/<int:aviso_id>', methods=['POST'])
@admin_requerido
def admin_eliminar_aviso(aviso_id):
    db.eliminar_aviso(aviso_id)
    flash('Aviso eliminado.')
    return redirect(url_for('admin_avisos'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
