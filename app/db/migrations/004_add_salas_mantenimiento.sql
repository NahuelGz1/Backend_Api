USE cine_paradiso;

SET @salas_activo_existe := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'salas'
      AND column_name = 'activo'
);

SET @sql := IF(
    @salas_activo_existe = 0,
    'ALTER TABLE salas ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE',
    'SELECT 1'
);

PREPARE migracion_salas_activo FROM @sql;
EXECUTE migracion_salas_activo;
DEALLOCATE PREPARE migracion_salas_activo;
