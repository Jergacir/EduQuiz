CREATE TABLE `usuario` (
  `usuario_id` INT(11) NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(100) NOT NULL UNIQUE,
  `nombre` VARCHAR(100) NOT NULL,
  `contrasena` VARCHAR(100) NOT NULL,
  `correo` VARCHAR(100) NOT NULL UNIQUE,
  `dni` CHAR(8) NOT NULL UNIQUE,
  `tipo_usuario` CHAR(1) NOT NULL CHECK (`tipo_usuario` IN ('A', 'P', 'G')), -- A(Alumno), P(Profesor) y G(Gestor)
  `cant_monedas` INT(11) NOT NULL,
  PRIMARY KEY (`usuario_id`)
);

¡Excelente idea! Hacer la tienda dinámica es el siguiente paso lógico.

Aquí tienes el script SQL para crear las dos tablas que pediste, skins y accesorios, en tu base de datos de XAMPP (MySQL). El script también incluye algunos datos de ejemplo para que puedas empezar a probar de inmediato.

📦 Script SQL para la Tienda
Este código creará las tablas y las llenará con los ítems que tenías en tu diseño.

SQL

-- ##############################################
-- TABLA PARA LAS APARIENCIAS (SKINS)
-- Almacena los avatares o temas que el usuario puede comprar.
-- ##############################################

CREATE TABLE `skins` (
  `skin_id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `url_imagen` VARCHAR(255) NOT NULL,
  `precio` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`skin_id`)
);


-- ##############################################
-- TABLA PARA LOS ACCESORIOS DE LAS SKINS
-- 
-- ##############################################

CREATE TABLE `accesorios` (
  `accesorio_id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `url_imagen` VARCHAR(255) NOT NULL,
  `precio` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`accesorio_id`)
);


--Insert opcionales
-- Insertando datos en la tabla 'skins'
INSERT INTO `skins` (`nombre`, `url_imagen`, `precio`) VALUES
('Avatar Dinosaurio', 'https://i.imgur.com/e2O5RUy.png', 100),
('Avatar Astronauta', 'https://i.imgur.com/7g21MMa.png', 150),
('Avatar Ninja', 'https://i.imgur.com/URL_AVATAR_NINJA.png', 250); -- Ejemplo adicional

-- Insertando datos en la tabla 'accesorios'
INSERT INTO `accesorios` (`nombre`, `url_imagen`, `precio`) VALUES
('Gorro kawai', 'https://i.imgur.com/lJ4xFwR.png', 50),
('Lentes Hot', 'https://i.imgur.com/SQLJ21a.png', 200),
('Zapatos cute', 'https://i.imgur.com/URL_POTENCIADOR_5050.png', 120); -- Ejemplo adicional