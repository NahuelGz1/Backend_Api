-- Por defecto solo agrega servicios faltantes. Con @restablecer_catalogo = 1
-- restaura el catálogo y desactiva los demás servicios sin borrar su historial.
SET NAMES utf8mb4;

CREATE TEMPORARY TABLE catalogo_inicial_servicios AS
    SELECT 'Balde de pochoclos' AS nombre, '1 balde de pochoclos' AS descripcion, 13500.00 AS precio, 'Pochoclos' AS categoria
    UNION ALL SELECT 'Combo Mega Recargado', '1 balde de pochoclos, 2 gaseosas grandes, 1 golosina y recarga de balde y vasos', 39700.00, 'Pochoclos'
    UNION ALL SELECT 'Combo Mega Individual', '1 balde de pochoclos y 1 gaseosa grande', 23400.00, 'Pochoclos'
    UNION ALL SELECT 'Agua', '1 agua, valor por unidad', 5200.00, 'Bebidas'
    UNION ALL SELECT 'Estacionamiento', 'Cochera durante la función', 6000.00, 'Mejoras de experiencia'
    UNION ALL SELECT 'Acceso VIP', 'Zona de espera con souvenir temático y snacks.', 15000.00, 'Mejoras de experiencia'
    UNION ALL SELECT 'Combo Familia', '2 baldes de pochoclos, 4 gaseosas grandes y 2 golosinas sin eleccion', 54000.00, 'Pochoclos'
    UNION ALL SELECT 'Gaseosa', '1 gaseosa 500ml', 6000.00, 'Bebidas'
    UNION ALL SELECT 'Combo Nachos', 'Nachos con queso y 1 gaseosa a elección', 19350.00, 'Snacks'
    UNION ALL SELECT 'Combo Pancho', '1 pancho y 1 gaseosa grande a elección', 14700.00, 'Snacks'
    UNION ALL SELECT 'Nachos', '1 Nachos con queso', 12500.00, 'Snacks'
    UNION ALL SELECT 'Pancho', '1 pancho con aderezos a elección', 6900.00, 'Snacks';

START TRANSACTION;

INSERT INTO servicios (nombre, descripcion, precio, categoria)
SELECT catalogo.nombre, catalogo.descripcion, catalogo.precio, catalogo.categoria
FROM catalogo_inicial_servicios AS catalogo
WHERE NOT EXISTS (
    SELECT 1 FROM servicios existente WHERE existente.nombre = catalogo.nombre
);

CREATE TEMPORARY TABLE servicios_iniciales_elegidos AS
SELECT MIN(servicio.id) AS id, catalogo.nombre, catalogo.descripcion,
       catalogo.precio, catalogo.categoria
FROM catalogo_inicial_servicios AS catalogo
JOIN servicios AS servicio ON servicio.nombre = catalogo.nombre
GROUP BY catalogo.nombre, catalogo.descripcion, catalogo.precio, catalogo.categoria;

UPDATE servicios AS servicio
JOIN servicios_iniciales_elegidos AS catalogo ON servicio.id = catalogo.id
SET servicio.nombre = catalogo.nombre,
    servicio.descripcion = catalogo.descripcion,
    servicio.precio = catalogo.precio,
    servicio.categoria = catalogo.categoria,
    servicio.imagen_url = NULL,
    servicio.activo = TRUE
WHERE COALESCE(@restablecer_catalogo, 0) = 1;

UPDATE servicios AS servicio
LEFT JOIN servicios_iniciales_elegidos AS catalogo ON servicio.id = catalogo.id
SET servicio.activo = FALSE
WHERE COALESCE(@restablecer_catalogo, 0) = 1 AND catalogo.id IS NULL;

COMMIT;
DROP TEMPORARY TABLE servicios_iniciales_elegidos;
DROP TEMPORARY TABLE catalogo_inicial_servicios;
