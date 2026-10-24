# Sistema de Inventario Tecnológico

Sistema web para gestión de inventario tecnológico escolar con Flask, MySQL y notificaciones por correo.

## 🚀 Deployment en Easypanel

### Prerrequisitos
- Easypanel instalado y configurado
- Acceso al servidor en http://144.126.156.160:3000
- Dominio configurado: inventariocusiana.programasena.online

### Variables de Entorno Requeridas

```env
# Seguridad
INVENTARIO_SECRET_KEY=tu_clave_secreta_muy_segura_aqui

# Base de Datos
INVENTARIO_DB_HOST=db
INVENTARIO_DB_PORT=3306
INVENTARIO_DB_NAME=inventario
INVENTARIO_DB_USER=inventario_user
INVENTARIO_DB_PASSWORD=tu_password_seguro

# Administrador Inicial
INVENTARIO_ADMIN_EMAIL=admin@colegio.edu.co
INVENTARIO_ADMIN_PASSWORD=contraseña_minimo_12_caracteres
INVENTARIO_ADMIN_NAME=Administrador
INVENTARIO_ADMIN_LASTNAME=Principal

# SMTP (Opcional - para notificaciones de equipos dañados)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_app_password
SMTP_FROM=tu_correo@gmail.com

# Producción
INVENTARIO_COOKIE_SECURE=1
```

### Pasos de Deployment

1. **Crear servicio en Easypanel**
   - Ir a http://144.126.156.160:3000/projects/sustentaciones2026
   - Crear nuevo servicio tipo "App"
   - Seleccionar "GitHub" como fuente
   - Conectar repositorio: https://github.com/DanielPuin2025/INVENTARIO-TECNOLOGICO

2. **Configurar Build**
   - Build Method: Docker
   - Dockerfile path: `./Dockerfile`
   - Context: `.`

3. **Configurar Variables de Entorno**
   - Agregar todas las variables del archivo `.env.example`
   - **IMPORTANTE**: Usar contraseñas seguras en producción

4. **Configurar Dominio**
   - Agregar dominio: `inventariocusiana.programasena.online`
   - Configurar SSL automático

5. **Deploy**
   - Hacer click en "Deploy"
   - Esperar a que la aplicación esté corriendo
   - Acceder en: https://inventariocusiana.programasena.online

## 🏗️ Arquitectura

- **Backend**: Flask (Python) + Waitress WSGI Server
- **Base de Datos**: MySQL 8.0
- **Frontend**: HTML/CSS/JavaScript vanilla
- **Containerización**: Docker + Docker Compose

## 📦 Estructura del Proyecto

```
.
├── app.py                 # Punto de entrada principal
├── backend/
│   ├── app.py            # Aplicación Flask
│   ├── db.py             # Conexión y modelos de BD
│   ├── templates/        # Plantillas HTML
│   ├── static/           # Archivos estáticos
│   ├── uploads/          # Fotos de equipos
│   └── imagenes/         # Imágenes procesadas
├── Dockerfile            # Imagen Docker
├── docker-compose.yml    # Orquestación de servicios
├── requirements.txt      # Dependencias Python
└── .env.example          # Ejemplo de configuración

```

## 🔧 Desarrollo Local

```bash
# Clonar repositorio
git clone https://github.com/DanielPuin2025/INVENTARIO-TECNOLOGICO.git
cd INVENTARIO-TECNOLOGICO

# Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Iniciar con Docker Compose
docker-compose up -d

# La aplicación estará en http://localhost:5000
```

## 🔐 Seguridad

- Autenticación por correo y contraseña
- Hash de contraseñas con Werkzeug
- Sesiones seguras con cookies HttpOnly
- Validación de archivos subidos
- Protección CSRF
- Headers de seguridad configurados

## 📧 Notificaciones

El sistema envía alertas automáticas por correo cuando:
- Se registra un equipo dañado
- Se modifica el estado de un equipo a dañado
- Se reporta un daño desde el panel

## 👥 Roles de Usuario

- **Administrador**: Control total del sistema
- **Encargado**: Gestión de equipos y asignaciones
- **Rector/Coordinador**: Visualización y reportes

## 📄 Licencia

Desarrollado para instituciones educativas.

---

**Desarrollado por**: Daniel Puin  
**Año**: 2026
