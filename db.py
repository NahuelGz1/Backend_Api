import os
import threading
import pymysql
from pymysql.cursors import DictCursor

_schema_lock = threading.Lock()
_schema_ready = False


def _asegurar_tablas_compra(cursor):
    """Completa instalaciones antiguas sin entradas; nunca borra su historial."""
    cursor.execute("SHOW COLUMNS FROM entradas")
    columnas = {fila["Field"]: fila for fila in cursor.fetchall()}
    if "id_compra" not in columnas:
        cursor.execute("SELECT COUNT(*) AS cantidad FROM entradas")
        if cursor.fetchone()["cantidad"]:
            raise RuntimeError(
                "El esquema antiguo contiene entradas. Se requiere una migración "
                "de su historial antes de habilitar compras; no se modificaron esas entradas."
            )
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_usuario INT NOT NULL,
            codigo_qr VARCHAR(255) NOT NULL,
            fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
        )
    """)
    if "id_compra" not in columnas:
        cursor.execute("""
            ALTER TABLE entradas
            ADD COLUMN id_compra INT NOT NULL,
            ADD FOREIGN KEY (id_compra) REFERENCES compras(id)
        """)
    if "precio_historico" not in columnas:
        cursor.execute("ALTER TABLE entradas ADD COLUMN precio_historico DECIMAL(10, 2) NOT NULL DEFAULT 0")
    if "id_usuario" in columnas and columnas["id_usuario"]["Null"] == "NO":
        cursor.execute("ALTER TABLE entradas MODIFY id_usuario INT NULL")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalles_servicios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_compra INT NOT NULL,
            id_servicio INT NOT NULL,
            cantidad INT DEFAULT 1,
            precio_historico DECIMAL(10, 2) NOT NULL,
            usado BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (id_compra) REFERENCES compras(id),
            FOREIGN KEY (id_servicio) REFERENCES servicios(id)
        )
    """)


def asegurar_esquema():
    """Aplica migraciones compatibles usando el usuario configurado en el entorno."""
    _asegurar_columnas_de_estado()


