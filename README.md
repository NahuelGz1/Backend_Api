# Cine Paradiso — API Backend

API REST del sistema **Cine Paradiso**, desarrollada con Python y Flask. Provee las operaciones necesarias para autenticación de usuarios, cartelera, programación y cancelación de funciones, disponibilidad de butacas y estacionamiento, servicios adicionales, compras de entradas, validación de códigos QR y métricas administrativas.

> Este repositorio contiene el **backend**. La interfaz web se encuentra en [Frontend-Web](https://github.com/NahuelGz1/Frontend-Web).

## Tecnologías

- **Python 3** y **Flask 3.0.3**: servidor HTTP y rutas REST.
- **MySQL** y **PyMySQL**: persistencia de datos.
- **PyJWT**: autenticación mediante tokens JWT.
- **Requests**: integración con servicios externos como TMDB.
- **qrcode** y **Pillow**: generación de códigos QR.
- **python-dotenv**: variables de entorno.
- **Gunicorn**: servidor WSGI para despliegue (incluido en `requirements.txt`).

El `Dockerfile` utiliza **Python 3.12**.

## Requisitos previos

- Python 3 y el módulo `venv`.
- MySQL en ejecución y una cuenta de base de datos con los permisos necesarios.
- Git para clonar y actualizar el repositorio.
- Una clave de API de **TMDB** para las funciones que consultan esa plataforma.

## Instalación local

### 1. Clonar el proyecto

```bash
git clone https://github.com/NahuelGz1/Backend_Api.git
cd Backend_Api
```

Si ya tenés el repositorio, no hace falta volver a clonarlo.

### 2. Preparar el entorno de Python

**Linux (bash):**

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

**Windows (PowerShell):**

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Como alternativa en entornos bash, el repositorio incluye `init.sh` para crear o reutilizar `venv`, instalar dependencias y copiar `.env.example` si todavía no existe:

```bash
bash init.sh
```

### 3. Configurar variables de entorno

Creá un archivo `.env` a partir del ejemplo:

```bash
cp .env.example .env
```

En Windows también podés copiar y renombrar el archivo desde el explorador de archivos.

Configurá como mínimo las variables correspondientes a tu entorno:

| Variable | Propósito |
| --- | --- |
| `DB_HOST` | Host de MySQL; normalmente `localhost` en desarrollo local. |
| `DB_PORT` | Puerto de MySQL; normalmente `3306`. |
| `DB_USER` | Usuario de MySQL utilizado por la API. |
| `DB_PASSWORD` | Contraseña de ese usuario. |
| `DB_NAME` | Nombre de la base de datos; por defecto `cine_paradiso`. |
| `JWT_SECRET_KEY` | Clave secreta para JWT; **mínimo 32 caracteres**. |
| `TMDB_API_KEY` | Clave de acceso a TMDB para las funciones que lo utilizan. |
| `AUTO_MIGRATE` | Si vale `true`, ejecuta la comprobación/migración del esquema al iniciar. |
| `AUTO_SEED` | Si vale `true`, intenta crear datos de prueba para validar QR; mantener en `false` normalmente. |

El archivo de ejemplo también contiene parámetros SMTP y de recuperación de contraseña (`SMTP_*`, `PASSWORD_RESET_URL`) y opciones de TMDB (`TMDB_BASE_URL`, `TMDB_IMAGE_BASE_URL`). Revisalos si vas a usar esas funcionalidades.

**Seguridad:** no subas `.env` al repositorio ni compartas contraseñas, tokens JWT, claves de TMDB o credenciales SMTP. El proyecto ya incluye `.env` en `.gitignore`.

### 4. Preparar MySQL (solamente en una instalación nueva)

El esquema inicial se encuentra en `app/db/init_db.sql`. Debe ejecutarse **solo sobre una instalación nueva**, con una cuenta de MySQL autorizada para crear la base y sus tablas. Por ejemplo:

```bash
sudo mysql < app/db/init_db.sql
```

El repositorio también incluye `app/db/seed.sql` con datos iniciales y registros de prueba. Su ejecución es **opcional** y debe reservarse a una base nueva de desarrollo:

```bash
sudo mysql < app/db/seed.sql
```

**Importante:** no vuelvas a ejecutar estos archivos sobre una base con datos. El script de tablas no es una migración general para instalaciones existentes y el de datos puede insertar registros duplicados. Antes de cualquier cambio de esquema, realizá un respaldo y revisá las migraciones disponibles en `app/db/migrations/` (incluida `003_add_cancelacion_funciones.sql`, que agrega el estado y el motivo de cancelación).

Las migraciones que ejecuta `db.py` también pueden necesitar permisos de creación o alteración de tablas. Utilizá una cuenta MySQL con permisos adecuados para el entorno, evitando credenciales de administrador global en producción.

La tabla `reseñas` se incluye en el esquema inicial. Para instalaciones existentes, `app/db/migrations/004_create_resenas.sql` la crea si no existe, sin modificar reseñas previas; seleccioná la base de datos al ejecutar el script. La comprobación automática de `db.py` se mantiene por compatibilidad cuando `AUTO_MIGRATE` está habilitado.

La película destacada se guarda en `pelicula_destacada`. En instalaciones existentes se crea al iniciar con `AUTO_MIGRATE=true`, o manualmente con `app/db/migrations/005_create_pelicula_destacada.sql` sobre la base seleccionada. Un administrador puede elegirla desde una función activa y futura; si deja de tener funciones vigentes, la portada muestra otra película de cartelera hasta que vuelva a estar disponible o se elija otra.

### 5. Iniciar el backend

Con el entorno virtual activado y MySQL disponible:

```bash
python app.py
```

De forma predeterminada, Flask escucha en el puerto **5000**, con base de API `/api`.

**Verificación rápida:** abrí [http://127.0.0.1:5000/api/ping](http://127.0.0.1:5000/api/ping) o ejecutá:

```bash
curl http://127.0.0.1:5000/api/ping
```

La respuesta esperada es:

```json
{
  "ok": true,
  "data": null,
  "message": "Backend Flask running"
}
```

## Principales recursos de la API

Las rutas se registran en `app.py`. Con la configuración predeterminada, los grupos de endpoints son:

| Prefijo | Funcionalidad |
| --- | --- |
| `/api/auth` | Registro, acceso, perfil y administración de usuarios. |
| `/api/peliculas` | Cartelera, detalle, estrenos y gestión de películas. |
| `/api/funciones` | Programación, cancelación y estado de funciones; disponibilidad de butacas y estacionamiento. |
| `/api/funciones/salas` | Gestión de salas. |
| `/api/butacas` | Consulta de disponibilidad por función. |
| `/api/servicios` | Catálogo y administración de servicios adicionales. |
| `/api/compras` | Compras de entradas y servicios, cancelaciones de compras y validación de QR. |
| `/api/dashboard` | Métricas administrativas. |

### Cambios funcionales recientes

- **Estacionamiento por función:** `GET /api/funciones/{funcion_id}/estacionamiento` devuelve `limite`, `vendidos` y `disponibles`. El cupo actual es de **20 plazas por función**. Al comprar servicios, el número de estacionamientos no puede superar las entradas de la compra ni el cupo disponible.
- **Cancelación administrativa de funciones:** `PUT /api/funciones/{funcion_id}/cancelar` requiere una cuenta administradora y un JSON con `motivo`. Cancela entradas activas, registra el importe de devolución de entradas y servicios e intenta notificar por correo a los compradores. Las funciones canceladas permanecen en el historial y no pueden reactivarse.
- **Validación de compras:** en `POST /api/compras`, cada elemento de `servicios` incluye `id_servicio`, `cantidad` y `precio` conforme a la implementación actual.

> Estas rutas administrativas y de compra modifican datos reales. Para probarlas, usá una base de desarrollo y consultá los detalles y códigos de respuesta en el manual OpenAPI.

Algunas rutas requieren un token JWT y otras además exigen el rol `administrador`. Las respuestas exitosas siguen, en general, la estructura `{ "ok": true, "data": ..., "message": ... }`; los errores devuelven `{ "ok": false, "error": { "code": ..., "message": ..., "details": ... } }`.

La documentación detallada de parámetros, cuerpos de solicitud, respuestas y autenticación se encuentra en el [Manual de API](docs/Manual_API_Cine_paradiso.yaml), elaborado siguiendo OpenAPI 3.0 y el modelo proporcionado por la cátedra.

## Estructura relevante

```text
Backend_Api/
├── app.py                  # Creación de la app Flask y registro de rutas
├── wsgi.py                 # Entrada WSGI para Gunicorn
├── db.py                   # Conexión, consultas y migraciones del esquema
├── requirements.txt       # Dependencias de Python
├── .env.example           # Plantilla de configuración
├── Dockerfile             # Imagen del backend
├── docs/                  # Manual de API OpenAPI 3.0
├── init.sh                # Inicialización del entorno local
└── app/
    ├── routes/            # Endpoints de la API
    ├── db/
    │   ├── init_db.sql    # Esquema para instalaciones nuevas
    │   ├── seed.sql       # Datos de desarrollo
    │   └── migrations/    # Migraciones incrementales
    └── utils/             # Utilidades, incluido el formato de respuestas
```

## Ejecución con Docker (opcional)

Existe un `Dockerfile` que instala dependencias y ejecuta Gunicorn en el puerto `5000`:

```bash
docker build -t cine-paradiso-backend .
```

Para ejecutar el contenedor es necesario pasar las variables de entorno correspondientes y configurar un **MySQL accesible desde el contenedor**. Atención: `DB_HOST=localhost` dentro de Docker apunta al propio contenedor, no a la computadora anfitriona. Ajustá `DB_HOST` y la conectividad de red según tu entorno antes de levantarlo.

## Colaboración

El desarrollo del equipo se integra en la rama `develop`. Para una contribución nueva, creá una rama de trabajo, realizá los cambios necesarios y abrí un Pull Request para su revisión.

## Documentación

- [Repositorio del frontend](https://github.com/NahuelGz1/Frontend-Web)
- [Issue de documentación técnica #83](https://github.com/NahuelGz1/Backend_Api/issues/83)
- [Manual de API (OpenAPI 3.0)](docs/Manual_API_Cine_paradiso.yaml).
