# Cine Paradiso — Directrices del backend

Este documento es obligatorio para cualquier agente de inteligencia artificial (Copilot,
Cursor, Claude u otro) y para cualquier desarrollador que modifique el backend. Si una
decisión de implementación contradice este documento, debe detenerse y solicitar una
decisión del equipo antes de escribir código.

## 1. Rol y objetivo del agente

El agente actúa como Tech Lead y especialista en backend del proyecto universitario
**Cine Paradiso**. Su objetivo es entregar una API REST pura, segura, mantenible y
verificable para gestionar salas, películas, funciones, butacas, entradas, servicios
adicionales, compras, dashboards y control de acceso mediante QR.

Antes de modificar código, el agente debe:

1. Revisar la estructura existente, el esquema SQL, `requirements.txt`, `init.sh` y las
   pruebas disponibles.
2. Preservar el comportamiento válido y las convenciones del repositorio.
3. Implementar validación de entrada, autenticación, autorización por rol, manejo de
   errores y transacciones donde corresponda.
4. No inventar endpoints, estados o reglas que contradigan este documento o el esquema
   SQL. Las ambigüedades deben documentarse y consultarse.
5. Ejecutar las validaciones disponibles antes de informar que el trabajo está terminado.

## 2. Contexto y arquitectura

El backend es una API REST desarrollada en Python con Flask y conectada a MySQL
mediante un conector nativo, actualmente PyMySQL. Todos los endpoints deben responder
exclusivamente JSON; no se sirven plantillas HTML ni respuestas de redirección como
parte del contrato de la API.

La arquitectura obligatoria es por capas:

```text
HTTP/JSON
  -> Controladores / Blueprints
  -> Servicios / lógica de negocio
  -> Repositorios / DAO
  -> Conector MySQL
```

- **Controladores/Blueprints:** definen rutas y verbos HTTP, leen y validan el JSON
  superficialmente, aplican autenticación/autorización mediante decoradores o
  middleware y traducen resultados a respuestas HTTP.
- **Servicios:** contienen reglas de negocio, validaciones de dominio, políticas de
  cancelación, compras, QR, email simulado y coordinación de transacciones. No deben
  depender del objeto `request` de Flask.
- **Repositorios/DAO:** encapsulan conexiones, cursores y consultas SQL explícitas.
  Reciben parámetros separados de la sentencia y no contienen lógica HTTP.
- **Configuración:** usa variables de entorno y configuración de la aplicación. No se
  permiten credenciales codificadas ni estado mutable global.

El esquema debe mantenerse en scripts SQL reproducibles (`app/db/init_db.sql` para
creación y `app/db/seed.sql` para datos iniciales). Toda modificación del modelo debe
actualizar ambos scripts cuando corresponda y conservar claves foráneas, índices y
restricciones de integridad.

## 3. Reglas técnicas inquebrantables

| Hacer obligatoriamente | Terminantemente prohibido |
|---|---|
| Usar Flask y Blueprints para exponer una API REST JSON. | Usar HTML, templates, respuestas no JSON o lógica de presentación en el backend. |
| Ejecutar SQL escrito explícitamente con PyMySQL o un conector nativo equivalente. | Usar SQLAlchemy, Peewee, SQLModel, Flask-SQLAlchemy u otro ORM. |
| Pasar los valores mediante placeholders `%s` y una tupla/lista de parámetros. | Concatenar valores, interpolar strings o usar f-strings para construir SQL. |
| Validar tipos, presencia, rangos, enums y relaciones antes de ejecutar operaciones. | Confiar en datos del cliente o devolver éxito para entradas inválidas. |
| Mantener `datetime` como un único campo MySQL/Python para fecha y hora. | Separar fecha y horario en dos columnas o aceptar formatos ambiguos. |
| Abrir, confirmar y cerrar conexiones/cusores de forma segura. | Dejar conexiones abiertas, compartir cursores entre requests o usar estado mutable global. |
| Usar `BEGIN` y `COMMIT`/`ROLLBACK` en operaciones de compra y check-in. | Permitir que una butaca se venda dos veces o actualizar parcialmente una compra. |
| Aplicar autenticación y validar el rol requerido en cada endpoint protegido. | Confiar en un `user_id` enviado por el cliente o saltarse autorización. |
| Reutilizar helpers, validadores, respuestas y manejo de excepciones. | Duplicar código, copiar consultas o esconder errores con `except` amplios. |
| Gestionar dependencias mediante `requirements.txt` e `init.sh`. | Añadir dependencias que no puedan instalarse desde `init.sh`. |
| Mantener secretos en variables de entorno y fuera del repositorio. | Commitear contraseñas, tokens, claves o archivos `.env`. |

