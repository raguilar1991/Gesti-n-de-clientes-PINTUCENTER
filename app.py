#================ IMPORTACIONES ==================
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session # Importamos las librerías necesarias de Flask
import os, sqlite3 # Importamos sqlite3 para manejar la base de datos
from werkzeug.security import generate_password_hash, check_password_hash # Importamos funciones para hashear contraseñas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'clientes.db')

app=Flask(__name__)
app.secret_key='clave_secreta_tmimport'

#=============ahora voy a conectar con la base de datos===========
def conectar_bd():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def crear_tabla_cotizaciones():
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cotizaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        ruc TEXT,
        empresa TEXT,
        contacto TEXT,
        correo TEXT,
        telefono TEXT,
        estado TEXT DEFAULT 'pendiente',
        subtotal REAL DEFAULT 0.0,
        fecha TEXT DEFAULT (datetime('now','localtime')),
        notas TEXT,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    conn.close()
    print("✅ Tabla cotizaciones creada (o ya existía) en:", DB_PATH)

# llamar una sola vez para crear
#crear_tabla_cotizaciones()

#==============RUTA PARA COTIZACIONES===================
@app.route('/crear_cotizacion', methods=['POST'])
def crear_cotizacion():
    cliente_id = request.form.get('cliente_id')  # o buscar por ruc
    subtotal = float(request.form.get('subtotal', 0))
    estado = request.form.get('estado', 'pendiente')
    notas = request.form.get('notas', '')

    conn = conectar_bd()
    cursor = conn.cursor()
    # activar foreign keys por si acaso
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Obtener datos del cliente para guardar copia
    cursor.execute("SELECT ruc, empresa, nombre, apellido, correo, telefono FROM clientes WHERE id = ?", (cliente_id,))
    c = cursor.fetchone()
    if not c:
        flash('Cliente no encontrado', 'danger')
        return redirect(url_for('clientes_busqueda'))

    ruc = c['ruc']
    empresa = c['empresa']
    contacto = (c['nombre'] or '') + ' ' + (c['apellido'] or '')
    correo = c['correo']
    telefono = c['telefono']

    cursor.execute("""
        INSERT INTO cotizaciones (cliente_id, ruc, empresa, contacto, correo, telefono, estado, subtotal, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cliente_id, ruc, empresa, contacto, correo, telefono, estado, subtotal, notas))

    conn.commit()
    conn.close()
    flash('Cotización creada', 'success')
    return redirect(url_for('main'))

#==============AGREGAR CLIENTES===================
@app.route('/agregar_cliente', methods=['GET','POST'])
def agregar_cliente():
    if request.method == 'POST':
        ruc=request.form.get('ruc')
        empresa=request.form.get('empresa')
        nombre=request.form.get('nombre')
        apellido=request.form.get('apellido')
        correo=request.form.get('correo')
        telefono=request.form.get('telefono')

        if not ruc or not empresa:
            flash('RUC y Empresa son obligatorios', 'danger')
            return redirect(url_for('agregar_cliente'))

        try:
            conn=conectar_bd()
            cursor=conn.cursor()
            cursor.execute(""" INSERT INTO clientes (ruc, empresa, nombre, apellido, correo, telefono) VALUES (?, ?, ?, ?, ?, ?) """,
                           (ruc, empresa, nombre, apellido, correo, telefono))
            conn.commit()
            conn.close()
            flash('Cliente agregado exitosamente', 'success')
            return redirect(url_for('main'))
        except Exception as e:
            flash(f'Error al agregar cliente: {e}', 'danger')
            return redirect(url_for('agregar_cliente'))
    return render_template('agregar_cliente.html', usuario="Usuario")

#===========ruta principal muestra el fomulario login===================
@app.route('/')
def login():
    return render_template('login.html') #aqui se muestra el formulario de login

#=============ruta que valida el login=====================
@app.route('/validar_login', methods=['POST'])
def validar_login():
    usuario=request.form['usuario']
    contrasena=request.form['contrasena']

    conn=conectar_bd()
    cursor=conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE usuario=?', (usuario,))
    row = cursor.fetchone()
    conn.close()

    if row and check_password_hash(row['contrasena'], contrasena):
        session['usuario'] = usuario  # Guardar el usuario en la sesión
        return redirect(url_for('main')) #si el login es correcto redirige a la ruta main
    else:
        flash('Usuario o contraseña incorrectos')
        return redirect(url_for('login')) #si el login es incorrecto redirige a la ruta login

#=================ruta para el logout==================
@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))

#=================Ruta formulario de crear cotizacion================
@app.route('/nueva_cotizacion')
def nueva_cotizacion():
    if 'usuario' not in session:
        flash('Debe iniciar sesión primero.', 'warning')
        return redirect(url_for('login'))

    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clientes')
    clientes = cursor.fetchall()
    conn.close()

    return render_template('crear_cotizacion.html', clientes=clientes)
#=================ruta principal despues del login================
@app.route('/main')
def main():
    if 'usuario' not in session:
        flash('Debe iniciar sesión primero.', 'warning')
        return redirect(url_for('login'))

    usuario = session.get('usuario', 'Usuario')
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clientes')
    clientes = cursor.fetchall()
    conn.close()
    return render_template('main.html', usuario=usuario, clientes=clientes)

#==================ruta para ver los productos=====================
@app.route('/productos')
def productos():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    conn.close()
    return render_template('productos.html', productos=productos)

#=================ruta para registrar nuevos usuarios==================
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        confirmpass = request.form['confirmpass']
        
        if contrasena != confirmpass:
            flash('Las contraseñas no coinciden')
            return redirect(url_for('registrar'))
        
        if not usuario or not contrasena or not confirmpass:
            flash('Todos los campos son obligatorios')
            return redirect(url_for('registrar'))

        hash = generate_password_hash(contrasena)
        conn = conectar_bd()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO usuarios (usuario, contrasena) VALUES (?, ?)', (usuario, hash))
            conn.commit()
            flash('Usuario registrado exitosamente')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El usuario ya existe')
            return redirect(url_for('registrar'))
        finally:
            conn.close()
    return render_template('registrar.html')

#=================ruta para verificar usuario y contraseña hasheadas==================
#===Sirve para depurar, pero no debería quedar activa en producción porque muestra hashes. ✔️ Está bien para test, ❌ pero elimínala o protégela con autenticación una vez que tu app esté en uso real.
@app.route('/verificar_usuario')
def verificar_usuario():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, contrasena FROM usuarios WHERE usuario = ?", ('jportalanza',))
    row = cursor.fetchone()
    conn.close()

    if row:
        return f"Usuario: {row['usuario']}<br>Contraseña (hash): {row['contrasena']}"
    else:
        return "Usuario no encontrado"

#=================ruta para buscar clientes==================    
# BUSCAR CLIENTE (POST desde el formulario de búsqueda)
@app.route('/buscar_cliente', methods=['POST'])
def buscar_cliente():
    if 'usuario' not in session:
        flash('Debe iniciar sesión primero.', 'warning')
        return redirect(url_for('login'))

    # Tomamos el criterio de forma segura y lo normalizamos
    criterio_raw = request.form.get('criterio', '').strip()
    criterio = criterio_raw.lower()

    conn = conectar_bd()
    cursor = conn.cursor()

    if criterio == '':
        # Si el criterio está vacío, devolvemos todos los clientes
        cursor.execute('SELECT * FROM clientes')
        clientes = cursor.fetchall()
    else:
        like = f"%{criterio}%"
        # Buscamos en ruc, nombre, apellido y empresa (case-insensitive usando LOWER)
        cursor.execute("""
            SELECT * FROM clientes
            WHERE LOWER(nombre) LIKE ?
               OR LOWER(apellido) LIKE ?
               OR LOWER(empresa) LIKE ?
               OR LOWER(ruc) LIKE ?
        """, (like, like, like, like))
        clientes = cursor.fetchall()

    conn.close()

    # Renderizamos la plantilla principal con los resultados y el usuario real de la sesión
    usuario = session.get('usuario', 'Usuario')
    return render_template('main.html', usuario=usuario, clientes=clientes)

# =========================== RUTA API: OBTENER PRODUCTOS ===========================
@app.route('/api/productos')
def api_productos():
    try:
        conn = conectar_bd()
        conn.row_factory = sqlite3.Row  # 🔹 Asegura nombres de columnas
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre_producto, marca, precio, stock
            FROM productos
            ORDER BY nombre_producto
        """)
        rows = cursor.fetchall()
        productos = [dict(row) for row in rows]
        return jsonify(productos)
    except Exception as e:
        print("Error al obtener productos:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ---------------------------
# Rutas para el menú "Clientes"
# ---------------------------

# Ruta comodín /clientes que redirige a la página de búsqueda
@app.route('/clientes')
def clientes_index():
    # Si no hay sesión activa, forzamos login
    if 'usuario' not in session:
        flash('Debe iniciar sesión primero.', 'warning')
        return redirect(url_for('login'))
    # Redireccionamos a la vista de búsqueda (mantiene la URL limpia)
    return redirect(url_for('clientes_busqueda'))


# Ruta que muestra la misma plantilla main.html pero cuando se accede desde
# "Clientes > Búsqueda" (útil para enlazar desde el submenú).

@app.route('/clientes/busqueda')
def clientes_busqueda():
    # Verificamos que el usuario esté autenticado; si no, redirigimos al login
    if 'usuario' not in session:
        flash('Debe iniciar sesión primero.', 'warning')
        return redirect(url_for('login'))

    # Obtenemos el usuario actual desde la sesión (siempre usar session para el nombre)
    usuario = session.get('usuario', 'Usuario')

    # Abrimos conexión a la BD, obtenemos todos los clientes y la cerramos
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clientes')  # traemos todos por defecto
    clientes = cursor.fetchall()
    conn.close()

    # Renderizamos main.html pasándole el usuario y la lista de clientes
    # (la plantilla ya contiene el formulario de búsqueda que POSTea a /buscar_cliente)
    return render_template('main.html', usuario=usuario, clientes=clientes)

#=================ejecuto la app================== 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)