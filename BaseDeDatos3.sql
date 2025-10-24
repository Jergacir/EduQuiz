-- ================================================================
-- 1. TABLAS "PADRE" (Sin dependencias)
-- ================================================================

-- Definición unificada de USUARIO (usamos la versión detallada)
CREATE TABLE `usuario` (
  `usuario_id` INT(11) NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(100) NOT NULL UNIQUE,
  `nombre` VARCHAR(100) NOT NULL,
  `contrasena` VARCHAR(100) NOT NULL,
  `correo` VARCHAR(100) NOT NULL UNIQUE,
  `dni` CHAR(8) NOT NULL UNIQUE,
  `tipo_usuario` CHAR(1) NOT NULL CHECK (`tipo_usuario` IN ('A', 'P', 'G')),
  `cant_monedas` INT(11) NOT NULL,
  `verificado` INT(1) NOT NULL DEFAULT 0,
  `vigencia` BOOLEAN NOT NULL DEFAULT TRUE,
  `url_foto_perfil` VARCHAR(255),
  `url_avatar` VARCHAR(255),
  PRIMARY KEY (`usuario_id`)
);

-- Tabla de Tipos de Accesorio
CREATE TABLE `tipo_accesorio` (
  `id_tipo_accesorio` INT PRIMARY KEY,
  `nombre_tipo` VARCHAR(100) NOT NULL
);

-- ================================================================
-- 2. TABLAS "HIJO" (Con dependencias)
-- ================================================================

-- Definición unificada de SKIN
CREATE TABLE `skin` (
  `skin_id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `url_imagen` VARCHAR(255) NOT NULL,
  `precio` INT UNSIGNED NOT NULL,
  `vigencia` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`skin_id`)
);

-- CORREGIDO: Definición unificada de ACCESORIO
-- Se incluye 'id_tipo_accesorio' y la FK desde el inicio.
CREATE TABLE `accesorio` (
  `accesorio_id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `url_imagen` VARCHAR(255) NOT NULL,
  `precio` INT UNSIGNED NOT NULL,
  `vigencia` BOOLEAN NOT NULL DEFAULT TRUE,
  `id_tipo_accesorio` INT NOT NULL, -- CORRECCIÓN: Añadido aquí
  PRIMARY KEY (`accesorio_id`),
  CONSTRAINT `fk_accesorio_tipo` -- CORRECCIÓN: FK añadida aquí
    FOREIGN KEY (`id_tipo_accesorio`)
    REFERENCES `tipo_accesorio`(`id_tipo_accesorio`)
);

-- Tabla intermedia Skin-Accesorio
-- CORREGIDO: Referencias a 'accesorio' y 'skin' (minúsculas)
CREATE TABLE `SkinAccesorio` (
  `id_accesorio` INT NOT NULL,
  `id_skin` INT NOT NULL,
  `default_accesorio` BOOLEAN,
  PRIMARY KEY (`id_accesorio`, `id_skin`),
  FOREIGN KEY (`id_accesorio`) REFERENCES `accesorio`(`accesorio_id`),
  FOREIGN KEY (`id_skin`) REFERENCES `skin`(`skin_id`)
);
ALTER TABLE `skin`
ADD `categoria` CHAR(1) NOT NULL
CHECK (`categoria` IN ('N', 'E', 'L'))
AFTER `skinDefault`;

ALTER TABLE `skin`
ADD `categoria` CHAR(1) NOT NULL
CHECK (`categoria` IN ('N', 'E', 'L'))
AFTER `skinDefault`;
-- Tabla Inventario
-- CORREGIDO: Referencia a 'usuario' (minúscula)
CREATE TABLE `Inventario` (
  `id_inventario` INT PRIMARY KEY,
  `usuario_id` INT NOT NULL,
  `equipada` BOOLEAN,
  `fecha_adquisicion` DATE,
  `id_item` INT NOT NULL,
  `tipo_item` VARCHAR(20) NOT NULL,
  FOREIGN KEY (`usuario_id`) REFERENCES `usuario`(`usuario_id`),
  CHECK (tipo_item IN ('SKIN', 'ACCESORIO'))
);