### Integridad, butacas y concurrencia

- Una entrada se identifica, como mínimo, por `id_funcion` y `numero_butaca`.
- Debe existir una restricción única compuesta equivalente a
  `UNIQUE (id_funcion, numero_butaca)`; la transacción debe tratar la violación como
  conflicto de negocio y responder `409` si el proyecto incorpora ese código.
- La compra debe ejecutarse dentro de una transacción SQL: validar función, sala,
  capacidad y butacas; insertar entradas y servicios; confirmar todo con `COMMIT` o
  deshacer todo con `ROLLBACK`.
- Una butaca cancelada puede volver a estar disponible solo si la regla de negocio y
  el modelo lo permiten; nunca se debe borrar el historial de una entrada usada.
- Las cancelaciones solo se permiten hasta el límite configurado antes de
  `funciones.fecha_hora_proyeccion`. El límite debe estar centralizado y probado.

### QR y email

Cada compra o entrada debe tener un código QR único y no predecible. El check-in debe
verificar autenticación del backoffice, existencia del código, función, fecha y hora,
estado no cancelado y estado no utilizado. La marcación como utilizada y la respuesta
de validación deben ocurrir en la misma transacción para impedir doble uso concurrente.

El envío de confirmación y factura al email se simula o se gestiona mediante un
servicio aislado; nunca debe impedir la consistencia de la compra ni exponer datos
privados en logs. Los fallos de email deben registrarse y devolverse según la política
del servicio, sin convertir una compra confirmada en una compra falsa.

## 4. Catálogo mínimo de endpoints

Los nombres son el contrato mínimo; pueden agregarse filtros o recursos compatibles
sin cambiar semántica. Todos los endpoints protegidos deben documentar el rol
permitido. Los identificadores se reciben como parámetros de ruta y los filtros como
query parameters validados.

### Autenticación y usuarios

| Método y ruta | Propósito | Acceso |
|---|---|---|
| `POST /api/auth/register` | Registrar cliente, validar email y almacenar contraseña hasheada. | Público |
| `POST /api/auth/login` | Autenticar y emitir token/sesión. | Público |
| `GET /api/auth/me` | Obtener el usuario autenticado. | Cliente, administrador |
| `POST /api/auth/logout` | Invalidar sesión/token cuando el mecanismo lo requiera. | Cliente, administrador |

### Películas, salas y funciones

| Método y ruta | Propósito | Acceso |
|---|---|---|
| `GET /api/peliculas` | Listar y filtrar películas. | Público |
| `GET /api/peliculas/<id>` | Consultar una película. | Público |
| `POST /api/peliculas` | Crear película. | Administrador |
| `PUT /api/peliculas/<id>` | Actualizar película. | Administrador |
| `DELETE /api/peliculas/<id>` | Desactivar/eliminar según integridad referencial. | Administrador |
| `GET /api/salas` | Listar salas y capacidades. | Público/administrador |
| `POST /api/salas` | Crear sala y sus butacas. | Administrador |
| `PUT /api/salas/<id>` | Actualizar sala sin invalidar ventas históricas. | Administrador |
| `GET /api/funciones` | Listar funciones por película, sala o `datetime`. | Público |
| `GET /api/funciones/<id>` | Consultar detalle de una función. | Público |
| `POST /api/funciones` | Programar función con `fecha_hora_proyeccion`. | Administrador |
| `PUT /api/funciones/<id>` | Reprogramar una función aplicando reglas de ventas. | Administrador |
| `DELETE /api/funciones/<id>` | Cancelar función, conservando trazabilidad. | Administrador |

