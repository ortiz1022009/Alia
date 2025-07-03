# 🚀 Sistema de Registro - Alia IA (con verificación de correo)

Este sistema permite a los usuarios registrarse para acceso anticipado a la aplicación Alia IA, confirmando su correo electrónico mediante un código enviado por email.

## 📋 Características

- ✅ Registro de usuarios con email y nombre opcional
- ✅ Verificación de correo electrónico (código por email)
- ✅ Validación de emails
- ✅ Base de datos SQLite para almacenar registros
- ✅ Panel de administración para ver registros y estado de verificación
- ✅ Formulario de contacto funcional
- ✅ Interfaz moderna y responsive
- ✅ Mensajes de confirmación y error
- ✅ Animaciones y efectos visuales

## 🛠️ Instalación y configuración

### Inicio rápido

**Windows:**
```bash
iniciar_servidor.bat
```

**Linux/Mac:**
```bash
chmod +x iniciar_servidor.sh
./iniciar_servidor.sh
```

### Instalación manual

1. **Instalar dependencias:**
```bash
pip install -r requirements_registro.txt
```

2. **Configurar SMTP:**
- Abre `registro_backend.py` y edita:
  - `SMTP_USER = 'TU_CORREO@gmail.com'`
  - `SMTP_PASS = 'TU_CONTRASEÑA_DE_APP'`
- Si usas Gmail, crea una contraseña de aplicación en tu cuenta Google.
- Puedes usar cualquier servidor SMTP (Gmail, Outlook, Zoho, etc.).

3. **Ejecutar el servidor:**
```bash
python registro_backend.py
```

El servidor se iniciará en `http://localhost:5000`

## 📁 Estructura de archivos

```
Pagina oficial/
├── registro_backend.py          # Servidor Flask
├── requirements_registro.txt    # Dependencias Python
├── registros_alia.db           # Base de datos (se crea automáticamente)
├── iniciar_servidor.bat        # Script de inicio para Windows
├── iniciar_servidor.sh         # Script de inicio para Linux/Mac
├── index.html                  # Página web principal
├── estilos.css                 # Estilos CSS
├── logo_alia.png               # Logo de la aplicación
├── screenshot1.png             # Capturas de pantalla
├── screenshot2.png
├── screenshot3.png
├── screenshot4.png
└── README_REGISTRO.md          # Este archivo
```

## 🔗 Endpoints disponibles

### Registro de usuarios
- **URL**: `POST /api/registro`
- **Body**: 
  ```json
  {
    "email": "usuario@ejemplo.com",
    "nombre": "Nombre del usuario" // opcional
  }
  ```
- **Respuesta**: Se envía un código de verificación al correo.

### Verificar código
- **URL**: `POST /api/verificar`
- **Body**:
  ```json
  {
    "email": "usuario@ejemplo.com",
    "codigo": "123456"
  }
  ```
- **Respuesta**: Marca el correo como verificado si el código es correcto.

### Reenviar código
- **URL**: `POST /api/reenviar`
- **Body**:
  ```json
  {
    "email": "usuario@ejemplo.com"
  }
  ```
- **Respuesta**: Envía un nuevo código al correo.

### Formulario de contacto
- **URL**: `POST /api/contacto`
- **Body**:
  ```json
  {
    "email": "usuario@ejemplo.com",
    "nombre": "Nombre del usuario",
    "mensaje": "Mensaje de contacto"
  }
  ```

### Panel de administración
- **URL**: `GET /admin/registros`
- **Descripción**: Muestra todos los registros y su estado de verificación

## 🎨 Personalización

### Cambiar la URL del backend

En `index.html`, línea donde dice:
```javascript
const BACKEND_URL = 'https://TU-BACKEND.com';
```

Cambia la URL por la de tu servidor Flask.

### Modificar estilos

Los estilos están en `estilos.css`. Puedes personalizar:
- Colores del tema
- Animaciones
- Responsive design
- Mensajes de éxito/error

## 📊 Base de datos

La base de datos `registros_alia.db` contiene:

### Tabla `registros`
- `id`: ID único del registro
- `email`: Email del usuario (único)
- `nombre`: Nombre del usuario (opcional)
- `fecha_registro`: Fecha y hora del registro
- `ip_address`: IP del usuario
- `user_agent`: Navegador del usuario
- `estado`: Estado del registro (pendiente/verificado)
- `codigo_verificacion`: Código enviado por email
- `codigo_expira`: Fecha/hora de expiración del código
- `verificado`: 1 si el correo está verificado, 0 si no

### Tabla `contactos`
- `id`: ID único del contacto
- `email`: Email del usuario
- `nombre`: Nombre del usuario
- `mensaje`: Mensaje de contacto
- `fecha_envio`: Fecha y hora del envío
- `ip_address`: IP del usuario
- `estado`: Estado del mensaje (nuevo por defecto)

## 🔒 Seguridad

- Validación de formato de email
- Prevención de registros duplicados
- Sanitización de datos de entrada
- CORS habilitado para desarrollo
- Código de verificación expira en 30 minutos

## 🚀 Despliegue

### Para producción:

1. **Configura SMTP seguro**
2. **Usa un servidor WSGI** como Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 registro_backend:app
   ```
3. **Configura un proxy reverso** (nginx/apache)
4. **Actualiza la URL del backend** en el frontend

## 📱 Uso

1. Abre `index.html` en tu navegador (puedes subirlo a GitHub Pages)
2. Navega a la sección "Registro"
3. Completa el formulario con tu email y nombre (opcional)
4. Haz clic en "Registrarse"
5. Ingresa el código recibido por email
6. ¡Listo! Tu correo estará verificado para acceso anticipado

## 🛠️ Mantenimiento

### Ver registros:
- Accede a `http://localhost:5000/admin/registros`

### Backup de base de datos:
```bash
cp registros_alia.db backup_registros_$(date +%Y%m%d).db
```

### Limpiar registros antiguos:
```sql
DELETE FROM registros WHERE fecha_registro < date('now', '-30 days');
```

## 🐛 Solución de problemas

### Error de conexión
- Verifica que el servidor esté ejecutándose
- Comprueba que el puerto 5000 esté disponible
- Revisa la URL del backend en el frontend

### Error de CORS
- El servidor ya tiene CORS habilitado
- Si persiste, verifica la configuración del navegador

### Base de datos corrupta
- Elimina `registros_alia.db`
- Reinicia el servidor (se creará automáticamente)

## 📞 Soporte

Para dudas o problemas, revisa:
1. Los logs del servidor en la consola
2. La consola del navegador (F12)
3. La base de datos SQLite

---

**Alia IA** - Inteligencia Artificial Móvil 🚀 