from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
import re
import smtplib
import ssl
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
DATABASE = 'registros_alia.db'

# Configuración SMTP (modifica estos valores con tus credenciales)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465
SMTP_USER = 'TU_CORREO@gmail.com'  # Cambia esto
SMTP_PASS = 'TU_CONTRASEÑA_DE_APP'  # Cambia esto (usa contraseña de aplicación)
FROM_NAME = 'Alia IA'

# Duración del código de verificación (en minutos)
CODE_EXPIRATION_MINUTES = 30

def init_db():
    """Inicializa la base de datos con la tabla de registros"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nombre TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            estado TEXT DEFAULT 'pendiente',
            codigo_verificacion TEXT,
            codigo_expira TIMESTAMP,
            verificado INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contactos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            nombre TEXT,
            mensaje TEXT NOT NULL,
            fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            estado TEXT DEFAULT 'nuevo'
        )
    ''')
    conn.commit()
    conn.close()

def validar_email(email):
    """Valida el formato del email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generar_codigo(longitud=6):
    return ''.join(random.choices(string.digits, k=longitud))

def enviar_email_verificacion(destinatario, codigo):
    asunto = 'Tu código de verificación - Alia IA'
    cuerpo = f'''
    <h2>Verifica tu correo para acceso anticipado a Alia IA</h2>
    <p>Tu código de verificación es:</p>
    <h1 style="color:#7c4dff;">{codigo}</h1>
    <p>Este código expira en {CODE_EXPIRATION_MINUTES} minutos.</p>
    <p>Si no solicitaste este registro, ignora este mensaje.</p>
    <br><br>
    <b>Alia IA</b>
    '''
    msg = MIMEMultipart()
    msg['From'] = f"{FROM_NAME} <{SMTP_USER}>"
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'html'))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, destinatario, msg.as_string())

@app.route('/')
def index():
    """Página principal - redirige a la página oficial"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Alia IA - Backend</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Alia IA - Backend</h1>
            <p>Servidor de registro funcionando correctamente</p>
            <p><a href="index.html">Ir a la página oficial</a></p>
        </div>
    </body>
    </html>
    '''

@app.route('/api/registro', methods=['POST'])
def registrar_usuario():
    """Endpoint para registrar usuarios para acceso anticipado"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email requerido'}), 400
        
        email = data['email'].strip().lower()
        nombre = data.get('nombre', '').strip()
        
        # Validar email
        if not validar_email(email):
            return jsonify({'error': 'Formato de email inválido'}), 400
        
        # Obtener información del cliente
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Guardar en base de datos
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        try:
            codigo = generar_codigo()
            expira = datetime.utcnow() + timedelta(minutes=CODE_EXPIRATION_MINUTES)
            cursor.execute('''
                INSERT INTO registros (email, nombre, ip_address, user_agent, codigo_verificacion, codigo_expira, estado, verificado)
                VALUES (?, ?, ?, ?, ?, ?, 'pendiente', 0)
                ON CONFLICT(email) DO UPDATE SET codigo_verificacion=excluded.codigo_verificacion, codigo_expira=excluded.codigo_expira, estado='pendiente', verificado=0
            ''', (email, nombre, ip_address, user_agent, codigo, expira))
            conn.commit()
            
            # Obtener el ID del registro
            registro_id = cursor.lastrowid
            
            enviar_email_verificacion(email, codigo)
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Te enviamos un código de verificación a tu correo.',
                'registro_id': registro_id
            }), 200
            
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Este email ya está registrado'}), 409
            
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/verificar', methods=['POST'])
def verificar_codigo():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    codigo = data.get('codigo', '').strip()
    if not email or not codigo:
        return jsonify({'error': 'Email y código requeridos'}), 400
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT codigo_verificacion, codigo_expira, verificado FROM registros WHERE email=?', (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Registro no encontrado'}), 404
    codigo_guardado, expira, verificado = row
    if verificado:
        conn.close()
        return jsonify({'success': True, 'message': 'Correo ya verificado.'}), 200
    if codigo != codigo_guardado:
        conn.close()
        return jsonify({'error': 'Código incorrecto'}), 400
    if datetime.utcnow() > datetime.strptime(expira, '%Y-%m-%d %H:%M:%S.%f'):
        conn.close()
        return jsonify({'error': 'El código ha expirado'}), 400
    cursor.execute('UPDATE registros SET verificado=1, estado="verificado" WHERE email=?', (email,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '¡Correo verificado correctamente!'}), 200

@app.route('/api/reenviar', methods=['POST'])
def reenviar_codigo():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email requerido'}), 400
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT nombre FROM registros WHERE email=?', (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Registro no encontrado'}), 404
    codigo = generar_codigo()
    expira = datetime.utcnow() + timedelta(minutes=CODE_EXPIRATION_MINUTES)
    cursor.execute('UPDATE registros SET codigo_verificacion=?, codigo_expira=?, verificado=0, estado="pendiente" WHERE email=?', (codigo, expira, email))
    conn.commit()
    conn.close()
    enviar_email_verificacion(email, codigo)
    return jsonify({'success': True, 'message': 'Nuevo código enviado a tu correo.'}), 200

@app.route('/api/contacto', methods=['POST'])
def enviar_contacto():
    """Endpoint para enviar mensajes de contacto"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'mensaje' not in data:
            return jsonify({'error': 'Email y mensaje requeridos'}), 400
        
        email = data['email'].strip().lower()
        nombre = data.get('nombre', '').strip()
        mensaje = data['mensaje'].strip()
        
        # Validar email
        if not validar_email(email):
            return jsonify({'error': 'Formato de email inválido'}), 400
        
        # Guardar mensaje de contacto
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO contactos (email, nombre, mensaje, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (email, nombre, mensaje, request.remote_addr))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '¡Mensaje enviado! Pronto nos pondremos en contacto.'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/admin/registros')
def admin_registros():
    """Panel de administración para ver registros"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registros ORDER BY fecha_registro DESC LIMIT 100')
        registros = cursor.fetchall()
        conn.close()
        
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin - Registros Alia IA</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .stats { margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <h1>📊 Panel de Administración - Alia IA</h1>
            <div class="stats">
                <h3>Estadísticas:</h3>
                <p>Total de registros: ''' + str(len(registros)) + '''</p>
            </div>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Email</th>
                    <th>Nombre</th>
                    <th>Fecha</th>
                    <th>Estado</th>
                    <th>Verificado</th>
                </tr>
        '''
        
        for registro in registros:
            html += f'''
                <tr>
                    <td>{registro[0]}</td>
                    <td>{registro[1]}</td>
                    <td>{registro[2] or '-'}</td>
                    <td>{registro[3]}</td>
                    <td>{registro[6]}</td>
                    <td>{'Sí' if registro[9] else 'No'}</td>
                </tr>
            '''
        
        html += '''
            </table>
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        return f'Error: {str(e)}', 500

if __name__ == '__main__':
    init_db()
    print("🚀 Servidor de registro Alia IA iniciado")
    print("📧 Endpoint de registro: http://localhost:5000/api/registro")
    print("📞 Endpoint de contacto: http://localhost:5000/api/contacto")
    print("👨‍💼 Panel admin: http://localhost:5000/admin/registros")
    app.run(debug=True, host='0.0.0.0', port=5000) 