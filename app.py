import os
import smtplib
import random
import string
import re
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from image_analyzer import analyze_image_with_ai
import os

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("✅ google.generativeai importado correctamente")
except ImportError as e:
    genai = None
    GEMINI_AVAILABLE = False
    print(f"❌ Error importando google.generativeai: {e}")
    print("📋 Información del sistema:")
    import sys, os
    print(f"   - Python: {sys.version}")
    print(f"   - Plataforma: {sys.platform}")
    print(f"   - PATH: {os.environ.get('PATH', 'No encontrado')[:100]}...")
    print(
        "🔧 Solución alternativa: Las dependencias del sistema se están cargando..."
    )
    try:
        import ctypes
        import glob
        lib_paths = glob.glob('/nix/store/*/lib/libstdc++.so.6*')
        if lib_paths:
            ctypes.CDLL(lib_paths[0])
            print("✅ Librerías del sistema cargadas manualmente")
        else:
            print("❌ No se encontraron las librerías del sistema necesarias")
    except Exception as lib_error:
        print(f"❌ Error cargando librerías: {lib_error}")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False
    print("Advertencia: openai no disponible")

import sqlite3

# Usar funciones propias en lugar de chat_db
# from chat_db import (
#     init_db,
#     save_message,
#     get_chat_history,
#     get_all_chats_for_user,
#     delete_chat_history,
# )

