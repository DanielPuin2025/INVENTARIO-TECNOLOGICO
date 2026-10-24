# Sistema de Inventario Tecnológico

Aplicación web en Flask para gestionar el inventario tecnológico de un colegio. Permite iniciar sesión, registrar usuarios, consultar equipos y asignarlos a encargados y salones.

## Requisitos

- Windows con XAMPP.
- Python 3.
- MySQL iniciado desde el panel de XAMPP.

## Estructura

```text
codigo/
├── README.md
├── MANUAL_DE_USUARIO.md
├── app.py
├── run.py
├── iniciar.bat
├── index.html
├── requirements.txt
├── .env.example
├── backend/
│   ├── app.py
│   ├── db.py
│   ├── database/
│   │   └── crear_base_datos.sql
│   ├── templates/
│   │   ├── login.html
│   │   └── panel.html
│   ├── static/
│   ├── imagenes/
│   └── uploads/
├── archive/
└── .vscode/
```

Las páginas activas están en `backend/templates`. Las copias antiguas se
conservan en `archive/legacy-ui` y `archive/legacy-database`. No publiques
archivos `.env`, bases de datos locales, exportaciones con datos personales,
fotografías cargadas ni entornos virtuales.

## Instalacion

1. Abre una terminal en la carpeta raíz del proyecto:

   ```powershell
   cd C:\xampp\htdocs\codigo
   ```

   > **Nota sobre tu ruta:** Puedes verificar en qué carpeta estás con `pwd`. Si tu terminal ya dice `C:\xampp\htdocs\codigo\backend`, puedes volver a la raíz con:
   > ```powershell
   > cd ..
   > ```
   > O ir directamente a la raíz con:
   > ```powershell
   > cd C:\xampp\htdocs\codigo
   > ```

2. Crea y activa el entorno virtual del proyecto:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instala las dependencias:

   ```powershell
   python -m pip install -r requirements.txt
   ```

## Configuracion

1. Inicia **MySQL** desde XAMPP.
2. En phpMyAdmin, importa `backend/database/crear_base_datos.sql` o ejecuta su
   instrucción para crear la base `inventario`. La aplicación crea las tablas y
   actualiza las columnas que necesita al arrancar.
3. Si todavía no existe, copia `.env.example` como `.env` y genera una clave
   secreta con:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Pega el resultado en `INVENTARIO_SECRET_KEY` dentro de `.env`. Configura
   también allí el usuario, la contraseña y el puerto de MySQL. No publiques ni
   compartas los archivos `.env`.

Las fotografías heredadas que todavía estén en `backend/uploads` se migran a
MySQL al iniciar. `backend/database/inventario.sql` es una copia local que puede
contener datos personales; no es el script de instalación ni debe publicarse.

## Ejecutar la aplicacion

Desde la raíz del proyecto (`C:\xampp\htdocs\codigo`), inicia MySQL en XAMPP
y ejecuta:

```powershell
.\.venv\Scripts\python.exe app.py
```

También puedes hacer doble clic en `iniciar.bat`. El comando `python run.py` se
conserva como alias compatible. Usa siempre el Python del entorno `.venv`.

Después abre en el navegador:

- **En este equipo:** `http://localhost:5000`
- **Desde otros dispositivos:** `http://<IP-del-servidor>:5000`. Obtén la IPv4
  del equipo servidor con `ipconfig` y permite el puerto 5000 en la red local.

### Crear el primer administrador

Configura los siguientes valores en `.env` antes de iniciar por primera vez:

```powershell
INVENTARIO_ADMIN_EMAIL=admin@colegio.local
INVENTARIO_ADMIN_PASSWORD=usa-una-clave-segura-de-al-menos-12-caracteres
INVENTARIO_ADMIN_NAME=Administrador
INVENTARIO_ADMIN_LASTNAME=Principal
```

El administrador solo se crea si todavía no existe uno. La contraseña debe
tener al menos 12 caracteres. Después inicia sesión con ese correo y contraseña;
aparecerá el botón **Actividad** para consultar los movimientos.

La pagina de inicio de sesion esta en `backend/templates/login.html` y Flask la sirve automaticamente desde la ruta principal.

## Funcionalidades

- Registro público de cuentas únicamente como `encargado`.
- Inicio y cierre de sesion.
- Control de acceso para administradores y encargados.
- Perfiles de consulta de rector y coordinador, sin permisos de edición.
- Registro y consulta de equipos.
- Asignacion de equipos a encargados y salones.
- Notificaciones por correo al reportar equipos dañados. El administrador configura
  los destinatarios desde **Correo de alertas** en el panel.
- Almacenamiento de contraseñas mediante hash.

### Notificaciones por correo

Desde el panel, un administrador puede agregar, editar o eliminar destinatarios y
enviarles un correo de prueba. Los encargados y administradores pueden abrir un
equipo y usar **Reportar daño y notificar** para marcarlo como dañado, describir la
falla y enviar el reporte inmediatamente a toda la lista. También se notifica al
registrar o editar un equipo con estado **Dañado**.

Para que los mensajes se envíen realmente, configura estas variables en el archivo
`.env` del servidor:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=cuenta-remitente@gmail.com
SMTP_PASSWORD=contraseña-de-aplicación
SMTP_FROM=cuenta-remitente@gmail.com
```

Con Gmail, `SMTP_PASSWORD` debe ser una contraseña de aplicación y no la contraseña
habitual de la cuenta. Los destinatarios se pueden cambiar desde el panel; los
datos SMTP pertenecen a la cuenta que envía los mensajes. La opción de correo de
prueba permite verificar la entrega antes de usar los reportes.

El administrador puede crear usuarios con los perfiles `encargado`,
`rector` y `coordinador` desde el botón **Registrar usuario**. Rector y
coordinador solo consultan el inventario, sus fotos, estados, responsables y
el número de salas o áreas; no pueden registrar, editar, asignar ni eliminar.

## Nota de seguridad

Las operaciones de edición, eliminación, reasignación y aprobación requieren
un administrador. Antes de usar la aplicación fuera de un entorno local,
configura HTTPS, `INVENTARIO_COOKIE_SECURE=1`, una cuenta MySQL limitada y un
servidor WSGI como Waitress detrás de un proxy.
