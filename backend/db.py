import mysql.connector
import os

def obtener_conexion():
    return mysql.connector.connect(
        host=os.environ.get("INVENTARIO_DB_HOST", "localhost"),
        user=os.environ.get("INVENTARIO_DB_USER", "root"),
        password=os.environ.get("INVENTARIO_DB_PASSWORD", ""),
        database=os.environ.get("INVENTARIO_DB_NAME", "inventario"),
        port=int(os.environ.get("INVENTARIO_DB_PORT", "3306"))
    )

def inicializar_base_datos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100),
            correo VARCHAR(150),
            contrasena_hash VARCHAR(255),
            rol VARCHAR(50),
            estado_autorizacion VARCHAR(20) NOT NULL DEFAULT 'aprobado',
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        SELECT DATA_TYPE FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'usuarios'
          AND COLUMN_NAME = 'rol'
    """)
    rol_columna = cursor.fetchone()
    if rol_columna and rol_columna[0].lower() == "enum":
        cursor.execute("ALTER TABLE usuarios MODIFY COLUMN rol VARCHAR(50) NOT NULL")

    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'usuarios'
          AND COLUMN_NAME = 'estado_autorizacion'
    """)
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "ALTER TABLE usuarios ADD COLUMN estado_autorizacion VARCHAR(20) NOT NULL DEFAULT 'aprobado'"
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(100) NOT NULL UNIQUE,
            tipo VARCHAR(50) NOT NULL,
            marca VARCHAR(100),
            modelo VARCHAR(100),
            numero_serie VARCHAR(100),
            caracteristicas TEXT,
            foto VARCHAR(255),
            estado VARCHAR(50) NOT NULL DEFAULT 'bueno',
            salon_actual VARCHAR(100),
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    for columna, definicion in (
        ("foto_datos", "MEDIUMBLOB NULL"),
        ("foto_mime", "VARCHAR(50) NULL"),
    ):
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'equipos'
              AND COLUMN_NAME = %s
        """, (columna,))
        if cursor.fetchone()[0] == 0:
            cursor.execute(f"ALTER TABLE equipos ADD COLUMN {columna} {definicion}")

    # Agrega la columna en instalaciones que ya tenían creada la tabla.
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'equipos'
          AND COLUMN_NAME = 'foto'
    """)
    if cursor.fetchone()[0] == 0:
        cursor.execute("ALTER TABLE equipos ADD COLUMN foto VARCHAR(255) NULL")

    cursor.execute("""
        SELECT DATA_TYPE FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'equipos'
          AND COLUMN_NAME = 'tipo'
    """)
    tipo_columna = cursor.fetchone()
    if tipo_columna and tipo_columna[0].lower() == "enum":
        cursor.execute("ALTER TABLE equipos MODIFY COLUMN tipo VARCHAR(50) NOT NULL")

    for columna, definicion in (
        ("seccion", "VARCHAR(100) NULL"),
        ("fecha_modificacion", "DATETIME NULL"),
        ("modificado_por", "INT UNSIGNED NULL"),
        ("docente_cargo", "VARCHAR(150) NULL"),
    ):
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'equipos'
              AND COLUMN_NAME = %s
        """, (columna,))
        if cursor.fetchone()[0] == 0:
            cursor.execute(f"ALTER TABLE equipos ADD COLUMN {columna} {definicion}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salas (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL UNIQUE,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asignaciones (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            equipo_id INT UNSIGNED NOT NULL,
            usuario_id INT UNSIGNED NOT NULL,
            salon VARCHAR(100),
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE DEFAULT NULL,
            CONSTRAINT fk_asignacion_equipo
                FOREIGN KEY (equipo_id) REFERENCES equipos(id) ON DELETE CASCADE,
            CONSTRAINT fk_asignacion_usuario
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario_id INT UNSIGNED NULL,
            accion VARCHAR(80) NOT NULL,
            detalle VARCHAR(255) NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_movimientos_fecha (fecha),
            CONSTRAINT fk_movimiento_usuario
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave VARCHAR(50) PRIMARY KEY,
            valor TEXT NOT NULL,
            fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    admin_email = os.environ.get("INVENTARIO_ADMIN_EMAIL", "admin@colegio.local")
    cursor.execute("""
        INSERT IGNORE INTO configuracion (clave, valor)
        VALUES ('correo_alertas', %s)
    """, (admin_email,))

    conexion.commit()
    cursor.close()
    conexion.close()