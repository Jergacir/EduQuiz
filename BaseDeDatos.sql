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
  `codigo_visualizacion` VARCHAR(12) DEFAULT NULL,
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

ALTER TABLE partida
ADD COLUMN num_grupos INT NOT NULL DEFAULT 0 
ALTER TABLE partida
ADD COLUMN tipo_partida CHAR(1) NOT NULL DEFAULT 'I';

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



-- 6. TABLA PARTICIPANTE
CREATE TABLE `participante` (
  `participante_id` INT NOT NULL AUTO_INCREMENT,
  `puntuacion_total` NUMERIC(9, 2) NOT NULL DEFAULT 0.00, -- Puntaje total acumulado por el participante
  `cant_preguntas_correctas` INT NOT NULL DEFAULT 0, -- Cantidad de respuestas correctas
  `cant_preguntas_incorrectas` INT NOT NULL DEFAULT 0, -- Cantidad de respuestas incorrectas
  `lider_id` INT NULL, -- FK a sí mismo (participante) si este participante es el líder de su grupo (si la partida tiene grupos)
  `usuario_id` INT NOT NULL, -- FK al usuario registrado que participa (o puede ser null si es invitado)
  `partida_id` INT NOT NULL, -- FK a la partida en la que participa
  
  PRIMARY KEY (`participante_id`),
  
  -- La restricción de líder_id se crea con ON DELETE SET NULL para evitar problemas de borrado.
  -- Si el líder es eliminado, el participante se queda sin líder asignado.
  FOREIGN KEY (`lider_id`) REFERENCES `participante`(`participante_id`) ON DELETE SET NULL, 
  
  -- Asumiendo que existe una tabla 'usuario' con 'usuario_id' como llave primaria
  FOREIGN KEY (`usuario_id`) REFERENCES `usuario`(`usuario_id`), 
  
  FOREIGN KEY (`partida_id`) REFERENCES `partida`(`partida_id`) -- Referencia a la tabla PARTIDA
);
ALTER TABLE participante ADD COLUMN grupo_id INT DEFAULT NULL;
-- 7. TABLA PREGUNTA_PARTICIPANTE
CREATE TABLE `pregunta_participante` (
  `pregunta_participante_id` INT NOT NULL AUTO_INCREMENT,
  `participante_id` INT NOT NULL, -- FK al participante que respondió la pregunta
  `pregunta_id` INT NOT NULL, -- FK a la pregunta que se respondió
  `respuesta_seleccionada_id` INT NULL, -- FK a la respuesta elegida por el participante (puede ser null si no respondió)
  `texto_pregunta` VARCHAR(255) NOT NULL, -- Texto de la pregunta en el momento de la respuesta (para registro histórico)
  `correcta` BOOL NOT NULL, -- Indicador de si la respuesta fue correcta (1 = TRUE, 0 = FALSE)
  `tiempo_pregunta` INT NOT NULL, -- Tiempo que tardó el participante en responder (en segundos o milisegundos, según tu lógica)
  `tiempo_maximo_pregunta` INT NOT NULL, -- Límite de tiempo para la pregunta (para registro histórico)

  PRIMARY KEY (`pregunta_participante_id`),
  
  FOREIGN KEY (`participante_id`) REFERENCES `participante`(`participante_id`), -- Referencia a la tabla PARTICIPANTE
  
  -- Asumiendo que existe una tabla 'pregunta' con 'pregunta_id' como llave primaria
  FOREIGN KEY (`pregunta_id`) REFERENCES `pregunta`(`pregunta_id`), 
  
  -- Asumiendo que existe una tabla 'respuesta' con 'respuesta_id' como llave primaria
  -- La restricción es ON DELETE RESTRICT o NO ACTION para no permitir borrar respuestas que ya fueron seleccionadas.
  FOREIGN KEY (`respuesta_seleccionada_id`) REFERENCES `respuesta`(`respuesta_id`)
);