-- Tablas del sistema de Cuestionarios
CREATE TABLE `cuestionario` (
  `cuestionario_id` INT(11) NOT NULL AUTO_INCREMENT,
  `nombre_cuestionario` VARCHAR(100) NOT NULL,
  `descripcion` VARCHAR(250),
  `publico` TINYINT(1) NOT NULL DEFAULT 0, 
  `modo_juego` CHAR(1) NOT NULL,
  `tiempo_limite_pregunta` INT(11) NOT NULL,
  `usuario_id` INT(11) NOT NULL,
  `url_img_cuestionario` VARCHAR(250),
  `codigo_visualizacion` VARCHAR(12) DEFAULT NULL,
  `estado` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`cuestionario_id`),
  FOREIGN KEY (`usuario_id`) REFERENCES `usuario`(`usuario_id`) 
    ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE `pregunta` (
  `pregunta_id` INT(11) NOT NULL AUTO_INCREMENT,
  `texto_pregunta` VARCHAR(100) NOT NULL,
  `media_url` VARCHAR(255),
  `tiempo_limite` INT(11),
  `cuestionario_id` INT(11) NOT NULL,
  PRIMARY KEY (`pregunta_id`),
  FOREIGN KEY (`cuestionario_id`) REFERENCES `cuestionario`(`cuestionario_id`) 
    ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE `respuesta` (
  `respuesta_id` INT(11) NOT NULL AUTO_INCREMENT,
  `texto_respuesta` VARCHAR(100) NOT NULL,
  `estado_respuesta` TINYINT(1) NOT NULL, 
  `pregunta_id` INT(11) NOT NULL,
  PRIMARY KEY (`respuesta_id`),
  FOREIGN KEY (`pregunta_id`) REFERENCES `pregunta`(`pregunta_id`) 
    ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tablas del sistema de Partidas
CREATE TABLE `partida` (
  `partida_id` INT NOT NULL AUTO_INCREMENT,
  `codigo_partida` VARCHAR(6) NOT NULL UNIQUE,
  `cuestionario_id` INT NOT NULL,
  `usuario_creador_id` INT NOT NULL,
  `estado` VARCHAR(20) NOT NULL DEFAULT 'creada',
  `fecha_creacion` DATETIME NOT NULL,
  `num_grupos` INT NOT NULL DEFAULT 0,
  `tipo_partida` CHAR(1) NOT NULL DEFAULT 'I',
  PRIMARY KEY (`partida_id`),
  FOREIGN KEY (`cuestionario_id`) REFERENCES `cuestionario`(`cuestionario_id`),
  FOREIGN KEY (`usuario_creador_id`) REFERENCES `usuario`(`usuario_id`)
);

CREATE TABLE `participante` (
  `participante_id` INT NOT NULL AUTO_INCREMENT,
  `puntuacion_total` NUMERIC(9, 2) NOT NULL DEFAULT 0.00,
  `cant_preguntas_correctas` INT NOT NULL DEFAULT 0,
  `cant_preguntas_incorrectas` INT NOT NULL DEFAULT 0,
  `lider_id` INT NULL,
  `usuario_id` INT NOT NULL,
  `partida_id` INT NOT NULL,
  `grupo_id` INT DEFAULT NULL,
  PRIMARY KEY (`participante_id`),
  FOREIGN KEY (`lider_id`) REFERENCES `participante`(`participante_id`) ON DELETE SET NULL, 
  FOREIGN KEY (`usuario_id`) REFERENCES `usuario`(`usuario_id`), 
  FOREIGN KEY (`partida_id`) REFERENCES `partida`(`partida_id`)
);

CREATE TABLE `pregunta_participante` (
  `pregunta_participante_id` INT NOT NULL AUTO_INCREMENT,
  `participante_id` INT NOT NULL,
  `pregunta_id` INT NOT NULL,
  `respuesta_seleccionada_id` INT NULL,
  `texto_pregunta` VARCHAR(255) NOT NULL,
  `correcta` BOOL NOT NULL,
  `tiempo_pregunta` INT NOT NULL,
  `tiempo_maximo_pregunta` INT NOT NULL,
  PRIMARY KEY (`pregunta_participante_id`),
  FOREIGN KEY (`participante_id`) REFERENCES `participante`(`participante_id`),
  FOREIGN KEY (`pregunta_id`) REFERENCES `pregunta`(`pregunta_id`), 
  FOREIGN KEY (`respuesta_seleccionada_id`) REFERENCES `respuesta`(`respuesta_id`)
);

-- Tablas de soporte (registro y tokens)
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

CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
  `prt_id` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NOT NULL,
  `token_hash` VARCHAR(255) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`prt_id`),
  FOREIGN KEY (`usuario_id`) REFERENCES `usuario`(`usuario_id`) ON DELETE CASCADE
);

-- ================================================================
-- 3. VISTA (Inventario Completo)
-- ================================================================

