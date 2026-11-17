USE cine_paradiso;

ALTER TABLE detalles_servicios
    ADD COLUMN IF NOT EXISTS cantidad_usada INT NOT NULL DEFAULT 0;

UPDATE detalles_servicios
SET cantidad_usada = cantidad
WHERE usado = TRUE AND cantidad_usada = 0;
