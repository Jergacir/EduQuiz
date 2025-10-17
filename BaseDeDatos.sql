CREATE TABLE `usuario` (
  `usuario_id` INT(11) NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(100) NOT NULL UNIQUE,
  `nombre` VARCHAR(100) NOT NULL,
  `contrasena` VARCHAR(100) NOT NULL,
  `correo` VARCHAR(100) NOT NULL UNIQUE,
  `dni` CHAR(8) NOT NULL UNIQUE,
  `tipo_usuario` CHAR(1) NOT NULL CHECK (`tipo_usuario` IN ('A', 'P', 'G')), -- A(Alumno), P(Profesor) y G(Gestor)
  `cant_monedas` INT(11) NOT NULL,
  `verificado` INT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`usuario_id`)
);

-- Tabla temporal para almacenar registros antes de verificar el email
CREATE TABLE IF NOT EXISTS `registro_temp` (
  `temp_id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(100) NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `contrasena` VARCHAR(200) NOT NULL,
  `correo` VARCHAR(100) NOT NULL,
  `dni` CHAR(8) NOT NULL,
  `tipo_usuario` CHAR(1) NOT NULL,
  `cant_monedas` INT NOT NULL DEFAULT 0,
  `verification_code` VARCHAR(10) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`temp_id`)
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


--Alter necesarios para dar de baja
-- ##############################################
-- 1. ALTER TABLE para la tabla USUARIO
-- ##############################################

ALTER TABLE `usuario`
ADD COLUMN `vigencia` BOOLEAN NOT NULL DEFAULT TRUE;

-- Comentario: Este campo indica si el usuario está activo o ha sido desactivado (soft delete).


-- ##############################################
-- 2. ALTER TABLE para la tabla SKINS
-- ##############################################

ALTER TABLE `skins`
ADD COLUMN `vigencia` BOOLEAN NOT NULL DEFAULT TRUE;

-- Comentario: Este campo indica si el skin está disponible para la compra/uso en la tienda.


-- ##############################################
-- 3. ALTER TABLE para la tabla ACCESORIOS
-- ##############################################

ALTER TABLE `accesorios`
ADD COLUMN `vigencia` BOOLEAN NOT NULL DEFAULT TRUE;


-- 2. TABLA CUESTIONARIO
CREATE TABLE `cuestionario` (
  `cuestionario_id` INT(11) NOT NULL AUTO_INCREMENT,
  `nombre_cuestionario` VARCHAR(100) NOT NULL,
  `descripcion` VARCHAR(250),
  -- 0=Privado, 1=Público (Corresponde al campo 'publico' bool/tinyint)
  `publico` TINYINT(1) NOT NULL DEFAULT 0, 
  -- char(1): 'M'=Múltiple, 'C'=Clásico (Modo de Juego)
  `modo_juego` CHAR(1) NOT NULL,
  `tiempo_limite_pregunta` INT(11) NOT NULL,
  `usuario_id` INT(11) NOT NULL, -- Creador del cuestionario (FK a usuario)
  `url_img_cuestionario` VARCHAR(250),
  PRIMARY KEY (`cuestionario_id`),
  FOREIGN KEY (`usuario_id`) REFERENCES `usuario`(`usuario_id`) 
    ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE `cuestionario`
ADD COLUMN `estado` BOOLEAN NOT NULL DEFAULT TRUE;

-- 3. TABLA PREGUNTA
CREATE TABLE `pregunta` (
  `pregunta_id` INT(11) NOT NULL AUTO_INCREMENT,
  `texto_pregunta` VARCHAR(100) NOT NULL,
  `media_url` VARCHAR(255), -- URL de imagen/video/audio
  `tiempo_limite` INT(11),
  `cuestionario_id` INT(11) NOT NULL, -- FK a cuestionario
  PRIMARY KEY (`pregunta_id`),
  FOREIGN KEY (`cuestionario_id`) REFERENCES `cuestionario`(`cuestionario_id`) 
    ON DELETE CASCADE ON UPDATE CASCADE
);

-- 4. TABLA RESPUESTA
CREATE TABLE `respuesta` (
  `respuesta_id` INT(11) NOT NULL AUTO_INCREMENT,
  `texto_respuesta` VARCHAR(100) NOT NULL,
  -- 0=Incorrecta, 1=Correcta (Corresponde al campo 'estado_respuesta' bool/tinyint)
  `estado_respuesta` TINYINT(1) NOT NULL, 
  `pregunta_id` INT(11) NOT NULL, -- FK a pregunta
  PRIMARY KEY (`respuesta_id`),
  FOREIGN KEY (`pregunta_id`) REFERENCES `pregunta`(`pregunta_id`) 
    ON DELETE CASCADE ON UPDATE CASCADE
);

-- 5. TABLA PARTIDA (Juego Activo)
CREATE TABLE `partida` (
  `partida_id` INT NOT NULL AUTO_INCREMENT,
  `codigo_partida` VARCHAR(6) NOT NULL UNIQUE, -- El código que el usuario ingresa
  `cuestionario_id` INT NOT NULL,            -- FK al cuestionario que se está jugando
  `usuario_creador_id` INT NOT NULL,         -- FK al profesor que creó la partida
  `estado` VARCHAR(20) NOT NULL DEFAULT 'creada', -- 'creada', 'en_juego', 'finalizada'
  `fecha_creacion` DATETIME NOT NULL,
  PRIMARY KEY (`partida_id`),
  FOREIGN KEY (`cuestionario_id`) REFERENCES `cuestionario`(`cuestionario_id`),
  FOREIGN KEY (`usuario_creador_id`) REFERENCES `usuario`(`usuario_id`)
);

-- 6. TABLA PARTICIPANTE_PARTIDA (Relación Usuario-Partida)
CREATE TABLE `participante_partida` (
  `participante_id` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NOT NULL,
  `partida_id` INT NOT NULL,
  `puntuacion` INT NOT NULL DEFAULT 0,
  `fecha_union` DATETIME NOT NULL,
  PRIMARY KEY (`participante_id`),
  UNIQUE KEY `idx_usuario_partida` (`usuario_id`, `partida_id`), -- Un usuario solo puede estar una vez en una partida
  FOREIGN KEY (`usuario_id`) REFERENCES `usuario`(`usuario_id`),
  FOREIGN KEY (`partida_id`) REFERENCES `partida`(`partida_id`)
);

	INSERT INTO `skins` (`nombre`, `url_imagen`, `precio`, `vigencia` ) VALUES
	('Skin Ingeniero Civil', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214821/Ingeniero-Civil128x128.png_pnf3ts.png', 250, 1), -- Ejemplo adicional
	('Skin Administrador', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214817/Administrador-1.png_yx2uzf.png', 250, 1), -- Ejemplo adicional
	('Skin Abogado', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214817/Abogado-1.png_ezmvx6.png', 250,1), -- Ejemplo adicional
	('Skin Hacker', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214817/Hacker-1.png_zlyogm.png', 300,1), -- Ejemplo adicional
	('Skin Doctor', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214816/medico-1.png_tqmr1v.png', 350,1); -- Ejemplo adicional
	-- Insertando datos en la tabla 'accesorios'
	INSERT INTO `accesorios` (`nombre`, `url_imagen`, `precio`, `vigencia`) VALUES
	('Peluca Rubia', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214821/pelucaRubia_ftqdqz.png', 50,1),
	('Simbionte', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214822/poloVenom_l06da3.png', 150,1),
	('Super Polo', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214821/PoloSuperman_xgwvpe.png', 180,1), -- Ejemplo adicional
	('Lentes Cool', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214824/lentesSol_bz4bbt.png', 80,1), -- Ejemplo adicional
	('Sombrero Luffy', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214817/sombreroOnepiece_h2zf0c.png', 120,1); -- Ejemplo adicional

-- Tabla para tokens de restablecimiento de contraseña
CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
  `prt_id` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NOT NULL,
  `token_hash` VARCHAR(255) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`prt_id`),
  FOREIGN KEY (`usuario_id`) REFERENCES `usuario`(`usuario_id`) ON DELETE CASCADE
);
