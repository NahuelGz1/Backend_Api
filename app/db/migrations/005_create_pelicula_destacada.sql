CREATE TABLE IF NOT EXISTS pelicula_destacada (
    id TINYINT PRIMARY KEY,
    id_pelicula INT NOT NULL,
    FOREIGN KEY (id_pelicula) REFERENCES peliculas(id)
);
