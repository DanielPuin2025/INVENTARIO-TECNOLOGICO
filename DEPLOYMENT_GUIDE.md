# 🚀 GUÍA DE DEPLOYMENT EN EASYPANEL

## ✅ COMPLETADO
- ✓ Código revisado y optimizado
- ✓ Dockerfile creado
- ✓ docker-compose.yml configurado
- ✓ Repositorio Git inicializado
- ✓ Código subido a GitHub: https://github.com/DanielPuin2025/INVENTARIO-TECNOLOGICO

## 📋 PRÓXIMOS PASOS EN EASYPANEL

### 1. Acceder a Easypanel
```
URL: http://144.126.156.160:3000/projects/sustentaciones2026
```

### 2. Crear Nuevo Servicio

#### OPCIÓN A: Service con GitHub (Recomendado)
1. Click en "New Service" o "Add Service"
2. Seleccionar "GitHub" como fuente
3. Conectar repositorio: `DanielPuin2025/INVENTARIO-TECNOLOGICO`
4. Branch: `main`
5. Build method: **Dockerfile**
6. Dockerfile path: `Dockerfile`

#### OPCIÓN B: Docker Compose
1. Click en "New Service"
2. Seleccionar "Docker Compose"
3. Copiar el contenido del archivo `docker-compose.yml`
4. Pegar en el editor de Easypanel

### 3. Configurar Variables de Entorno ⚠️ IMPORTANTE

```env
# SEGURIDAD (OBLIGATORIO)
INVENTARIO_SECRET_KEY=tu_clave_secreta_muy_larga_y_segura_aqui_minimo_32_caracteres

# BASE DE DATOS
INVENTARIO_DB_HOST=db
INVENTARIO_DB_PORT=3306
INVENTARIO_DB_NAME=inventario
INVENTARIO_DB_USER=inventario_user
INVENTARIO_DB_PASSWORD=TuPasswordMuySeguroAqui123!

# ADMINISTRADOR INICIAL (OBLIGATORIO)
INVENTARIO_ADMIN_EMAIL=admin@colegio.edu.co
INVENTARIO_ADMIN_PASSWORD=PasswordSeguro123456!
INVENTARIO_ADMIN_NAME=Administrador
INVENTARIO_ADMIN_LASTNAME=Principal

# PRODUCCIÓN
INVENTARIO_COOKIE_SECURE=1

# SMTP (OPCIONAL - para notificaciones)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_app_password_de_gmail
SMTP_FROM=tu_correo@gmail.com
```

### 4. Configurar Puerto
- **Puerto interno**: 5000
- **Puerto externo**: 80 o el que asigne Easypanel

### 5. Configurar Dominio
1. En la configuración del servicio, ir a "Domains"
2. Agregar dominio: `inventariocusiana.programasena.online`
3. Easypanel configurará automáticamente:
   - Proxy reverso
   - Certificado SSL (Let's Encrypt)
   - Redirección HTTP → HTTPS

### 6. Deploy
1. Click en "Deploy" o "Build & Deploy"
2. Esperar a que se construya la imagen (2-5 minutos)
3. Verificar logs para confirmar que inició correctamente

### 7. Verificar Deployment
```bash
# Debería mostrar:
# "Serving on http://0.0.0.0:5000"
```

Acceder a: `https://inventariocusiana.programasena.online`

---

## 🔧 CONFIGURACIÓN DE BASE DE DATOS

Easypanel creará automáticamente:
- Contenedor MySQL 8.0
- Base de datos `inventario`
- Usuario configurado
- Volumen persistente para los datos

La primera vez que inicie, el sistema:
1. Creará todas las tablas automáticamente
2. Creará el usuario administrador inicial
3. Cargará las salas predefinidas

---

## 📊 MONITOREO

### Logs en Easypanel
1. Ir al servicio
2. Click en "Logs"
3. Ver logs en tiempo real

### Verificar Estado
```bash
# Debe mostrar "healthy" en el servicio de base de datos
# Debe mostrar "running" en el servicio de la app
```

---

## 🆘 TROUBLESHOOTING

### Error: "No se puede conectar a la base de datos"
- Verificar que el servicio `db` esté corriendo
- Verificar las variables de entorno de conexión
- Esperar unos segundos más (healthcheck de MySQL)

### Error: "INVENTARIO_SECRET_KEY no configurada"
- Agregar variable de entorno `INVENTARIO_SECRET_KEY`
- Debe ser una cadena larga y aleatoria

### Error 502 Bad Gateway
- Verificar que el puerto 5000 esté expuesto
- Verificar logs de la aplicación
- Reiniciar el servicio

### No puedo iniciar sesión
- Verificar que las variables `INVENTARIO_ADMIN_*` estén configuradas
- El email debe tener mínimo 12 caracteres en la contraseña
- Revisar logs de la aplicación

---

## 🔐 SEGURIDAD EN PRODUCCIÓN

✅ Configurado:
- Sesiones seguras con cookies HttpOnly
- Headers de seguridad (X-Frame-Options, X-Content-Type-Options)
- Validación de origen para peticiones
- Hash de contraseñas con Werkzeug
- Validación de archivos subidos

⚠️ Recomendaciones adicionales:
1. Usar contraseñas fuertes (20+ caracteres)
2. Cambiar contraseñas por defecto
3. Configurar backups automáticos de la base de datos
4. Revisar logs regularmente
5. Mantener actualizado el sistema

---

## 📞 SOPORTE

Si tienes problemas durante el deployment:
1. Revisar logs en Easypanel
2. Verificar todas las variables de entorno
3. Confirmar que GitHub tiene el código actualizado
4. Reiniciar servicios si es necesario

---

**¡TODO LISTO PARA DEPLOYMENT! 🎉**

El código está optimizado, dockerizado y listo para producción.