def cargar_fixture_qr_prueba():
    """Crea una compra de prueba idempotente para validar el flujo completo."""
    conexion = obtener_conexion()
    qr = "QR-PRUEBA-CINE-PARADISO-2026"
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO compras (id_usuario, codigo_qr)
                SELECT id, %s FROM usuarios
                WHERE email = %s
                  AND NOT EXISTS (
                      SELECT 1 FROM compras WHERE codigo_qr = %s
                  )
                LIMIT 1
                """,
                (qr, "cine_paradiso@admin.com", qr),
            )
            cursor.execute("SELECT id FROM compras WHERE codigo_qr = %s", (qr,))
            compra = cursor.fetchone()
            if not compra:
                raise RuntimeError("No se pudo crear la compra de prueba del QR")

            cursor.execute(
                "SELECT COUNT(*) AS cantidad FROM entradas WHERE id_compra = %s",
                (compra["id"],),
            )
            if cursor.fetchone()["cantidad"]:
                conexion.commit()
                return

            cursor.execute(
                """
                SELECT f.id, s.capacidad
                FROM funciones f
                INNER JOIN salas s ON s.id = f.id_sala
                WHERE f.activo = TRUE
                ORDER BY f.id
                LIMIT 1
                """
            )
            funcion = cursor.fetchone()
            if not funcion:
                raise RuntimeError("No hay funciones activas para crear el QR de prueba")

            cursor.execute(
                """
                SELECT numero_butaca
                FROM entradas
                WHERE id_funcion = %s AND estado != 'cancelada'
                """,
                (funcion["id"],),
            )
            ocupadas = {fila["numero_butaca"] for fila in cursor.fetchall()}
            butacas = [
                numero for numero in range(1, int(funcion["capacidad"]) + 1)
                if numero not in ocupadas
            ][:2]
            if len(butacas) < 2:
                raise RuntimeError("No hay dos butacas libres para el QR de prueba")

            cursor.execute(
                """
                INSERT INTO entradas
                    (id_compra, id_funcion, numero_butaca, precio_historico, codigo_qr, estado)
                VALUES
                    (%s, %s, %s, 10000.00, %s, 'comprada'),
                    (%s, %s, %s, 10000.00, %s, 'comprada')
                ON DUPLICATE KEY UPDATE id_compra = VALUES(id_compra)
                """,
                (
                    compra["id"], funcion["id"], butacas[0], qr,
                    compra["id"], funcion["id"], butacas[1], qr,
                ),
            )
            cursor.execute(
                """
                SELECT id, nombre, precio
                FROM servicios
                WHERE nombre IN ('Estacionamiento', 'Acceso VIP')
                """
            )
            servicios_prueba = {
                fila["nombre"]: fila for fila in cursor.fetchall()
            }
            if len(servicios_prueba) < 2:
                raise RuntimeError(
                    "No están disponibles los servicios necesarios para el QR de prueba"
                )
            cursor.execute(
                """
                INSERT IGNORE INTO detalles_servicios
                    (id_compra, id_servicio, cantidad, precio_historico, usado)
                VALUES
                    (%s, %s, 1, %s, FALSE),
                    (%s, %s, 1, %s, FALSE)
                """,
                (
                    compra["id"],
                    servicios_prueba["Estacionamiento"]["id"],
                    servicios_prueba["Estacionamiento"]["precio"],
                    compra["id"],
                    servicios_prueba["Acceso VIP"]["id"],
                    servicios_prueba["Acceso VIP"]["precio"],
                ),
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def _asegurar_columnas_de_estado():
    global _schema_ready
    if _schema_ready:
        return
    with _schema_lock:
        if _schema_ready:
            return
        conexion = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "cine_paradiso"),
            port=int(os.getenv("DB_PORT", 3306)),
            cursorclass=DictCursor,
            autocommit=True,
        )
        try:
            with conexion.cursor() as cursor:
                _asegurar_tablas_compra(cursor)
                cursor.execute("SHOW COLUMNS FROM servicios LIKE 'activo'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE servicios ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE")
                for tabla in ("peliculas", "funciones"):
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS cantidad
                        FROM information_schema.columns
                        WHERE table_schema = DATABASE()
                          AND table_name = %s
                          AND column_name = 'activo'
                        """,
                        (tabla,),
                    )
                    if cursor.fetchone()["cantidad"] == 0:
                        cursor.execute(
                            f"ALTER TABLE `{tabla}` "
                            "ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE"
                        )
                cursor.execute(
                    """
                    SELECT COUNT(*) AS cantidad
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                      AND table_name = 'funciones'
                      AND column_name = 'eliminada'
                    """
                )
                if cursor.fetchone()["cantidad"] == 0:
                    cursor.execute(
                        "ALTER TABLE funciones ADD COLUMN eliminada BOOLEAN NOT NULL DEFAULT FALSE"
                    )
                cursor.execute(
                    """
                    SELECT COUNT(*) AS cantidad
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                      AND table_name = 'peliculas'
                      AND column_name = 'eliminada'
                    """
                )
                if cursor.fetchone()["cantidad"] == 0:
                    cursor.execute(
                        "ALTER TABLE peliculas ADD COLUMN eliminada BOOLEAN NOT NULL DEFAULT FALSE"
                    )
                cursor.execute(
                    """
                    SELECT COUNT(*) AS cantidad FROM information_schema.columns
                    WHERE table_schema = DATABASE() AND table_name = 'servicios'
                    AND column_name = 'categoria'
                    """
                )
                if cursor.fetchone()["cantidad"] == 0:
                    cursor.execute(
                        "ALTER TABLE servicios ADD COLUMN categoria VARCHAR(40) NOT NULL DEFAULT 'Snacks'"
                    )
                cursor.execute(
                    """
                    SELECT COUNT(*) AS cantidad FROM information_schema.columns
                    WHERE table_schema = DATABASE() AND table_name = 'servicios'
                    AND column_name = 'imagen_url'
                    """
                )
                if cursor.fetchone()["cantidad"] == 0:
                    cursor.execute(
                        "ALTER TABLE servicios ADD COLUMN imagen_url MEDIUMTEXT"
                    )
                cursor.execute(
                    """
                    SELECT COUNT(*) AS cantidad
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                      AND table_name = 'compras'
                      AND column_name = 'codigo_qr'
                    """
                )
                if cursor.fetchone()["cantidad"] == 0:
                    cursor.execute("ALTER TABLE compras ADD COLUMN codigo_qr VARCHAR(255) NULL")
                    cursor.execute(
                        """
                        UPDATE compras c
                        INNER JOIN (
                            SELECT id_compra, MIN(codigo_qr) AS codigo_qr
                            FROM entradas
                            GROUP BY id_compra
                        ) e ON e.id_compra = c.id
                        SET c.codigo_qr = e.codigo_qr
                        WHERE c.codigo_qr IS NULL
                        """
                    )
                    cursor.execute("ALTER TABLE compras MODIFY codigo_qr VARCHAR(255) NOT NULL")

                cursor.execute(
                    """
                    SELECT COUNT(*) AS cantidad
                    FROM information_schema.statistics
                    WHERE table_schema = DATABASE()
                      AND table_name = 'entradas'
                      AND index_name = 'codigo_qr'
                    """
                )
                if cursor.fetchone()["cantidad"]:
                    cursor.execute("ALTER TABLE entradas DROP INDEX codigo_qr")
            _schema_ready = True
        finally:
            conexion.close()

def obtener_conexion():
    """
    Crea y devuelve la conexión a la base de datos usando las variables de entorno.
    Si falla, lanza la excepción para ser capturada por el handler global.
    """
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "cine_paradiso"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=DictCursor,
        autocommit=False,
    )

def ejecutar_consulta(sql: str, parametros: tuple = ()) -> list[dict]:
    """
    Ejecuta consultas SELECT y devuelve una lista de diccionarios.
    Lanza la excepción si ocurre un error en la base de datos.
    """
    _asegurar_columnas_de_estado()
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchall()
    finally:
        conexion.close()

def ejecutar_mutacion(sql: str, parametros: tuple = ()) -> int:
    """
    Ejecuta consultas INSERT, UPDATE o DELETE con manejo explícito de transacciones.
    En caso de error hace rollback y vuelve a lanzar la excepción.
    """
    _asegurar_columnas_de_estado()
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            conexion.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()