### Butacas, reservas y entradas

| Método y ruta | Propósito | Acceso |
|---|---|---|
| `GET /api/funciones/<id>/butacas` | Mostrar capacidad y disponibilidad. | Público |
| `POST /api/reservas` | Crear una reserva temporal si el alcance la contempla. | Cliente |
| `DELETE /api/reservas/<id>` | Liberar reserva antes de su vencimiento. | Cliente |
| `POST /api/compras` | Comprar entradas y servicios en una transacción. | Cliente |
| `GET /api/compras` | Consultar compras propias o todas según rol. | Cliente/administrador |
| `GET /api/compras/<id>` | Consultar detalle, entradas y servicios. | Propietario/administrador |
| `DELETE /api/compras/<id>` | Cancelar compra si no venció el límite. | Propietario/administrador |

La compra debe validar que cada `numero_butaca` esté dentro de la capacidad de la sala,
que pertenezca a la función solicitada y que no exista otra entrada activa para la
misma función y butaca.

### Servicios adicionales

| Método y ruta | Propósito | Acceso |
|---|---|---|
| `GET /api/servicios` | Listar comida, bebidas, estacionamiento y VIP. | Público |
| `GET /api/servicios/<id>` | Consultar precio y descripción. | Público |
| `POST /api/servicios` | Crear servicio. | Administrador |
| `PUT /api/servicios/<id>` | Actualizar servicio. | Administrador |
| `DELETE /api/servicios/<id>` | Desactivar servicio sin romper compras históricas. | Administrador |
| `POST /api/compras/<id>/servicios` | Agregar servicios antes de la política de cierre. | Propietario/administrador |

### QR, check-in y notificaciones

| Método y ruta | Propósito | Acceso |
|---|---|---|
| `GET /api/entradas/<id>/qr` | Obtener/generar el QR único de una entrada válida. | Propietario/administrador |
| `POST /api/check-in/qr/validate` | Validar y marcar un QR como utilizado atómicamente. | Backoffice/administrador |
| `POST /api/compras/<id>/confirmation` | Simular reenvío de confirmación y factura. | Propietario/administrador |

### Dashboards

| Método y ruta | Propósito | Acceso |
|---|---|---|
| `GET /api/dashboard/ventas` | Ventas por período, función, sala y servicios. | Administrador |
| `GET /api/dashboard/ocupacion` | Ocupación y disponibilidad por función/sala. | Administrador |
| `GET /api/dashboard/servicios` | Rendimiento de comida, bebidas, estacionamiento y VIP. | Administrador |

Las agregaciones de dashboards deben usar SQL parametrizado y validar período,
`datetime` y permisos. No deben filtrar datos de otros clientes desde endpoints
destinados a clientes.

## 5. Contrato JSON y errores

### Respuesta exitosa

Las respuestas exitosas mantienen una forma coherente:

```json
{
  "ok": true,
  "data": {},
  "message": "Operación completada"
}
```

Para listados, `data` debe ser un arreglo y puede incluir `meta` para paginación:

```json
{
  "ok": true,
  "data": [],
  "meta": {"page": 1, "per_page": 20, "total": 0}
}
```

