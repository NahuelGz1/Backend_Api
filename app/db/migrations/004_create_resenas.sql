-- Ejecutar sobre la base de datos seleccionada de una instalación existente.
CREATE TABLE IF NOT EXISTS reseñas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_pelicula INT NOT NULL,
    puntuacion INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY (id_pelicula) REFERENCES peliculas(id),
    UNIQUE KEY (id_usuario, id_pelicula)
);
