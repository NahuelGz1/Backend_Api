
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
    precio DECIMAL(10, 2) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
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

-- Compras centrales. Agrupa entradas y servicios en una misma transaccion.
CREATE TABLE compras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

-- Entradas. Estado: 'comprada', 'cancelada' o 'utilizada'
-- La butaca no se puede repetir en la misma función
CREATE TABLE entradas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_compra INT NOT NULL,
    id_funcion INT NOT NULL,
    numero_butaca INT NOT NULL,
    precio_historico DECIMAL(10, 2) NOT NULL,
    codigo_qr VARCHAR(255) UNIQUE NOT NULL,
    estado VARCHAR(20) DEFAULT 'comprada',
    UNIQUE KEY butaca_unica_por_funcion (id_funcion, numero_butaca),
    FOREIGN KEY (id_compra) REFERENCES compras(id),
    FOREIGN KEY (id_funcion) REFERENCES funciones(id)
);

-- Servicios adicionales asociados al mismo ticket de compra
CREATE TABLE detalles_servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_compra INT NOT NULL,
    id_servicio INT NOT NULL,
    cantidad INT DEFAULT 1,
    precio_historico DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (id_compra) REFERENCES compras(id),
    FOREIGN KEY (id_servicio) REFERENCES servicios(id)
);

