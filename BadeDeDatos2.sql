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
  `vigencia` BOOLEAN NOT NULL DEFAULT TRUE,
  `url_foto_perfil` VARCHAR(255), -- URL de la foto de perfil
  `url_avatar` VARCHAR(255), -- URL del avatar
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

CREATE TABLE `skins` (
  `skin_id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `url_imagen` VARCHAR(255) NOT NULL,
  `precio` INT UNSIGNED NOT NULL,
  `vigencia` BOOLEAN NOT NULL DEFAULT TRUE, -- Columna añadida del ALTER TABLE
  PRIMARY KEY (`skin_id`)
);

CREATE TABLE `accesorios` (
  `accesorio_id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `url_imagen` VARCHAR(255) NOT NULL,
  `precio` INT UNSIGNED NOT NULL,
  `vigencia` BOOLEAN NOT NULL DEFAULT TRUE, -- Columna añadida del ALTER TABLE
  PRIMARY KEY (`accesorio_id`)
);

CREATE TABLE `cuestionario` (
  `cuestionario_id` INT(11) NOT NULL AUTO_INCREMENT,
  `nombre_cuestionario` VARCHAR(100) NOT NULL,
  `descripcion` VARCHAR(250),
  -- 0=Privado, 1=Público
  `publico` TINYINT(1) NOT NULL DEFAULT 0, 
  -- char(1): 'M'=Múltiple, 'C'=Clásico (Modo de Juego)
  `modo_juego` CHAR(1) NOT NULL,
  `tiempo_limite_pregunta` INT(11) NOT NULL,
  `usuario_id` INT(11) NOT NULL, -- Creador del cuestionario (FK a usuario)
  `url_img_cuestionario` VARCHAR(250),
  `codigo_visualizacion` VARCHAR(12) DEFAULT NULL,
  `estado` BOOLEAN NOT NULL DEFAULT TRUE, -- Columna añadida del ALTER TABLE
  PRIMARY KEY (`cuestionario_id`),
  FOREIGN KEY (`usuario_id`) REFERENCES `usuario`(`usuario_id`) 
    ON DELETE CASCADE ON UPDATE CASCADE
);

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

CREATE TABLE `partida` (
  `partida_id` INT NOT NULL AUTO_INCREMENT,
  `codigo_partida` VARCHAR(6) NOT NULL UNIQUE, -- El código que el usuario ingresa
  `cuestionario_id` INT NOT NULL,              -- FK al cuestionario que se está jugando
  `usuario_creador_id` INT NOT NULL,          -- FK al profesor que creó la partida
  `estado` VARCHAR(20) NOT NULL DEFAULT 'creada', -- 'creada', 'en_juego', 'finalizada'
  `fecha_creacion` DATETIME NOT NULL,
  `num_grupos` INT NOT NULL DEFAULT 0,          -- Columna añadida del ALTER TABLE
  `tipo_partida` CHAR(1) NOT NULL DEFAULT 'I',  -- Columna añadida del ALTER TABLE
  PRIMARY KEY (`partida_id`),
  FOREIGN KEY (`cuestionario_id`) REFERENCES `cuestionario`(`cuestionario_id`),
  FOREIGN KEY (`usuario_creador_id`) REFERENCES `usuario`(`usuario_id`)
);

CREATE TABLE `participante` (
  `participante_id` INT NOT NULL AUTO_INCREMENT,
  `puntuacion_total` NUMERIC(9, 2) NOT NULL DEFAULT 0.00, -- Puntaje total acumulado
  `cant_preguntas_correctas` INT NOT NULL DEFAULT 0,
  `cant_preguntas_incorrectas` INT NOT NULL DEFAULT 0,
  `lider_id` INT NULL, -- FK a sí mismo (participante) si es líder de un grupo
  `usuario_id` INT NOT NULL, -- FK al usuario registrado que participa
  `partida_id` INT NOT NULL, -- FK a la partida
  `grupo_id` INT DEFAULT NULL, -- Columna añadida del ALTER TABLE
  
  PRIMARY KEY (`participante_id`),
  
  FOREIGN KEY (`lider_id`) 
    REFERENCES `participante`(`participante_id`) 
    ON DELETE SET NULL, 
  
  -- Asumiendo que la tabla 'usuario' existe
  FOREIGN KEY (`usuario_id`) 
    REFERENCES `usuario`(`usuario_id`), 
  
  -- Asumiendo que la tabla 'partida' existe
  FOREIGN KEY (`partida_id`) 
    REFERENCES `partida`(`partida_id`)
);

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


-- CAMBIOS SUGERIDOS EN MI BD
-- ================================================================
-- MIGRACIÓN: Mejoras al Sistema de Partidas
-- Fecha: 2025-01-XX
-- ================================================================

