USE cine_paradiso;

ALTER TABLE peliculas
    ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE funciones
    ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE funciones
    ADD COLUMN eliminada BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE peliculas
    ADD COLUMN IF NOT EXISTS eliminada BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE servicios
    ADD COLUMN IF NOT EXISTS categoria VARCHAR(40) NOT NULL DEFAULT 'Snacks';

ALTER TABLE compras
    ADD COLUMN IF NOT EXISTS codigo_qr VARCHAR(255) UNIQUE;

UPDATE compras c
    INNER JOIN (
        SELECT id_compra, MIN(codigo_qr) AS codigo_qr
        FROM entradas
        GROUP BY id_compra
    ) e ON e.id_compra = c.id
SET c.codigo_qr = e.codigo_qr
WHERE c.codigo_qr IS NULL;

ALTER TABLE compras
    MODIFY codigo_qr VARCHAR(255) NOT NULL;
