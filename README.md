# Proyecto-Web-Final

## Autenticacion — Subtask 3.1.1

[Issue #67](https://github.com/NahuelGz1/Backend_Api/issues/67).
Rama: `feature/subtask_3.1.1`, coordinada con la misma rama de Frontend-Web.
Se conserva la estructura: rutas en `app/routes`, servicios en `app/services`,
SQL parametrizado en `app/repositories`, conexion y esquema en `app/db` y `db.py`.
No hay ORM ni persistencia de credenciales en el frontend.

### Inicio

```sh
bash init.sh
```

Configurar `.env` con MySQL, una `JWT_SECRET_KEY` aleatoria de al menos 32 caracteres
y un servidor SMTP. No hay secreto JWT por defecto; la aplicacion falla al
arrancar si falta. Generar una clave con:

```sh
venv/bin/python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`PASSWORD_RESET_URL` debe apuntar a la vista del frontend, por ejemplo
`http://localhost:3000/auth/restablecer-contrasena`, sin query ni fragmento.
SMTP usa `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, `SMTP_USERNAME`, `SMTP_PASSWORD` y
`SMTP_STARTTLS` (true por defecto). Solo deshabilitar STARTTLS para un buzon
aislado local como Mailpit. No enviar mensajes reales en las pruebas.

```sh
venv/bin/python app.py
# Alternativamente:
venv/bin/flask --app app:create_app run --port 5000
```

El esquema `usuarios` existente es suficiente; no se requiere una migracion.
**No volver a ejecutar `app/db/init_db.sql` contra una base existente: contiene
DROP DATABASE.**

### Contrato HTTP

Todas las respuestas tienen `ok`, `data` y `message` en exito; en error,
`ok=false` y `error: {code, message, details}`. Los endpoints de autenticacion
usan `Cache-Control: no-store`.

| Metodo / endpoint | JSON | Respuestas |
| --- | --- | --- |
| POST `/api/auth/register` | `nombre`, `email`, `password` | 201 creado, 400 invalido, 409 email duplicado |
| POST `/api/auth/login` | `email`, `password` | 200 con `data.token` y `data.usuario`, 401 credenciales incorrectas, 400 datos invalidos, 403 rol no admitido |
| POST `/api/auth/forgot-password` | `email` | 200 mensaje generico, 400 email invalido, 503 fallo SMTP |
| POST `/api/auth/reset-password` | `token`, `password` | 200 actualizada, 400 enlace invalido/vencido/usado o clave invalida |
| GET `/api/auth/usuarios/me` | Header `Authorization: Bearer ...` | 200 perfil, 401 sesion invalida |
| POST `/api/auth/logout` | Header `Authorization: Bearer ...` | 200; el frontend elimina su sesion del servidor |

Se rechazan arrays, escalares, JSON malformado y cuerpos sin formato JSON con 400.
Las excepciones HTTP conservan su codigo, incluido 405; los errores inesperados
responden 500 sin exponer SQL, contraseñas o tokens.

Registro fuerza `cliente`; el cliente no puede solicitar un rol privilegiado.
Los roles son `cliente` y `administrador`. El nombre/email tienen un maximo de
100 caracteres y las claves nuevas de 8 a 128. El email se normaliza a minusculas.
Las contraseñas se guardan mediante `generate_password_hash` de Werkzeug (scrypt),
nunca en texto plano ni con cifrado reversible.

### Recuperacion y sesiones

La solicitud no cambia la clave: envia un enlace firmado de 30 minutos al correo
de la cuenta. Su respuesta normal es igual para correos existentes e inexistentes.
El token incluye una huella del hash actual y se firma con un salt exclusivo para
recuperacion. No se devuelve el token en JSON ni se registra en logs.

El restablecimiento verifica firma, vencimiento y huella actual, y ejecuta:

```sql
UPDATE usuarios SET password_hash = %s WHERE id = %s AND password_hash = %s
```

La comparacion con el hash anterior impide reutilizacion y carreras: solo una
operacion modifica la fila. Todos los enlaces anteriores quedan invalidos al
cambiar la clave, incluso si todavia no vencieron.

Los JWT de acceso incluyen la huella de la credencial. Cada ruta autenticada
consulta el usuario vigente, valida esa huella y toma el rol de MySQL, no del
rol antiguo del JWT. Al cambiar/restablecer la contraseña se invalidan sesiones
anteriores. Los JWT emitidos antes de este cambio carecen de `ver` y requieren
iniciar sesion nuevamente. El logout no mantiene lista de revocacion JWT; elimina
la sesion frontend que custodia el token. Un token ya robado es valido hasta su
vencimiento o cambio de clave.

En produccion usar HTTPS, SMTP con TLS y limites de solicitudes en el proxy
para registro/login/recuperacion. Configurar los logs de acceso para no registrar
query strings con tokens ni cuerpos JSON de autenticacion.

### Pruebas sobre MySQL real

Las pruebas crean una base `test_auth_<uuid>` y eliminan **solo esa base** al
terminar. Requieren una instancia MySQL aislada accesible con root sin contraseña,
exclusivamente para pruebas; no apuntarlas a produccion.

```sh
docker run --name cine-auth-mysql-test --rm -d \
  -e MYSQL_ALLOW_EMPTY_PASSWORD=yes -p 127.0.0.1:3307:3306 \
  mysql:8.0 --default-authentication-plugin=mysql_native_password
docker exec cine-auth-mysql-test mysqladmin ping -h127.0.0.1
TEST_DB_PORT=3307 venv/bin/python -m unittest discover -s tests -v
docker stop cine-auth-mysql-test
```

Esperar a que MySQL este listo antes de ejecutar las pruebas. Cubren SQL real,
hash, roles, JSON, errores HTTP, duplicados, inyeccion como datos, recuperacion,
fallo SMTP, vencimiento, reutilizacion e invalidacion de JWT. La prueba completa
de formularios/HTTP/SMTP esta en `Frontend-Web/tests/test_auth_integration.py`.