-- 1. Agregar campo para controlar índice de pregunta actual
ALTER TABLE partida 
ADD COLUMN pregunta_actual_index INT DEFAULT 0 
COMMENT 'Índice de la pregunta que se está mostrando actualmente (0-based)';

-- 2. Agregar campo para timestamp de inicio de pregunta actual
ALTER TABLE partida 
ADD COLUMN tiempo_inicio_pregunta DATETIME NULL
COMMENT 'Timestamp cuando comenzó la pregunta actual';

-- 3. Agregar campo para contador de respuestas recibidas
ALTER TABLE partida 
ADD COLUMN respuestas_recibidas INT DEFAULT 0
COMMENT 'Contador de respuestas recibidas en la pregunta actual';

-- 4. Mejorar índices para consultas frecuentes
CREATE INDEX idx_partida_estado ON partida(estado);
CREATE INDEX idx_partida_codigo ON partida(codigo_partida);

-- 5. Agregar timestamp de última actualización
ALTER TABLE partida 
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
COMMENT 'Última actualización de la partida';

-- ================================================================
-- PROCEDIMIENTO: Avanzar a la siguiente pregunta
-- ================================================================
DELIMITER $$

CREATE PROCEDURE avanzar_pregunta(
    IN p_codigo_partida VARCHAR(6)
)
BEGIN
    DECLARE v_partida_id INT;
    DECLARE v_total_preguntas INT;
    DECLARE v_index_actual INT;
    
    -- Obtener datos de la partida
    SELECT partida_id, pregunta_actual_index
    INTO v_partida_id, v_index_actual
    FROM partida
    WHERE codigo_partida = p_codigo_partida;
    
    -- Contar preguntas del cuestionario
    SELECT COUNT(*)
    INTO v_total_preguntas
    FROM pregunta p
    JOIN partida pa ON p.cuestionario_id = pa.cuestionario_id
    WHERE pa.partida_id = v_partida_id;
    
    -- Si hay más preguntas, avanzar
    IF v_index_actual + 1 < v_total_preguntas THEN
        UPDATE partida
        SET 
            pregunta_actual_index = pregunta_actual_index + 1,
            respuestas_recibidas = 0,
            tiempo_inicio_pregunta = NOW(),
            estado = 'en_curso'
        WHERE partida_id = v_partida_id;
    ELSE
        -- No hay más preguntas, finalizar partida
        UPDATE partida
        SET estado = 'finalizada'
        WHERE partida_id = v_partida_id;
    END IF;
    
END$$

DELIMITER ;

-- ================================================================
-- VISTA: Estado completo de partida para polling
-- ================================================================
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

-- ================================================================
-- FUNCIÓN: Verificar si todos respondieron
-- ================================================================
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

-- ================================================================
-- DATOS DE PRUEBA (opcional)
-- ================================================================

-- Actualizar partidas existentes con valores por defecto
UPDATE partida 
SET 
    pregunta_actual_index = 0,
    respuestas_recibidas = 0,
    tiempo_inicio_pregunta = NULL
WHERE pregunta_actual_index IS NULL;


-- TRIGERRR
--EL TRIGGER QUE SE EJECUTA PARA QUE SE COPIE LOS RESULTADOS DEL LIDER:ESTE SE EJCUTA INTERNAMENTE:
-- NO SÉ SI EL TRIGGER ESTÁ BIEN 

CREATE TRIGGER replicar_respuesta_lider
AFTER INSERT ON PREGUNTA_PARTICIPANTE
FOR EACH ROW
BEGIN
    
    -- 1. VERIFICAR si el participante que acaba de insertar (NEW.participante_id) es un líder.
    IF (SELECT p.lider_id FROM PARTICIPANTE p WHERE p.participante_id = NEW.participante_id) = NEW.participante_id THEN
        
        -- 2. Replicar la respuesta a los seguidores (COPIAR TODOS LOS DATOS)
        INSERT INTO PREGUNTA_PARTICIPANTE
            (
                participante_id,
                texto_pregunta, 
                correcta, 
                tiempo_respuesta, 
                pregunta_id, 
                respuesta_seleccionada_id
            )
        SELECT
            p.participante_id,      
            NEW.texto_pregunta,     
            NEW.correcta,           
            NEW.tiempo_respuesta,   
            NEW.pregunta_id,        
            NEW.respuesta_seleccionada_id
        FROM PARTICIPANTE p
        WHERE
            p.lider_id = NEW.participante_id  
            AND p.participante_id != NEW.participante_id; 
    
    END IF;

END$$

DELIMITER ;