-- CORREGIDO: Vista actualizada para usar 'skin' y 'accesorio'
CREATE VIEW Inventario_Completo AS
SELECT
    I.id_inventario,
    I.usuario_id,
    I.equipada,
    I.fecha_adquisicion,
    I.id_item,
    I.tipo_item,
    S.nombre AS nombre_item,
    S.url_imagen AS url_imagen_base,
    NULL AS id_tipo_accesorio,
    NULL AS nombre_tipo_accesorio
FROM
    Inventario I
JOIN
    `skin` S ON I.id_item = S.skin_id -- Corregido
WHERE
    I.tipo_item = 'SKIN'

UNION ALL

SELECT
    I.id_inventario,
    I.usuario_id,
    I.equipada,
    I.fecha_adquisicion,
    I.id_item,
    I.tipo_item,
    A.nombre AS nombre_item,
    A.url_imagen AS url_imagen_base,
    TA.id_tipo_accesorio,
    TA.nombre_tipo AS nombre_tipo_accesorio
FROM
    Inventario I
JOIN
    `accesorio` A ON I.id_item = A.accesorio_id -- Corregido
JOIN
    `tipo_accesorio` TA ON A.id_tipo_accesorio = TA.id_tipo_accesorio -- Corregido
WHERE
    I.tipo_item = 'ACCESORIO';

-- ================================================================
-- 4. DATOS DE PRUEBA (INSERTS)
-- ================================================================

-- Usuarios
INSERT INTO `usuario`
  (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verificado, vigencia)
VALUES
  ('profe', 'Profesor Ejemplo', '$2b$12$8sbg23vMlHwjMYJrqiISj.ybiuyO2hMErhplxpjPmst5zmjwSmwgi', 'profe@gmail.com', '12345678', 'P', 0, 1, 1);

INSERT INTO `usuario`
  (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verificado, vigencia)
VALUES
  ('gestor', 'Gestor Ejemplo', '<HASH_BCRYPT>', 'gestor@example.com', '87654321', 'G', 0, 1, 1);

-- Tipos de Accesorio (NECESARIOS PARA LOS ACCESORIOS)
-- ¡Debes insertar aquí los tipos ANTES que los accesorios!
INSERT INTO `tipo_accesorio` (id_tipo_accesorio, nombre_tipo) VALUES
(1, 'Cabello'),
(2, 'Ropa'),
(3, 'Ropa'),
(4, 'Lentes'),
(5, 'Sombrero');