### Respuesta de error

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "El campo email es obligatorio",
    "details": {"field": "email"}
  }
}
```

`details` debe contener solo información segura y útil para el cliente; nunca SQL,
stack traces, contraseñas, tokens ni datos internos.

### Códigos HTTP obligatorios

| Código | Uso |
|---|---|
| `200 OK` | Consulta, actualización, eliminación lógica o acción completada. |
| `201 Created` | Recurso creado; incluir su representación o identificador. |
| `400 Bad Request` | JSON inválido, campos faltantes, tipos/formato inválidos o regla de entrada. |
| `401 Unauthorized` | Falta autenticación, token inválido o sesión expirada. |
| `403 Forbidden` | Usuario autenticado sin el rol o permiso requerido. |
| `404 Not Found` | Recurso inexistente o no visible para el usuario autorizado. |
| `500 Internal Server Error` | Error inesperado; registrar internamente y no filtrar detalles. |

Si el proyecto adopta `409 Conflict`, debe usarse para butacas ocupadas, QR ya
utilizado y conflictos de concurrencia, manteniendo el mismo formato JSON.

El manejo debe estar centralizado mediante handlers de Flask y excepciones de dominio
tipadas. Los controladores no deben contener bloques `try/except` repetidos ni devolver
respuestas diferentes para el mismo tipo de error. Los errores de base de datos deben
hacer `ROLLBACK` antes de liberar la conexión y deben registrarse con contexto
sanitizado.

## 6. Seguridad y validación

- Hashear contraseñas con una biblioteca segura; nunca guardarlas en texto plano.
- Configurar autenticación en un único punto y comprobar el rol en cada operación
  sensible.
- Validar que el usuario autenticado sea propietario del recurso, salvo rol
  administrador.
- Usar consultas parametrizadas incluso para filtros, orden permitido y paginación.
  Los nombres de columnas u órdenes dinámicos deben salir de listas blancas, nunca del
  input directo.
- No registrar contraseñas, tokens, códigos QR completos ni información de pago.
- Configurar CORS, límites de payload y modo debug solo según el entorno.

## 7. Dependencias, configuración y ejecución

Las dependencias deben declararse en `requirements.txt` y poder instalarse ejecutando:

```bash
./init.sh
```

La configuración de MySQL, secretos, entorno y límites de negocio debe provenir de
variables de entorno documentadas en `.env.example`. El archivo `.env` local nunca se
commitea. No crear singletons, caches mutables o conexiones globales; usar funciones,
fábricas o inyección explícita de dependencias con ciclo de vida por request/operación.

## 8. Convenciones de commits y Kanban

Cada commit debe representar una tarea concreta del Kanban de GitHub Projects y
referenciar su identificador:

```text
<tipo>(<área>): <descripción breve> [KAN-123]
```

Tipos permitidos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf` y
`security`. Áreas sugeridas: `auth`, `peliculas`, `funciones`, `butacas`, `compras`,
`servicios`, `qr`, `dashboard`, `db` e `infra`.

Ejemplos:

```text
feat(compras): impedir venta duplicada de butacas [KAN-42]
fix(qr): rechazar entradas ya utilizadas [KAN-57]
docs(db): documentar inicialización de MySQL [KAN-12]
```

No mezclar tareas del Kanban sin relación en un mismo commit. El cuerpo puede incluir
la decisión técnica relevante, las migraciones/scripts afectados y la validación
ejecutada. Las ramas y pull requests deben conservar la referencia de la tarea para
que el tablero pueda rastrear el trabajo.

## 9. Criterio de aceptación

Una modificación solo está terminada cuando:

- todos los endpoints nuevos o modificados respetan el contrato JSON y los códigos
  HTTP;
- la autenticación, roles, propiedad del recurso y validaciones están cubiertas;
- las consultas MySQL son SQL explícito y parametrizado;
- las operaciones críticas tienen `COMMIT`/`ROLLBACK` y preservan la integridad;
- los scripts SQL y `init.sh` siguen siendo reproducibles;
- no se introdujeron ORMs, variables globales, duplicación ni secretos;
- se ejecutaron las pruebas, linting o validaciones disponibles y se informaron sus
  resultados.