def save_message(email, chat_id, message, sender, time):
    try:
        conn = sqlite3.connect('alia_chat.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                message TEXT NOT NULL,
                sender TEXT NOT NULL,
                time TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        
        cursor.execute("""
            INSERT INTO messages (email, chat_id, message, sender, time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (email, chat_id, message, sender, time, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f"✅ Mensaje guardado: {sender} - {message[:50]}...")
    except Exception as e:
        print(f"❌ Error saving message: {e}")

# Funciones para nuevas características
def save_image_to_gallery(email, image_url, prompt):
    """Guarda imagen en galería del usuario"""
    try:
        import json
        gallery_file = f"gallery_{email.replace('@', '_').replace('.', '_')}.json"
        
        try:
            with open(gallery_file, 'r') as f:
                gallery = json.load(f)
        except:
            gallery = []
        
        gallery.append({
            'url': image_url,
            'prompt': prompt,
            'timestamp': datetime.now().isoformat()
        })
        
        # Mantener solo las últimas 50 imágenes
        gallery = gallery[-50:]
        
        with open(gallery_file, 'w') as f:
            json.dump(gallery, f)
    except Exception as e:
        print(f"Error guardando en galería: {e}")

def search_web_info(query):
    """Búsqueda web usando múltiples APIs gratuitas"""
    try:
        import requests
        import urllib.parse
        from datetime import datetime
        
        # Si pregunta por hora/fecha, responder directamente
        if any(word in query.lower() for word in ['hora', 'fecha', 'qué día', 'hoy']):
            from datetime import datetime as dt_now
            fecha_actual = dt_now.now()
            return f"Fecha y hora actual: {fecha_actual.strftime('%d de %B de %Y, %H:%M')} (hora del servidor)"
        
        # Para GTA VI, información conocida
        if 'gta' in query.lower() and any(word in query.lower() for word in ['vi', '6', 'six', 'sale', 'lanzamiento']):
            return "GTA VI (Grand Theft Auto VI) fue anunciado oficialmente por Rockstar Games y está programado para lanzarse en 2025 para PlayStation 5 y Xbox Series X/S. Inicialmente no estará disponible para PC al lanzamiento."
        
        # Intentar con Wikipedia API
        try:
            encoded_query = urllib.parse.quote(query)
            wiki_url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{encoded_query}"
            response = requests.get(wiki_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    return data['extract'][:400]
        except:
            pass
        
        # Fallback con DuckDuckGo
        try:
            ddg_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            response = requests.get(ddg_url, timeout=5)
            data = response.json()
            
            result = ""
            if data.get('Abstract'):
                result = data['Abstract']
            elif data.get('Definition'):
                result = data['Definition']
            elif data.get('Answer'):
                result = data['Answer']
            
            return result[:400] if result else None
        except:
            pass
            
        return None
    except Exception as e:
        print(f"Error en búsqueda web: {e}")
        return None

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()
print("🔑 Cargando variables de entorno...")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret")
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
socketio = SocketIO(app, cors_allowed_origins="*")
USER_FILE = "usuarios.json"

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"🔍 GEMINI_API_KEY encontrada: {'Sí' if GEMINI_API_KEY else 'No'}")
print(f"🔍 GEMINI_AVAILABLE: {GEMINI_AVAILABLE}")

if GEMINI_API_KEY and GEMINI_AVAILABLE:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ Gemini configurado correctamente")
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Modelo Gemini inicializado")
    except Exception as e:
        print(f"❌ Error configurando Gemini: {e}")
        GEMINI_AVAILABLE = False
else:
    print("❌ Gemini no está disponible")
    if not GEMINI_API_KEY:
        print("   - Razón: API key faltante")
    if not GEMINI_AVAILABLE:
        print(
            "   - Razón: Librería no importada (dependencias del sistema faltantes)"
        )
        print(
            "   - Solución: Ejecuta 'kill 1' en el terminal para reiniciar el entorno"
        )

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None
if OPENAI_API_KEY and OPENAI_AVAILABLE:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    print(
        "Advertencia: OpenAI API key no configurada o librería no disponible")

pending_codes = {}
reset_codes = {}
# init_db() # Ya no necesario, se crea automáticamente

intentos_fallidos = defaultdict(list)
MAX_INTENTOS = 5
BLOQUEO_MINUTOS = 10

MAINTENANCE_MODE = False


@app.route('/alia_voice_modal')
def alia_voice_modal():
    return render_template('alia_voice_modal.html')


# --- SOPORTE TECNICO POR CORREO (API AJAX) ACTUALIZADO ---
@app.route("/enviar_soporte", methods=["POST"])
def enviar_soporte():
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()
    dispositivo = request.form.get("dispositivo", "").strip()
    mensaje = request.form.get("mensaje", "").strip()
    tipo = request.form.get("tipo", "").strip()
    prioridad = request.form.get("prioridad", "Normal").strip()
    idusuario = request.form.get("idusuario", "").strip()
    imagen = request.files.get("captura", None)

    if not nombre or not email or not mensaje:
        return jsonify({
            "status": "error",
            "msg": "Faltan campos obligatorios"
        }), 400

    asunto = f"Soporte Alia: {tipo if tipo else 'Consulta'}"
    cid_img = "captura_img"
    img_block = ""
    if imagen and imagen.filename:
        img_block = f"""
        <div class="field-group" style="text-align:center;">
            <div class="field-label">Imagen adjunta</div>
            <img src="cid:{cid_img}" style="max-width:95%;border-radius:8px;box-shadow:0 2px 16px #aaa3;" alt="Captura adjunta">
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width-device-width, initial-scale=1.0">
        <title>Mensaje de Soporte - Alia</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            .content {{
                padding: 30px;
            }}
            .field-group {{
                margin-bottom: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid #6e48aa;
            }}
            .field-label {{
                font-weight: 600;
                color: #6e48aa;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 5px;
            }}
            .field-value {{
                color: #333;
                font-size: 16px;
                line-height: 1.5;
            }}
            .message-field {{
                background: #e8f2ff;
                border-left-color: #72eaff;
            }}
            .priority-high {{
                border-left-color: #ff6b6b;
            }}
            .footer {{
                background: #f1f3f4;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
            }}
            .footer p {{
                margin: 0;
                color: #666;
                font-size: 14px;
            }}
            .timestamp {{
                background: #e3f2fd;
                border-radius: 6px;
                padding: 10px;
                text-align: center;
                margin-bottom: 20px;
                color: #1565c0;
                font-weight: 500;
            }}
            .priority-group {{
                background: #fffbee;
                border-left: 4px solid #ffe082;
            }}
            .idusuario-group {{
                background: #f4e4ff;
                border-left: 4px solid #b388ff;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>💬 Nuevo mensaje de soporte</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Solicitud de asistencia técnica</p>
            </div>
            <div class="content">
                <div class="timestamp">
                    📅 Recibido el {datetime.now().strftime("%d/%m/%Y a las %H:%M")}
                </div>
                <div class="field-group">
                    <div class="field-label">Tipo de consulta</div>
                    <div class="field-value">{tipo if tipo else 'No especificado'}</div>
                </div>
                <div class="field-group priority-group">
                    <div class="field-label">Prioridad</div>
                    <div class="field-value">{prioridad}</div>
                </div>
                <div class="field-group idusuario-group">
                    <div class="field-label">ID de usuario</div>
                    <div class="field-value">{idusuario if idusuario else "(no proporcionado)"}</div>
                </div>
                <div class="field-group">
                    <div class="field-label">Nombre del usuario</div>
                    <div class="field-value">{nombre}</div>
                </div>
                <div class="field-group">
                    <div class="field-label">Correo electrónico</div>
                    <div class="field-value"><a href="mailto:{email}" style="color: #6e48aa; text-decoration: none;">{email}</a></div>
                </div>
                <div class="field-group">
                    <div class="field-label">Dispositivo</div>
                    <div class="field-value">{dispositivo}</div>
                </div>
                <div class="field-group message-field">
                    <div class="field-label">Mensaje completo</div>
                    <div class="field-value">{mensaje.replace(chr(10), '<br>')}</div>
                </div>
                {img_block}
            </div>
            <div class="footer">
                <p><strong>Alia - Asistente de IA</strong></p>
                <p>Este mensaje fue enviado desde el formulario de soporte técnico</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = Header(asunto, "utf-8")
        msg["From"] = formataddr((str(Header(nombre, "utf-8")), SMTP_USER))
        msg["To"] = SMTP_USER
        msg["Reply-To"] = email

        text_part = MIMEText(
            f"Tipo: {tipo}\nPrioridad: {prioridad}\nID usuario: {idusuario}\nNombre: {nombre}\nEmail: {email}\nDispositivo: {dispositivo}\nMensaje:\n{mensaje}",
            "plain", "utf-8")
        html_part = MIMEText(html_content, "html", "utf-8")

        alt = MIMEMultipart('alternative')
        alt.attach(text_part)
        alt.attach(html_part)
        msg.attach(alt)

        if imagen and imagen.filename:
            mimetype = imagen.mimetype or "image/png"
            maintype, subtype = mimetype.split('/', 1)
            img_att = MIMEBase(maintype, subtype)
            img_att.set_payload(imagen.read())
            encoders.encode_base64(img_att)
            img_att.add_header('Content-ID', f'<{cid_img}>')
            img_att.add_header('Content-Disposition',
                               'inline',
                               filename=imagen.filename)
            msg.attach(img_att)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, SMTP_USER, msg.as_string())

        return jsonify({"status": "ok"})
    except Exception as e:
        print("Error enviando correo soporte:", e)
        return jsonify({
            "status":
            "error",
            "msg":
            "No se pudo enviar el mensaje. Intenta más tarde o contacta directo por correo."
        }), 500


# --- ENVÍO CÓDIGO DE VERIFICACIÓN EMAIL ---
def enviar_codigo_correo(email, codigo):
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        # Cambia aquí al nombre correcto de tu plantilla
        with open("templates/verificacion_correo.html", "r",
                  encoding="utf-8") as f:
            html = f.read().replace("{{codigo}}", codigo)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Código de verificación - Alia"
        msg["From"] = SMTP_USER
        msg["To"] = email
        part = MIMEText(html, "html")
        msg.attach(part)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False


# ...resto del código igual que el tuyo original...
# Todas las rutas y helpers están igual y solo se ajusta la función anterior


# --- RESPUESTA DE SOPORTE CON ESTILO ---
@app.route("/responder_soporte", methods=["POST"])
def responder_soporte():
    """Endpoint para que el administrador responda consultas de soporte con estilo HTML"""
    email_usuario = request.form.get("email_usuario", "").strip()
    nombre_usuario = request.form.get("nombre_usuario", "").strip()
    asunto_original = request.form.get("asunto_original", "").strip()
    respuesta = request.form.get("respuesta", "").strip()
    admin_token = request.form.get("admin_token", "").strip()

    # Token simple de seguridad (puedes cambiarlo por algo más robusto)
    if admin_token != "alia_admin_2025":
        return jsonify({
            "status": "error",
            "msg": "Token de administrador inválido"
        }), 403

    if not email_usuario or not respuesta:
        return jsonify({
            "status": "error",
            "msg": "Email del usuario y respuesta son obligatorios"
        }), 400

    # Crear contenido HTML estilizado para la respuesta
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width-device-width, initial-scale=1.0">
        <title>Respuesta del Soporte - Alia</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            .content {{
                padding: 30px;
            }}
            .greeting {{
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                border-left: 4px solid #6e48aa;
            }}
            .response-content {{
                background: #e8f2ff;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                border-left: 4px solid #2196f3;
                line-height: 1.6;
            }}
            .footer {{
                background: #f1f3f4;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
            }}
            .footer p {{
                margin: 0;
                color: #666;
                font-size: 14px;
            }}
            .timestamp {{
                background: #e8f5e8;
                border-radius: 6px;
                padding: 10px;
                text-align: center;
                margin-bottom: 20px;
                color: #2e7d32;
                font-weight: 500;
            }}
            .contact-info {{
                background: #fff3e0;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
                border-left: 4px solid #ff9800;
            }}
            .signature {{
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid #eee;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>💬 Respuesta del Soporte Técnico</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Alia - Asistente de IA</p>
            </div>

            <div class="content">
                <div class="timestamp">
                    📅 Respondido el {datetime.now().strftime("%d/%m/%Y a las %H:%M")}
                </div>

                <div class="greeting">
                    <strong>Hola {nombre_usuario if nombre_usuario else 'Usuario'},</strong><br>
                    Gracias por contactarnos. Hemos revisado tu consulta y aquí tienes nuestra respuesta:
                </div>

                <div class="response-content">
                    {respuesta.replace(chr(10), '<br>')}
                </div>

                <div class="contact-info">
                    <strong>💡 ¿Necesitas ayuda adicional?</strong><br>
                    Si tienes más preguntas o necesitas ayuda adicional, no dudes en contactarnos nuevamente.<br>
                    Responde a este correo o escríbenos a: <strong>keymastergta@gmail.com</strong>
                </div>

                <div class="signature">
                    <strong>Equipo de Soporte Técnico</strong><br>
                    Alia - Asistente de IA<br>
                    <small>Horario de atención: Lunes a Domingo de 7:00 a 23:00</small>
                </div>
            </div>

            <div class="footer">
                <p><strong>Alia - Asistente de IA</strong></p>
                <p>Sistema de soporte técnico automatizado</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        asunto_respuesta = f"Re: {asunto_original}" if asunto_original else "Respuesta del Soporte - Alia"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(asunto_respuesta, "utf-8")
        msg["From"] = formataddr((str(Header("Soporte Alia",
                                             "utf-8")), SMTP_USER))
        msg["To"] = email_usuario

        # Adjuntar tanto texto plano como HTML
        text_part = MIMEText(
            f"Hola {nombre_usuario if nombre_usuario else 'Usuario'},\n\nGracias por contactarnos. Aquí tienes nuestra respuesta:\n\n{respuesta}\n\nSi necesitas más ayuda, contáctanos en keymastergta@gmail.com\n\nEquipo de Soporte Técnico\nAlia - Asistente de IA",
            "plain", "utf-8")
        html_part = MIMEText(html_content, "html", "utf-8")

        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, email_usuario, msg.as_string())

        return jsonify({
            "status": "ok",
            "msg": "Respuesta enviada con estilo HTML"
        })
    except Exception as e:
        print("Error enviando respuesta de soporte:", e)
        return jsonify({
            "status": "error",
            "msg": f"No se pudo enviar la respuesta: {str(e)}"
        }), 500


# ---- FIN SOPORTE ----


def cargar_usuarios():
    import json
    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def guardar_usuarios(usuarios):
    import json
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)


def enviar_codigo_correo(email, codigo):
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        with open("templates/email_verificacion_keymastergta.html",
                  "r",
                  encoding="utf-8") as f:
            html = f.read().replace("592521", codigo)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Código de verificación - Alia"
        msg["From"] = SMTP_USER
        msg["To"] = email
        part = MIMEText(html, "html")
        msg.attach(part)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False


def enviar_usuario_correo(email, usuario):
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width-device-width, initial-scale=1.0">
        <title>Recuperación de Usuario - Alia</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            .content {{
                padding: 30px;
                text-align: center;
            }}
            .user-info {{
                background: #f8f9fa;
                border-radius: 12px;
                padding: 25px;
                margin: 20px 0;
                border-left: 4px solid #6e48aa;
            }}
            .username {{
                font-size: 24px;
                font-weight: 700;
                color: #6e48aa;
                margin: 10px 0;
                letter-spacing: 1px;
            }}
            .info-text {{
                color: #666;
                font-size: 16px;
                line-height: 1.6;
                margin: 15px 0;
            }}
            .security-note {{
                background: #e3f2fd;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
                color: #1565c0;
                font-size: 14px;
                border-left: 4px solid #2196f3;
            }}
            .footer {{
                background: #f1f3f4;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
            }}
            .footer p {{
                margin: 0;
                color: #666;
                font-size: 14px;
            }}
            .timestamp {{
                background: #e8f5e8;
                border-radius: 6px;
                padding: 10px;
                text-align: center;
                margin-bottom: 20px;
                color: #2e7d32;
                font-weight: 500;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🔐 Recuperación de Usuario</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Tu información de acceso</p>
            </div>

            <div class="content">
                <div class="timestamp">
                    📅 Enviado el {datetime.now().strftime("%d/%m/%Y a las %H:%M")}
                </div>

                <p class="info-text">
                    Hemos encontrado el usuario registrado con tu correo electrónico:
                </p>

                <div class="user-info">
                    <div class="username">{usuario}</div>
                    <p style="margin: 10px 0 0 0; color: #888; font-size: 14px;">
                        Este es tu nombre de usuario para acceder a Alia
                    </p>
                </div>

                <div class="security-note">
                    <strong>💡 Consejo de seguridad:</strong><br>
                    Guarda esta información en un lugar seguro. Si necesitas ayuda adicional, 
                    puedes contactarnos en keymastergta@gmail.com
                </div>

                <p class="info-text">
                    Ahora puedes usar este usuario para iniciar sesión en tu cuenta de Alia.
                </p>
            </div>

            <div class="footer">
                <p><strong>Alia - Asistente de IA</strong></p>
                <p>Sistema automático de recuperación de usuario</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Recuperación de usuario - Alia"
    msg["From"] = SMTP_USER
    msg["To"] = email

    # Adjuntar tanto texto plano como HTML
    text_part = MIMEText(
        f"Recuperación de usuario\n\nEl usuario registrado con este correo es: {usuario}\n\nAlia - Asistente de IA",
        "plain", "utf-8")
    html_part = MIMEText(html_content, "html", "utf-8")

    msg.attach(text_part)
    msg.attach(html_part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


def es_contraseña_segura(password):
    requisitos = [
        (r'.{8,}', "al menos 8 caracteres"),
        (r'[A-Z]', "una letra mayúscula"),
        (r'[a-z]', "una letra minúscula"),
        (r'\d', "un número"),
        (r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?~]', "un símbolo"),
    ]
    faltantes = [
        desc for regex, desc in requisitos if not re.search(regex, password)
    ]
    return len(faltantes) == 0, faltantes


def esta_bloqueado(email):
    ahora = datetime.now()
    intentos_fallidos[email] = [
        t for t in intentos_fallidos[email]
        if ahora - t < timedelta(minutes=BLOQUEO_MINUTOS)
    ]
    if len(intentos_fallidos[email]) >= MAX_INTENTOS:
        return True
    return False


def sugerir_usuarios(usuario_base, usados, n=5):
    sugerencias = []
    sufijos = ["1", "123", "2025", "x", "h", "01", "00"]
    i = 0
    while len(sugerencias) < n and i < 30:
        if i == 0:
            candidato = usuario_base
        elif i <= len(sufijos):
            candidato = usuario_base + sufijos[i - 1]
        else:
            candidato = usuario_base + str(random.randint(10, 9999))
        if candidato not in usados and candidato not in sugerencias:
            sugerencias.append(candidato)
        i += 1
    return sugerencias


def generar_token_recordarme():
    return uuid.uuid4().hex


def guardar_token_recordarme(email, token):
    usuarios = cargar_usuarios()
    if email in usuarios:
        usuarios[email]["remember_token"] = token
        guardar_usuarios(usuarios)


def quitar_token_recordarme(email):
    usuarios = cargar_usuarios()
    if email in usuarios and "remember_token" in usuarios[email]:
        usuarios[email].pop("remember_token")
        guardar_usuarios(usuarios)


@app.before_request
def check_remember_me():
    # Si ya está en modo mantenimiento, no autologuear
    if MAINTENANCE_MODE:
        return
    if "email" not in session:
        token = request.cookies.get("recordarme")
        if token:
            usuarios = cargar_usuarios()
            for email, datos in usuarios.items():
                if datos.get("remember_token") == token:
                    session["email"] = email
                    session.permanent = True
                    session["mostrar_aviso_historial"] = True
                    break


@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No se recibió ninguna imagen'
            })

        file = request.files['file']
        user_text = request.form.get('text', '').strip()
        chat_id = request.form.get('chatId', '')
        email = session.get('email')

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No se seleccionó ningún archivo'
            })

        if not email:
            return jsonify({
                'success': False,
                'error': 'Sesión no válida'
            })

        print(f"🖼️ Analizando imagen: {file.filename}")
        print(f"📝 Texto del usuario: '{user_text}'")
        print(f"🔍 Gemini disponible: {GEMINI_AVAILABLE}")

        # Analizar imagen con Gemini unificado
        if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Servicio de análisis de imágenes no disponible'
            })

        # Usar el mismo modelo de Gemini que para texto
        try:
            from PIL import Image
            import io
            
            # Procesar imagen
            image = Image.open(file)
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(
                    image,
                    mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background

            # Crear prompt unificado
            if user_text:
                prompt = f"Analiza esta imagen enfocándote en: {user_text}. Si hay texto visible, transcríbelo exactamente. Responde en español y sé detallado."
            else:
                prompt = "Analiza detalladamente esta imagen. Si hay texto visible, transcríbelo exactamente. Describe objetos, personas, colores, contexto y atmósfera. Responde en español."

            # Usar el mismo modelo que para chat
            response = model.generate_content([prompt, image])
            
            if response and response.text:
                result = response.text
                
                # Guardar en historial si hay chat_id
                if chat_id:
                    user_message = user_text if user_text else "🖼️ Imagen enviada para análisis"
                    save_message(email, chat_id, user_message, "user", datetime.now().strftime("%H:%M"))
                    save_message(email, chat_id, result, "ai", datetime.now().strftime("%H:%M"))
                
                return jsonify({'success': True, 'description': result})
            else:
                return jsonify({
                    'success': False,
                    'error': 'No se pudo generar respuesta'
                })
                
        except Exception as e:
            print(f"❌ Error procesando imagen: {e}")
            return jsonify({
                'success': False,
                'error': f'Error procesando imagen: {str(e)}'
            })

    except Exception as e:
        print(f"❌ Error en análisis de imagen: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route("/sugerir_usuario")
def sugerir_usuario():
    usuario = request.args.get("usuario", "").strip().lower()
    if not usuario:
        return jsonify([])
    usuarios = cargar_usuarios()
    usados = set()
    for datos in usuarios.values():
        if "usuario" in datos:
            usados.add(datos["usuario"].lower())
    sugerencias = sugerir_usuarios(usuario, usados)
    return jsonify(sugerencias)


@app.route("/")
def index():
    if "email" not in session:
        return redirect(url_for("login"))
    mostrar_aviso_historial = session.get("mostrar_aviso_historial", True)
    return render_template("index.html",
                           mostrar_aviso_historial=mostrar_aviso_historial)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        identificador = request.form["usuario"].strip()
        password = request.form["contraseña"]
        recordarme = bool(request.form.get("recordarme"))
        usuarios = cargar_usuarios()
        email = None

        if identificador.lower() in usuarios:
            email = identificador.lower()
        else:
            for correo, datos in usuarios.items():
                if datos.get("usuario", "").lower() == identificador.lower():
                    email = correo
                    break

        bloqueado = email and esta_bloqueado(email)
        if not email or email not in usuarios:
            intentos_fallidos[identificador.lower()].append(datetime.now())
            error = "Credenciales incorrectas."
        elif bloqueado:
            error = "Demasiados intentos fallidos. Intenta de nuevo en 10 minutos."
        elif not check_password_hash(usuarios[email]["contraseña_hash"],
                                     password):
            intentos_fallidos[email].append(datetime.now())
            error = "Credenciales incorrectas."
        else:
            intentos_fallidos[email] = []
            session["email"] = email
            session.permanent = True
            session["mostrar_aviso_historial"] = True

            resp = make_response(redirect(url_for("index")))

            token = None
            if recordarme:
                token = generar_token_recordarme()
                guardar_token_recordarme(email, token)
                resp.set_cookie("recordarme", token, max_age=60 * 60 * 24 * 30)
            else:
                quitar_token_recordarme(email)
                resp.delete_cookie("recordarme")

            wants_json = (
                "application/json" in request.headers.get("Accept", "")
                or request.headers.get("X-Requested-With") == "XMLHttpRequest")
            if wants_json or request.is_json:
                return jsonify({"status": "ok", "remember_token": token})

            return resp

    soporte_url = url_for('soporte_tecnico')
    return render_template("login.html",
                           forgot_username_exists=True,
                           error=error,
                           soporte_url=soporte_url)


@app.route("/soporte.html")
def soporte_tecnico():
    return render_template("soporte.html")


@app.route("/admin/respuestas")
def admin_respuestas():
    """Panel de administración para responder consultas de soporte con estilo"""
    return render_template("admin_respuestas.html")


@app.route("/autologin", methods=["POST"])
def autologin():
    data = request.get_json()
    token = data.get("remember_token")
    usuarios = cargar_usuarios()
    for email, datos in usuarios.items():
        if datos.get("remember_token") == token:
            session["email"] = email
            session.permanent = True
            session["mostrar_aviso_historial"] = True
            return jsonify({"status": "ok"})
    return jsonify({"status": "fail"}), 401


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["contraseña"]
        if not usuario or not email or not password:
            error = "Todos los campos son obligatorios"
            return render_template("register.html", error=error)
        usuarios = cargar_usuarios()
        usados = set()
        for datos in usuarios.values():
            if "usuario" in datos:
                usados.add(datos["usuario"].lower())
        usuario_lower = usuario.lower()
        if usuario_lower in usados:
            sugerencias = sugerir_usuarios(usuario_lower, usados)
            error = "El usuario ya existe. Opciones disponibles: " + ", ".join(
                sugerencias)
            return render_template("register.html",
                                   error=error,
                                   sugerencias=sugerencias,
                                   usuario_intentado=usuario)
        es_segura, faltantes = es_contraseña_segura(password)
        if not es_segura:
            error = "La contraseña debe contener: " + ", ".join(
                faltantes) + "."
            return render_template("register.html", error=error)
        if email in usuarios:
            error = "El correo ya está registrado"
            return render_template("register.html", error=error)
        codigo = ''.join(random.choices(string.digits, k=6))
        pending_codes[email] = {
            "codigo": codigo,
            "password": password,
            "usuario": usuario,
            "timestamp": datetime.now()
        }
        if enviar_codigo_correo(email, codigo):
            return redirect(url_for("verify_code", email=email))
        else:
            error = "Error enviando código de verificación"
            return render_template("register.html", error=error)
    soporte_url = url_for('soporte_tecnico')
    return render_template("register.html", soporte_url=soporte_url)


@app.route("/verify_code/<email>", methods=["GET", "POST"])
def verify_code(email):
    if email not in pending_codes:
        return redirect(url_for("register"))
    mensaje = None
    if request.method == "POST":
        codigo_ingresado = request.form["codigo"]
        if pending_codes[email]["codigo"] == codigo_ingresado:
            usuarios = cargar_usuarios()
            usuario = pending_codes[email].get("usuario", email)
            usuarios[email] = {
                "contraseña_hash":
                generate_password_hash(pending_codes[email]["password"]),
                "email":
                email,
                "usuario":
                usuario,
                "created_at":
                datetime.now().isoformat()
            }
            guardar_usuarios(usuarios)
            del pending_codes[email]
            return render_template("registro_exitoso.html", email=email)
        else:
            mensaje = "Código incorrecto"
    if "mensaje" in request.args:
        mensaje = request.args["mensaje"]
    return render_template("verify_code.html", email=email, mensaje=mensaje)


@app.route("/resend_code/<email>", methods=["POST"])
def resend_code(email):
    email = email.strip().lower()
    if email not in pending_codes:
        return redirect(url_for("register"))
    codigo = ''.join(random.choices(string.digits, k=6))
    pending_codes[email]["codigo"] = codigo
    pending_codes[email]["timestamp"] = datetime.now()
    enviar_codigo_correo(email, codigo)
    return redirect(
        url_for("verify_code",
                email=email,
                mensaje="¡Nuevo código enviado a tu correo!"))


@app.route("/logout")
def logout():
    email = session.get("email")
    session.clear()
    resp = make_response(redirect(url_for("login")))
    resp.delete_cookie("recordarme")
    if email:
        quitar_token_recordarme(email)
    return resp


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    error = None
    mensaje = None
    email = ""
    paso = 1

    if request.method == "POST":
        if "codigo" not in request.form:
            email = request.form["email"].strip().lower()
            usuarios = cargar_usuarios()
            if email not in usuarios:
                error = "No existe una cuenta con ese correo."
            else:
                codigo = ''.join(random.choices(string.digits, k=6))
                reset_codes[email] = {
                    "codigo": codigo,
                    "timestamp": datetime.now()
                }
                enviar_codigo_correo(email, codigo)
                mensaje = "Te enviamos un código a tu correo."
                paso = 2
        else:
            email = request.form["email"].strip().lower()
            codigo = request.form["codigo"]
            nueva = request.form["password"]
            repetir = request.form["repeat_password"]
            if nueva != repetir:
                error = "Las contraseñas no coinciden."
                paso = 2
            else:
                es_segura, faltantes = es_contraseña_segura(nueva)
                if not es_segura:
                    error = "La contraseña debe contener: " + ", ".join(
                        faltantes) + "."
                    paso = 2
                elif email not in reset_codes or reset_codes[email][
                        "codigo"] != codigo:
                    error = "Código incorrecto o expirado."
                    paso = 2
                else:
                    usuarios = cargar_usuarios()
                    if email not in usuarios:
                        error = "No existe una cuenta con ese correo."
                        paso = 1
                    else:
                        usuarios[email][
                            "contraseña_hash"] = generate_password_hash(nueva)
                        guardar_usuarios(usuarios)
                        reset_codes.pop(email, None)
                        mensaje = "Contraseña actualizada correctamente. Ahora puedes iniciar sesión."
                        paso = 1
    elif "email" in request.args:
        email = request.args["email"]
        paso = 2

    return render_template("reset_password.html",
                           paso=paso,
                           email=email,
                           error=error,
                           mensaje=mensaje)


@app.route("/forgot_username", methods=["GET", "POST"])
def forgot_username():
    mensaje = None
    error = None
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        usuarios = cargar_usuarios()
        if email not in usuarios:
            mensaje = "Si el correo está registrado, recibirás un email con tu usuario."
        else:
            usuario = usuarios[email].get("usuario", email)
            try:
                enviar_usuario_correo(email, usuario)
                mensaje = "Si el correo está registrado, recibirás un email con tu usuario."
            except Exception:
                mensaje = "Si el correo está registrado, recibirás un email con tu usuario."
    return render_template("forgot_username.html",
                           mensaje=mensaje,
                           error=error)


@app.errorhandler(500)
def internal_error(error):
    if MAINTENANCE_MODE:
        return "Servicio en mantenimiento", 503
    return "Error interno del servidor", 500


@app.errorhandler(404)
def not_found(error):
    if MAINTENANCE_MODE:
        return "Servicio en mantenimiento", 503
    return "Página no encontrada", 404


active_responses = {}


@app.route("/speech_to_text", methods=["POST"])
def speech_to_text():
    """Endpoint para convertir voz a texto usando Web Speech API del navegador"""
    if not session.get("email"):
        return jsonify({"error": "Sesión no válida"}), 401

    try:
        # La funcionalidad de speech-to-text se maneja completamente en el frontend
        # con Web Speech API. Este endpoint puede usarse para validaciones adicionales.
        data = request.get_json()
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"error": "Texto vacío"}), 400

        return jsonify({
            "success": True,
            "text": text,
            "message": "Texto recibido correctamente"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/text_to_speech", methods=["POST"])
def text_to_speech():
    """Endpoint para preparar texto para síntesis de voz"""
    if not session.get("email"):
        return jsonify({"error": "Sesión no válida"}), 401

    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Texto vacío"}), 400

    try:
        # Limpiar el texto para síntesis de voz
        import re

        # Remover HTML tags
        clean_text = re.sub(r'<[^>]*>', '', text)

        # Remover caracteres especiales pero mantener puntuación básica
        clean_text = re.sub(r'[^\w\s.,;:!?¡¿áéíóúñü]',
                            '',
                            clean_text,
                            flags=re.IGNORECASE)

        # Limitar longitud para evitar textos muy largos
        if len(clean_text) > 500:
            clean_text = clean_text[:500] + "..."

        return jsonify({
            "success": True,
            "message": "Texto preparado para síntesis",
            "clean_text": clean_text.strip(),
            "original_length": len(text),
            "cleaned_length": len(clean_text)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generate_image", methods=["POST"])
def generate_image():
    if not session.get("email"):
        return jsonify({"error": "Sesión no válida"}), 401

    data = request.get_json()
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Prompt vacío"}), 400

    try:
        import requests
        import urllib.parse

        # Limpiar y formatear el prompt para la API
        clean_prompt = prompt.strip()
        if not clean_prompt:
            return jsonify({"error": "Prompt vacío"}), 400

        # URL encode del prompt para la API
        encoded_prompt = urllib.parse.quote(clean_prompt)

        # Usar Pollinations API - genera imágenes reales basadas en el prompt
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&seed={hash(prompt) % 10000}&enhance=true"

        # APIs de respaldo
        backup_apis = [
            # Placeholder con el prompt
            f"https://via.placeholder.com/800x600/6e48aa/ffffff?text={prompt.replace(' ', '+')[:30]}",
            # Lorem Picsum aleatorio
            f"https://picsum.photos/800/600?random={hash(prompt) % 1000}"
        ]

        try:
            # Verificar que Pollinations responde
            response = requests.head(pollinations_url, timeout=10)
            if response.status_code == 200:
                return jsonify({"image_url": pollinations_url})
            else:
                # Si falla, usar backup
                return jsonify({"image_url": backup_apis[0]})
        except:
            # Si hay error de conexión, usar backup
            return jsonify({"image_url": backup_apis[0]})

        return jsonify({"image_url": pollinations_url})

    except Exception as e:
        print(f"Error generando imagen: {e}")
        # URL de respaldo en caso de error total
        fallback_url = f"https://via.placeholder.com/800x600/6e48aa/ffffff?text=Error+generando+imagen"
        return jsonify({"image_url": fallback_url})


@socketio.on("voice_message")
def handle_voice_message(data):
    """Maneja mensajes de voz del usuario"""
    if not session.get("email"):
        emit("voice_response", {"error": "Sesión no válida"})
        return

    try:
        # Simular procesamiento de audio
        # En una implementación real aquí procesarías el audio recibido
        text = data.get("text", "")
        if text:
            emit(
                "voice_response", {
                    "success": True,
                    "text": text,
                    "message": "Audio procesado correctamente"
                })
        else:
            emit("voice_response", {"error": "No se pudo procesar el audio"})
    except Exception as e:
        emit("voice_response", {"error": str(e)})


@socketio.on("send_question")
def handle_send_question(data):
    print("Pregunta recibida:", data)
    if not session.get("email"):
        emit("new_message", {"message": "⚠️ Error: Sesión no válida"})
        return

    if not isinstance(data, dict):
        emit("new_message", {"message": "⚠️ Error: Datos inválidos"})
        return

    pregunta = data.get("pregunta", "").strip()
    chat_id = data.get("chatId", "")
    language = data.get("language", "es")
    is_voice = data.get("isVoice", False)
    has_image = data.get("hasImage", False)
    image_data = data.get("imageData", None)


    if not pregunta and not has_image:
        emit("new_message", {"message": "⚠️ Error: Mensaje vacío"})
        return
    if not chat_id:
        emit("new_message", {"message": "⚠️ Error: ID de chat no válido"})
        return
    
    email = session["email"]
    session_id = request.sid
    active_responses[session_id] = True

    # Notificar que la IA está hablando si es mensaje de voz
    if is_voice:
        emit("voice_status", {"status": "speaking"})

    try:
        print("Consultando Gemini...")
        print(f"Debug - GEMINI_API_KEY: {'Configurada' if GEMINI_API_KEY else 'No configurada'}")
        print(f"Debug - GEMINI_AVAILABLE: {GEMINI_AVAILABLE}")
        print(f"Debug - Has Image: {has_image}")


        if not GEMINI_API_KEY:
            emit("new_message", {
                "message": "⚠️ Error: API Key de Gemini no configurada. Verifica tu archivo .env"
            })
            return

        if not GEMINI_AVAILABLE:
            respuesta_fallback = f"🤖 Hola! Estoy funcionando en modo básico debido a problemas con las dependencias del sistema. Tu pregunta fue: '{pregunta}'. \n\n💡 Para activar mis capacidades completas de IA, las dependencias del sistema se están cargando automáticamente. La aplicación web funciona correctamente para el registro, login y funciones básicas."
            save_message(email, chat_id, pregunta, "user", datetime.now().strftime("%H:%M"))
            save_message(email, chat_id, respuesta_fallback, "ai", datetime.now().strftime("%H:%M"))
            emit("new_message", {"message": respuesta_fallback, "chatId": chat_id})
            return

        # Obtener el historial del chat actual
        historial = get_chat_messages(email, chat_id)

        # Crear contexto con el historial previo
        contexto = ""
        if historial:
            contexto = "\n\nContexto de la conversación previa:\n"
            for msg in historial[-10:]:
                if msg["sender"] == "user":
                    contexto += f"Usuario: {msg['content']}\n"
                elif msg["sender"] == "ai":
                    contexto += f"Asistente: {msg['content']}\n"

        # Detectar si el usuario quiere generar una imagen
        image_keywords = ['haz', 'crea', 'genera', 'dibuja', 'make', 'create', 'generate', 'draw', 'diseña', 'pinta', 'ilustra']
        question_words = ['puedes', 'puede', 'sabes', 'sabe', 'como', 'cómo', 'what', 'how', 'can', 'do']
        exclude_words = ['guion', 'script', 'código', 'programa', 'función', 'clase', 'método', 'algoritmo']
        
        # Solo generar imagen si NO es una pregunta y contiene palabras clave
        is_question = any(q_word in pregunta.lower() for q_word in question_words) or '?' in pregunta
        has_exclude = any(word in pregunta.lower() for word in exclude_words)
        wants_image = any(keyword in pregunta.lower() for keyword in image_keywords) and not has_image and not is_question and not has_exclude
        
        # Búsqueda web si se solicita información actualizada
        web_keywords = ['noticias', 'actualidad', 'hoy', 'ahora', 'reciente', 'nuevo', 'precio', 'cotización', 'clima', 'tiempo', 'qué pasó', 'información', 'busca', 'wikipedia', 'hora', 'fecha', 'cuándo', 'cuando', 'gta', 'videojuego', 'lanzamiento', 'sale']
        needs_web_search = any(keyword in pregunta.lower() for keyword in web_keywords) and not has_image and not wants_image
        
        if needs_web_search:
            try:
                print(f"🌍 ACTIVANDO BÚSQUEDA WEB para: {pregunta}")
                web_info = search_web_info(pregunta)
                if web_info:
                    contexto += f"\n\n🌐 INFORMACIÓN ACTUALIZADA DE INTERNET: {web_info}\n\nUSA ESTA INFORMACIÓN PARA RESPONDER DE FORMA ACTUALIZADA."
                    print(f"✅ Información web encontrada: {web_info[:100]}...")
                else:
                    # Agregar fecha actual como mínimo
                    import datetime as dt
                    fecha_actual = dt.datetime.now().strftime("%d de %B de %Y")
                    contexto += f"\n\n🕐 FECHA ACTUAL: Hoy es {fecha_actual}. Si te preguntan la fecha u hora, usa esta información."
                    print("❌ No se encontró información web, agregando fecha actual")
            except Exception as e:
                print(f"❌ Error en búsqueda web: {e}")
                pass
        
        # Crear prompt unificado para texto e imágenes
        language_prompts = {
            "es": "Eres Alia, un asistente de inteligencia artificial avanzado. Responde SIEMPRE en español, sin importar el idioma de la pregunta. NO te presentes automáticamente a menos que te pregunten quién eres o cuál es tu nombre. Mantén coherencia con la conversación previa.\n\n🔍 CAPACIDADES IMPORTANTES QUE TIENES:\n- Puedes analizar imágenes en detalle (objetos, texto, personas, colores, contexto)\n- Puedes leer y transcribir texto que aparece en imágenes\n- Puedes describir escenas, emociones y contextos visuales\n- Tienes visión artificial con Gemini Vision\n- Puedes ayudar con análisis visual, OCR, y descripción de contenido\n- PUEDES BUSCAR INFORMACIÓN ACTUALIZADA EN INTERNET cuando detectes palabras como: noticias, actualidad, hoy, información reciente, etc.\n- Cuando tengas información de internet, úsala para dar respuestas actualizadas y precisas\n- IMPORTANTE: Si una imagen contiene texto sobre un tema específico (como 'teatro', 'historia', 'ciencia', etc.), debes proporcionar información detallada sobre ese tema, no solo describir la imagen\n- Si el usuario pide investigación sobre algo que aparece en la imagen, proporciona información completa y educativa sobre el tema\n\nSi alguien pregunta sobre análisis de imágenes, confirma que SÍ puedes hacerlo y explica cómo: subiendo una imagen con el botón 📷.",
            "en": "You are Alia, an advanced artificial intelligence assistant. Always respond in English, regardless of the input language. DO NOT introduce yourself automatically unless asked who you are or what your name is. Keep coherence with the previous conversation.\n\n🔍 IMPORTANT CAPABILITIES YOU HAVE:\n- You can analyze images in detail (objects, text, people, colors, context)\n- You can read and transcribe text that appears in images\n- You can describe scenes, emotions and visual contexts\n- You have computer vision with Gemini Vision\n- You can help with visual analysis, OCR, and content description\n- IMPORTANT: If an image contains text about a specific topic (like 'theater', 'history', 'science', etc.), you should provide detailed information about that topic, not just describe the image\n- If the user asks for research about something that appears in the image, provide complete and educational information about the topic\n\nIf someone asks about image analysis, confirm that YES you can do it and explain how: by uploading an image with the 📷 button.",
            "fr": "Tu es Alia, un assistant d'intelligence artificielle avancé. Réponds TOUJOURS en français, peu importe la langue de la question. NE te présente PAS automatiquement sauf si on te demande qui tu es ou quel est ton nom. Maintiens la cohérence avec la conversation précédente.\n\n🔍 CAPACITÉS IMPORTANTES QUE TU AS:\n- Tu peux analyser les images en détail (objets, texte, personnes, couleurs, contexte)\n- Tu peux lire et transcrire le texte qui apparaît dans les images\n- Tu peux décrire des scènes, des émotions et des contextes visuels\n- Tu as la vision artificielle avec Gemini Vision\n- Tu peux aider avec l'analyse visuelle, OCR, et la description de contenu\n- IMPORTANT: Si une image contient du texte sur un sujet spécifique (comme 'théâtre', 'histoire', 'science', etc.), tu dois fournir des informations détaillées sur ce sujet, pas seulement décrire l'image\n- Si l'utilisateur demande des recherches sur quelque chose qui apparaît dans l'image, fournis des informations complètes et éducatives sur le sujet\n\nSi quelqu'un demande l'analyse d'images, confirme que OUI tu peux le faire et explique comment: en téléchargeant une image avec le bouton 📷."
        }

        language_instruction = language_prompts.get(language, language_prompts["es"])

        
        if wants_image:
            # Generar imagen usando API gratuita
            try:
                import urllib.parse
                
                # Obtener contexto de imagen previa si existe
                last_image_context = ""
                if historial:
                    for msg in reversed(historial[-5:]):
                        if msg["sender"] == "user" and any(kw in msg["message"].lower() for kw in image_keywords):
                            last_image_context = msg["message"]
                            break
                
                # Detectar estilos artísticos avanzados
                styles = {
                    'anime': 'anime style, manga art, japanese animation',
                    'realista': 'photorealistic, ultra realistic, high quality photo',
                    'cartoon': 'cartoon style, animated, colorful',
                    'pixel': 'pixel art, 8-bit style, retro gaming',
                    'oleo': 'oil painting, classical art, painterly',
                    'acuarela': 'watercolor painting, soft colors',
                    'sketch': 'pencil sketch, hand drawn, artistic',
                    'cyberpunk': 'cyberpunk style, neon lights, futuristic',
                    'fantasy': 'fantasy art, magical, ethereal',
                    'minimalista': 'minimalist design, clean, simple',
                    'vintage': 'vintage style, retro, old-fashioned',
                    'abstracto': 'abstract art, modern, artistic'
                }
                
                style_suffix = ''
                detected_styles = []
                for style_name, style_prompt in styles.items():
                    if style_name in pregunta.lower():
                        detected_styles.append(style_prompt)
                
                if detected_styles:
                    style_suffix = f', {detected_styles[0]}'
                
                # Limpiar y mejorar prompt
                clean_prompt = pregunta
                for keyword in ['haz', 'crea', 'genera', 'dibuja', 'diseña', 'pinta', 'ilustra', 'una imagen de', 'una foto de']:
                    clean_prompt = clean_prompt.replace(keyword, '').strip()
                
                # Detectar variaciones
                if any(word in pregunta.lower() for word in ['otra', 'otro', 'similar', 'parecida', 'diferente']) and last_image_context:
                    base_context = last_image_context.replace('haz', '').replace('crea', '').replace('genera', '').strip()
                    if 'diferente' in pregunta.lower():
                        clean_prompt = f"{base_context}, different style, alternative version"
                    else:
                        clean_prompt = f"{base_context}, variation, similar theme"
                
                # Mejorar calidad del prompt
                quality_enhancers = ', high quality, detailed, professional'
                if 'realista' in pregunta.lower() or 'foto' in pregunta.lower():
                    quality_enhancers = ', 4K, ultra realistic, professional photography'
                elif 'arte' in pregunta.lower() or 'artístico' in pregunta.lower():
                    quality_enhancers = ', artistic masterpiece, detailed, beautiful'
                
                clean_prompt = f"{clean_prompt}{style_suffix}{quality_enhancers}".strip()
                
                # Fallback si está vacío
                if not clean_prompt or len(clean_prompt) < 5:
                    clean_prompt = "creative artistic image, high quality, detailed"
                
                # Mostrar mensaje de carga inmediatamente
                loading_message = f"🎨 Creando imagen: '{clean_prompt}'...\n\n<div style='text-align: center; padding: 20px; background: #f0f0f0; border-radius: 12px; margin: 10px 0;'><div style='display: inline-block; width: 40px; height: 40px; border: 4px solid #ddd; border-top: 4px solid #7c4dff; border-radius: 50%; animation: spin 1s linear infinite;'></div><br><br>🔄 Generando imagen, por favor espera...</div>\n\n<style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>"
                
                save_message(email, chat_id, pregunta, "user", datetime.now().strftime("%H:%M"))
                save_message(email, chat_id, loading_message, "ai", datetime.now().strftime("%H:%M"))
                emit("new_message", {"message": loading_message, "chatId": chat_id})
                
                # Detectar dimensiones preferidas
                width, height = 1024, 1024  # Cuadrado por defecto
                if any(word in pregunta.lower() for word in ['horizontal', 'paisaje', 'ancho']):
                    width, height = 1344, 768
                elif any(word in pregunta.lower() for word in ['vertical', 'retrato', 'alto']):
                    width, height = 768, 1344
                elif any(word in pregunta.lower() for word in ['banner', 'portada']):
                    width, height = 1920, 1080
                
                # Generar imagen con parámetros mejorados
                encoded_prompt = urllib.parse.quote(clean_prompt)
                seed = hash(clean_prompt + str(datetime.now())) % 100000
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&enhance=true&model=flux"
                
                # Esperar un momento y enviar imagen final
                import time
                time.sleep(2)
                
                # Crear mensaje final mejorado
                style_info = detected_styles[0] if detected_styles else "estilo personalizado"
                dimension_info = f"{width}x{height}"
                
                final_message = f"🎨 **Imagen generada**: *{clean_prompt[:50]}{'...' if len(clean_prompt) > 50 else ''}*\n\n<div style='position: relative; display: inline-block; max-width: 100%;'><img src='{image_url}' alt='{clean_prompt}' style='max-width: 100%; border-radius: 12px; margin: 10px 0; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: transform 0.2s;' onclick='openImageModal(\"{image_url}\", \"{clean_prompt}\")' onmouseover='this.style.transform=\"scale(1.02)\"' onmouseout='this.style.transform=\"scale(1)\"' /><div style='position: absolute; top: 15px; right: 15px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;'>{dimension_info}</div></div>\n\n<div style='text-align: center; margin: 15px 0; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;'><button onclick='downloadImage(\"{image_url}\", \"{clean_prompt}\")' style='background: linear-gradient(45deg, #4caf50, #45a049); color: white; border: none; padding: 10px 20px; border-radius: 25px; cursor: pointer; font-size: 14px; box-shadow: 0 4px 12px rgba(76,175,80,0.3); transition: all 0.3s;' onmouseover='this.style.transform=\"translateY(-2px)\"' onmouseout='this.style.transform=\"translateY(0)\"'>💾 Descargar</button><button onclick='shareImage(\"{image_url}\")' style='background: linear-gradient(45deg, #2196f3, #1976d2); color: white; border: none; padding: 10px 20px; border-radius: 25px; cursor: pointer; font-size: 14px; box-shadow: 0 4px 12px rgba(33,150,243,0.3); transition: all 0.3s;' onmouseover='this.style.transform=\"translateY(-2px)\"' onmouseout='this.style.transform=\"translateY(0)\"'>🔗 Compartir</button><button onclick='regenerateImage(\"{clean_prompt}\")' style='background: linear-gradient(45deg, #ff9800, #f57c00); color: white; border: none; padding: 10px 20px; border-radius: 25px; cursor: pointer; font-size: 14px; box-shadow: 0 4px 12px rgba(255,152,0,0.3); transition: all 0.3s;' onmouseover='this.style.transform=\"translateY(-2px)\"' onmouseout='this.style.transform=\"translateY(0)\"'>🔄 Regenerar</button></div>\n\n**Detalles**: {style_info} • {dimension_info}\n\n💡 **Prueba**: \"otra similar\", \"diferente estilo\", \"más realista\", \"estilo anime\", \"horizontal\", \"vertical\""
                
                # Guardar imagen en galería del usuario con metadatos
                save_image_to_gallery(email, image_url, clean_prompt)
                
                # Guardar contexto para próximas generaciones
                last_image_context = clean_prompt
                
                save_message(email, chat_id, final_message, "ai", datetime.now().strftime("%H:%M"))
                emit("new_message", {"message": final_message, "chatId": chat_id, "replaceLastAI": True})
                return
            except Exception as e:
                print(f"Error generando imagen: {e}")
                # Continuar con respuesta normal si falla
        
        # Construir prompt según si hay imagen o no
        if has_image:
            if pregunta:
                full_prompt = f"{language_instruction}{contexto}\n\nEl usuario ha enviado una imagen junto con este mensaje: {pregunta}\n\nAnaliza la imagen y responde considerando tanto la imagen como el mensaje del usuario."
            else:
                full_prompt = f"{language_instruction}{contexto}\n\nEl usuario ha enviado una imagen para análisis. Analiza detalladamente la imagen, describe lo que ves, y si hay texto visible, transcríbelo exactamente."
        else:
            full_prompt = f"{language_instruction}{contexto}\n\nPregunta actual del usuario: {pregunta}"

        # Usar el modelo unificado
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Preparar contenido para enviar
        content_to_send = [full_prompt]
        
        # Si hay imagen, agregarla al contenido
        if has_image and image_data:
            try:
                from PIL import Image
                import io
                import base64
                
                # Decodificar imagen base64
                image_bytes = base64.b64decode(image_data.split(',')[1])
                image = Image.open(io.BytesIO(image_bytes))
                
                # Optimizar imagen
                max_size = (1024, 1024)
                if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(
                        image,
                        mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                
                content_to_send.append(image)
                print("✅ Imagen agregada al contenido")
            except Exception as e:
                print(f"❌ Error procesando imagen: {e}")
                emit("new_message", {"message": f"❌ Error procesando imagen: {str(e)}"})
                return
        
        # Generar respuesta
        response = model.generate_content(content_to_send)
        
        if session_id not in active_responses:
            print("Respuesta cancelada por el usuario")
            return
            
        print("Respuesta Gemini:", response.text)
        respuesta_formateada = response.text
        
        # Guardar en historial
        user_message = pregunta if pregunta else "🖼️ Imagen enviada para análisis"
        save_message(email, chat_id, user_message, "user", datetime.now().strftime("%H:%M"))
        save_message(email, chat_id, respuesta_formateada, "ai", datetime.now().strftime("%H:%M"))
        
        # Notificar al frontend que se actualice el historial
        emit("chat_updated", {"chatId": chat_id})

        # Preparar respuesta
        response_data = {"message": respuesta_formateada, "chatId": chat_id}
        if is_voice:
            response_data["isVoiceResponse"] = True
            response_data["voiceText"] = respuesta_formateada

        emit("new_message", response_data)

    except Exception as e:
        error_msg = f"⚠️ Error generando respuesta: {str(e)}"
        print(error_msg)
        emit("new_message", {"message": error_msg})
    finally:
        active_responses.pop(session_id, None)
        if is_voice:
            emit("voice_status", {"status": "finished"})


@socketio.on("stop_response")
def handle_stop_response():
    session_id = request.sid
    if session_id in active_responses:
        del active_responses[session_id]
        print(f"Respuesta detenida para sesión: {session_id}")
        emit("response_stopped", {"status": "stopped"})


@socketio.on("save_welcome_message")
def handle_save_welcome_message(data):
    if not session.get("email"):
        return
    
    email = session["email"]
    chat_id = data.get("chatId")
    message = data.get("message")
    
    if chat_id and message:
        save_message(email, chat_id, message, "ai", datetime.now().strftime("%H:%M"))

@socketio.on("disconnect")
def handle_disconnect():
    session_id = request.sid
    active_responses.pop(session_id, None)
    print(f"Cliente desconectado: {session_id}")


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/get_chats')
def get_chats():
    if 'email' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    email = session['email']
    chats = get_user_chats(email)
    return jsonify({'chats': chats})

@app.route('/get_chat_messages/<chat_id>')
def get_chat_messages_route(chat_id):
    if 'email' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    email = session['email']
    messages = get_chat_messages(email, chat_id)
    return jsonify({'messages': messages})

@app.route('/delete_chat/<chat_id>', methods=['DELETE'])
def delete_chat_route(chat_id):
    if 'email' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    email = session['email']
    success = delete_chat(email, chat_id)
    return jsonify({'success': success})

def get_user_chats(email):
    try:
        # Crear tabla si no existe
        conn = sqlite3.connect('alia_chat.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                message TEXT NOT NULL,
                sender TEXT NOT NULL,
                time TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        
        cursor.execute("""
            SELECT chat_id, MIN(timestamp) as first_message, 
                   COUNT(*) as message_count,
                   (SELECT message FROM messages m2 
                    WHERE m2.email = ? AND m2.chat_id = m1.chat_id 
                    AND m2.sender = 'user' ORDER BY m2.timestamp LIMIT 1) as first_user_message
            FROM messages m1 
            WHERE email = ? 
            GROUP BY chat_id 
            ORDER BY first_message DESC
        """, (email, email))
        
        print(f"🔍 Buscando chats para: {email}")
        
        chats = []
        rows = cursor.fetchall()
        print(f"📊 Encontradas {len(rows)} filas en BD")
        
        for row in rows:
            chat_id, first_message, message_count, first_user_msg = row
            title = (first_user_msg or "Nuevo chat")[:30]
            chat_data = {
                'id': chat_id,
                'title': title,
                'timestamp': first_message,
                'message_count': message_count
            }
            chats.append(chat_data)
            print(f"✅ Chat agregado: {title} (ID: {chat_id})")
        
        conn.close()
        print(f"📤 Retornando {len(chats)} chats")
        return chats
    except Exception as e:
        print(f"Error getting chats: {e}")
        return []

def get_chat_messages(email, chat_id):
    try:
        conn = sqlite3.connect('alia_chat.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                message TEXT NOT NULL,
                sender TEXT NOT NULL,
                time TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        
        cursor.execute("""
            SELECT message, sender, time FROM messages 
            WHERE email = ? AND chat_id = ? 
            ORDER BY timestamp ASC
        """, (email, chat_id))
        
        messages = []
        for row in cursor.fetchall():
            message, sender, time = row
            messages.append({
                'content': message,
                'sender': sender,
                'time': time
            })
        
        conn.close()
        return messages
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []

def delete_chat(email, chat_id):
    try:
        conn = sqlite3.connect('alia_chat.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                message TEXT NOT NULL,
                sender TEXT NOT NULL,
                time TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        
        cursor.execute("DELETE FROM messages WHERE email = ? AND chat_id = ?", (email, chat_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting chat: {e}")
        return False

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3000))
    print(f"🚀 Iniciando servidor en http://0.0.0.0:{PORT}")
    print(f"🌐 Accede a tu aplicación desde la URL que aparece arriba")
    print(
        f"📝 Nota: Google Generative AI puede tener problemas, pero la interfaz web funcionará"
    )
    print(f"🔗 URL local: http://0.0.0.0:{PORT}")
    socketio.run(app, host="0.0.0.0", port=PORT, debug=False)