-- Skins (CORREGIDO: insertando en 'skin')
INSERT INTO `skin` (`nombre`, `url_imagen`, `precio`, `vigencia` ) VALUES
('Skin Ingeniero Civil', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214821/Ingeniero-Civil128x128.png_pnf3ts.png', 250, 1),
('Skin Administrador', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214817/Administrador-1.png_yx2uzf.png', 250, 1),
('Skin Abogado', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214817/Abogado-1.png_ezmvx6.png', 250,1),
('Skin Hacker', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214817/Hacker-1.png_zlyogm.png', 300,1),
('Skin Doctor', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214816/medico-1.png_tqmr1v.png', 350,1);

-- Accesorios (CORREGIDO: insertando en 'accesorio' y añadiendo el 'id_tipo_accesorio')
INSERT INTO `accesorio` (`nombre`, `url_imagen`, `precio`, `vigencia`, `id_tipo_accesorio`) VALUES
('Peluca Rubia', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214821/pelucaRubia_ftqdqz.png', 50, 1, 1),
('Simbionte', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214822/poloVenom_l06da3.png', 150, 1, 2),
('Super Polo', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214821/PoloSuperman_xgwvpe.png', 180, 1, 3),
('Lentes Cool', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214824/lentesSol_bz4bbt.png', 80, 1, 4),
('Sombrero Luffy', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214817/sombreroOnepiece_h2zf0c.png', 120, 1, 5);

-- ================================================================
-- 5. MIGRACIONES Y LÓGICA (Procedimientos, Triggers)
-- ================================================================

-- Mejoras al Sistema de Partidas
ALTER TABLE partida 
ADD COLUMN `pregunta_actual_index` INT DEFAULT 0 
COMMENT 'Índice de la pregunta que se está mostrando actualmente (0-based)';

ALTER TABLE partida 
ADD COLUMN `tiempo_inicio_pregunta` DATETIME NULL
COMMENT 'Timestamp cuando comenzó la pregunta actual';

ALTER TABLE partida 
ADD COLUMN `respuestas_recibidas` INT DEFAULT 0
COMMENT 'Contador de respuestas recibidas en la pregunta actual';

ALTER TABLE partida 
ADD COLUMN `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
COMMENT 'Última actualización de la partida';

-- Índices
CREATE INDEX idx_partida_estado ON partida(estado);
CREATE INDEX idx_partida_codigo ON partida(codigo_partida);

-- Procedimiento: Avanzar a la siguiente pregunta
DELIMITER $$
CREATE PROCEDURE avanzar_pregunta(
    IN p_codigo_partida VARCHAR(6)
)
BEGIN
    DECLARE v_partida_id INT;
    DECLARE v_total_preguntas INT;
    DECLARE v_index_actual INT;
    
    SELECT partida_id, pregunta_actual_index
    INTO v_partida_id, v_index_actual
    FROM partida
    WHERE codigo_partida = p_codigo_partida;
    
    SELECT COUNT(*)
    INTO v_total_preguntas
    FROM pregunta p
    JOIN partida pa ON p.cuestionario_id = pa.cuestionario_id
    WHERE pa.partida_id = v_partida_id;
    
    IF v_index_actual + 1 < v_total_preguntas THEN
        UPDATE partida
        SET 
            pregunta_actual_index = pregunta_actual_index + 1,
            respuestas_recibidas = 0,
            tiempo_inicio_pregunta = NOW(),
            estado = 'en_curso'
        WHERE partida_id = v_partida_id;
    ELSE
        UPDATE partida
        SET estado = 'finalizada'
        WHERE partida_id = v_partida_id;
    END IF;
    
END$$
DELIMITER ;

-- Vista: Estado completo de partida
CREATE OR REPLACE VIEW vista_estado_partida AS
SELECT 
    pa.partida_id,
    pa.codigo_partida,
    pa.estado,
    pa.pregunta_actual_index,
    pa.respuestas_recibidas,
    pa.tiempo_inicio_pregunta,
    pa.updated_at,
    c.cuestionario_id,
    c.nombre_cuestionario,
    COUNT(DISTINCT part.participante_id) as total_participantes,
    (SELECT COUNT(*) FROM pregunta WHERE cuestionario_id = c.cuestionario_id) as total_preguntas
FROM partida pa
JOIN cuestionario c ON pa.cuestionario_id = c.cuestionario_id
LEFT JOIN participante part ON pa.partida_id = part.partida_id
GROUP BY pa.partida_id;

-- Función: Verificar si todos respondieron
DELIMITER $$
CREATE FUNCTION todos_respondieron(p_codigo_partida VARCHAR(6))
RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    DECLARE v_total_participantes INT;
    DECLARE v_respuestas_recibidas INT;
    
    SELECT COUNT(DISTINCT part.participante_id), pa.respuestas_recibidas
    INTO v_total_participantes, v_respuestas_recibidas
    FROM partida pa
    LEFT JOIN participante part ON pa.partida_id = part.partida_id
    WHERE pa.codigo_partida = p_codigo_partida
    GROUP BY pa.partida_id;
    
    RETURN v_respuestas_recibidas >= v_total_participantes;
END$$
DELIMITER ;

-- Trigger: Replicar respuesta del líder
DELIMITER $$
DROP TRIGGER IF EXISTS replicar_respuesta_lider$$

CREATE TRIGGER replicar_respuesta_lider
AFTER INSERT ON pregunta_participante
FOR EACH ROW
BEGIN
    DECLARE v_es_lider INT DEFAULT 0;
    
    SELECT COUNT(*) INTO v_es_lider
    FROM participante
    WHERE participante_id = NEW.participante_id
      AND lider_id = participante_id;
    
    IF v_es_lider > 0 THEN
        INSERT INTO pregunta_participante (
            participante_id,
            pregunta_id,
            respuesta_seleccionada_id,
            texto_pregunta,
            correcta,
            tiempo_pregunta,
            tiempo_maximo_pregunta
        )
        SELECT 
            p.participante_id,
            NEW.pregunta_id,
            NEW.respuesta_seleccionada_id,
            NEW.texto_pregunta,
            NEW.correcta,
            NEW.tiempo_pregunta,
            NEW.tiempo_maximo_pregunta
        FROM participante p
        WHERE p.lider_id = NEW.participante_id
          AND p.participante_id != NEW.participante_id
          AND NOT EXISTS (
              SELECT 1 FROM pregunta_participante pp
              WHERE pp.participante_id = p.participante_id
                AND pp.pregunta_id = NEW.pregunta_id
          );
    END IF;
END$$
DELIMITER ;