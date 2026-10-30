
-- Borra por completo la base de datos cine_paradiso si es que ya existía de antes.

DROP DATABASE IF EXISTS cine_paradiso;
CREATE DATABASE cine_paradiso CHARACTER SET utf8mb4; -- se le pone para que acepte tildes, eñes y emojis sin romperse.
USE cine_paradiso;


-- Usuarios. El rol puede ser 'administrador' o 'cliente'
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL
);

-- Películas. Clasificación: ATP, +13, +16, +18
CREATE TABLE peliculas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    sinopsis TEXT,
    poster VARCHAR(255),
    duracion INT,
    clasificacion VARCHAR(10),
    genero VARCHAR(50)
);

-- Salas de cada local
CREATE TABLE salas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    capacidad INT NOT NULL,
    local VARCHAR(100) NOT NULL
);

-- Servicios extra (comida, bebida, etc)
CREATE TABLE servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL
);

-- (ahora las que dependen de las anteriores)

-- Funciones: una película, en una sala, en un día y hora
CREATE TABLE funciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_pelicula INT NOT NULL,
    id_sala INT NOT NULL,
    fecha_hora_proyeccion DATETIME NOT NULL,
    FOREIGN KEY (id_pelicula) REFERENCES peliculas(id),
    FOREIGN KEY (id_sala) REFERENCES salas(id)
);

-- Entradas. Estado: 'comprada', 'cancelada' o 'utilizada'
-- La butaca no se puede repetir en la misma función
CREATE TABLE entradas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_funcion INT NOT NULL,
    numero_butaca INT NOT NULL,
    codigo_qr VARCHAR(255) UNIQUE NOT NULL,
    estado VARCHAR(20) DEFAULT 'comprada',
    UNIQUE KEY butaca_unica_por_funcion (id_funcion, numero_butaca),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY (id_funcion) REFERENCES funciones(id)
);

-- Compras de servicios
CREATE TABLE compras_servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_servicio INT NOT NULL,
    fecha_hora_compra DATETIME NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY (id_servicio) REFERENCES servicios(id)
);


-- Precargar los datos:
-- Aclaracion: importa el orden, primero van las películas y salas, despues funciones (Esto es porque usan sus ids)

-- 10 peliculas (los ids van del 1 al 10)
INSERT INTO peliculas (titulo, sinopsis, duracion, clasificacion, genero) VALUES
    ('Volver al Futuro', 'Un chico viaja al pasado en una máquina del tiempo.', 116, 'ATP', 'Ciencia ficción'),
    ('El Rey León', 'Un león joven debe recuperar su reino.', 88, 'ATP', 'Animación'),
    ('Terminator 2: El juicio final', 'Un robot viaja al pasado para proteger a un niño.', 137, '+16', 'Acción'),
    ('El Club de la Pelea', 'Un oficinista aburrido arma un club secreto de peleas.', 139, '+18', 'Drama'),
    ('Spider-Man', 'Un estudiante recibe poderes de una picadura de araña.', 121, '+13', 'Acción'),
    ('Jurassic Park', 'Un parque con dinosaurios clonados sale mal.', 127, '+13', 'Aventura'),
    ('Toy Story', 'Los juguetes de un nene cobran vida cuando nadie los ve.', 81, 'ATP', 'Animación'),
    ('Gladiador', 'Un general romano busca venganza como gladiador.', 155, '+16', 'Acción'),
    ('Shrek 2', 'Shrek conoce a los padres de Fiona.', 93, 'ATP', 'Animación'),
    ('Piratas del Caribe', 'Un pirata y un herrero rescatan a una joven del barco Perla Negra.', 143, '+13', 'Aventura');

-- 6 salas en 3 locales (los ids van del 1 al 6)
INSERT INTO salas (nombre, capacidad, local) VALUES
    ('Sala 1', 80, 'Paradiso Centro'),
    ('Sala 2', 50, 'Paradiso Centro'),
    ('Sala 1', 100, 'Paradiso Norte'),
    ('Sala 2', 60, 'Paradiso Norte'),
    ('Sala 1', 70, 'Paradiso Sur'),
    ('Sala 2', 40, 'Paradiso Sur');


-- 6 servicios
INSERT INTO servicios (nombre, descripcion, precio) VALUES
    ('Balde de pochoclos', '1 balde de pochoclos', 13500.00),
    ('Combo Mega Recargado', '1 balde de pochoclos, 2 gaseosas grandes, 1 golosina y recarga de balde y vasos', 39700.00),
    ('Combo Mega Individual', '1 balde de pochoclos y 1 gaseosa grande', 23400.00),
    ('Agua', '1 agua, valor por unidad', 5200.00),
    ('Estacionamiento', 'Cochera durante la función', 6000.00),
    ('Acceso VIP', 'Butacas reclinables y atención en la sala', 15000.00);


-- 14 funciones (del 4 al 6 de diciembre de 2026)
-- formato: (id_pelicula, id_sala, 'AAAA-MM-DD HH:MM:SS')
INSERT INTO funciones (id_pelicula, id_sala, fecha_hora_proyeccion) VALUES
    (1, 1, '2026-12-04 16:00:00'),
    (2, 1, '2026-12-04 19:00:00'),
    (8, 1, '2026-12-04 21:30:00'),
    (7, 2, '2026-12-04 17:00:00'),
    (4, 2, '2026-12-04 20:00:00'),
    (6, 3, '2026-12-04 18:00:00'),
    (10, 3, '2026-12-04 21:00:00'),
    (5, 4, '2026-12-05 18:00:00'),
    (3, 4, '2026-12-05 21:30:00'),
    (9, 5, '2026-12-05 19:00:00'),
    (10, 1, '2026-12-05 20:00:00'),
    (1, 5, '2026-12-06 17:00:00'),
    (7, 6, '2026-12-06 16:00:00'),
    (8, 6, '2026-12-06 19:30:00');