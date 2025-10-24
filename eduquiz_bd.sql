-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1:3339
-- Tiempo de generación: 24-10-2025 a las 08:27:06
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `eduquiz_bd`
--

DELIMITER $$
--
-- Procedimientos
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `avanzar_pregunta` (IN `p_codigo_partida` VARCHAR(6))   BEGIN
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

--
-- Funciones
--
CREATE DEFINER=`root`@`localhost` FUNCTION `todos_respondieron` (`p_codigo_partida` VARCHAR(6)) RETURNS TINYINT(1) DETERMINISTIC BEGIN
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

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `accesorio`
--

CREATE TABLE `accesorio` (
  `accesorio_id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `url_imagen` varchar(255) NOT NULL,
  `precio` int(10) UNSIGNED NOT NULL,
  `vigencia` tinyint(1) NOT NULL DEFAULT 1,
  `id_tipo_accesorio` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cuestionario`
--

CREATE TABLE `cuestionario` (
  `cuestionario_id` int(11) NOT NULL,
  `nombre_cuestionario` varchar(100) NOT NULL,
  `descripcion` varchar(250) DEFAULT NULL,
  `publico` tinyint(1) NOT NULL DEFAULT 0,
  `modo_juego` char(1) NOT NULL,
  `tiempo_limite_pregunta` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `url_img_cuestionario` varchar(250) DEFAULT NULL,
  `codigo_visualizacion` varchar(12) DEFAULT NULL,
  `estado` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inventario`
--

CREATE TABLE `inventario` (
  `id_inventario` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `equipada` tinyint(1) DEFAULT NULL,
  `fecha_adquisicion` date DEFAULT NULL,
  `id_item` int(11) NOT NULL,
  `tipo_item` varchar(20) NOT NULL
) ;

--
-- Volcado de datos para la tabla `inventario`
--

INSERT INTO `inventario` (`id_inventario`, `usuario_id`, `equipada`, `fecha_adquisicion`, `id_item`, `tipo_item`) VALUES
(1, 3, 0, '2025-10-23', 2, 'ACCESORIO'),
(1001, 1, 1, '2025-10-20', 4, 'SKIN'),
(1002, 1, 1, '2025-10-21', 4, 'ACCESORIO'),
(1003, 1, 0, '2025-10-22', 5, 'ACCESORIO'),
(1004, 2, 1, '2025-10-23', 1, 'SKIN'),
(1006, 3, 0, '2025-10-21', 4, 'ACCESORIO'),
(1007, 3, 0, '2025-10-22', 5, 'ACCESORIO'),
(1008, 3, 0, '2025-10-23', 1, 'SKIN'),
(1010, 3, 0, '2025-10-20', 4, 'SKIN'),
(1011, 3, 0, '2025-10-23', 3, 'ACCESORIO'),
(1012, 3, 0, '2025-10-23', 1, 'ACCESORIO'),
(1013, 3, 0, '2025-10-23', 2, 'SKIN'),
(1014, 3, 0, '2025-10-23', 3, 'SKIN'),
(1016, 3, 0, '2025-10-23', 5, 'SKIN'),
(1017, 3, 0, '2025-10-23', 15, 'SKIN'),
(1018, 3, 1, '2025-10-24', 14, 'SKIN'),
(1019, 3, 0, '2025-10-24', 7, 'SKIN'),
(1020, 3, 0, '2025-10-24', 10, 'SKIN'),
(1021, 3, 0, '2025-10-24', 12, 'SKIN');

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `inventario_completo`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `inventario_completo` (
`id_inventario` int(11)
,`usuario_id` int(11)
,`equipada` tinyint(4)
,`fecha_adquisicion` date
,`id_item` int(11)
,`tipo_item` varchar(20)
,`nombre_item` varchar(100)
,`url_imagen_base` varchar(255)
,`id_tipo_accesorio` int(11)
,`nombre_tipo_accesorio` varchar(100)
);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `participante`
--

CREATE TABLE `participante` (
  `participante_id` int(11) NOT NULL,
  `puntuacion_total` decimal(9,2) NOT NULL DEFAULT 0.00,
  `cant_preguntas_correctas` int(11) NOT NULL DEFAULT 0,
  `cant_preguntas_incorrectas` int(11) NOT NULL DEFAULT 0,
  `lider_id` int(11) DEFAULT NULL,
  `usuario_id` int(11) NOT NULL,
  `partida_id` int(11) NOT NULL,
  `grupo_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `partida`
--

CREATE TABLE `partida` (
  `partida_id` int(11) NOT NULL,
  `codigo_partida` varchar(6) NOT NULL,
  `cuestionario_id` int(11) NOT NULL,
  `usuario_creador_id` int(11) NOT NULL,
  `estado` varchar(20) NOT NULL DEFAULT 'creada',
  `fecha_creacion` datetime NOT NULL,
  `num_grupos` int(11) NOT NULL DEFAULT 0,
  `tipo_partida` char(1) NOT NULL DEFAULT 'I',
  `pregunta_actual_index` int(11) DEFAULT 0 COMMENT 'Índice de la pregunta que se está mostrando actualmente (0-based)',
  `tiempo_inicio_pregunta` datetime DEFAULT NULL COMMENT 'Timestamp cuando comenzó la pregunta actual',
  `respuestas_recibidas` int(11) DEFAULT 0 COMMENT 'Contador de respuestas recibidas en la pregunta actual',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT 'Última actualización de la partida'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `password_reset_tokens`
--

CREATE TABLE `password_reset_tokens` (
  `prt_id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `token_hash` varchar(255) NOT NULL,
  `expires_at` datetime NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pregunta`
--

CREATE TABLE `pregunta` (
  `pregunta_id` int(11) NOT NULL,
  `texto_pregunta` varchar(100) NOT NULL,
  `media_url` varchar(255) DEFAULT NULL,
  `tiempo_limite` int(11) DEFAULT NULL,
  `cuestionario_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pregunta_participante`
--

CREATE TABLE `pregunta_participante` (
  `pregunta_participante_id` int(11) NOT NULL,
  `participante_id` int(11) NOT NULL,
  `pregunta_id` int(11) NOT NULL,
  `respuesta_seleccionada_id` int(11) DEFAULT NULL,
  `texto_pregunta` varchar(255) NOT NULL,
  `correcta` tinyint(1) NOT NULL,
  `tiempo_pregunta` int(11) NOT NULL,
  `tiempo_maximo_pregunta` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `registro_temp`
--

CREATE TABLE `registro_temp` (
  `temp_id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `contrasena` varchar(200) NOT NULL,
  `correo` varchar(100) NOT NULL,
  `dni` char(8) NOT NULL,
  `tipo_usuario` char(1) NOT NULL,
  `cant_monedas` int(11) NOT NULL DEFAULT 0,
  `verification_code` varchar(10) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `respuesta`
--

CREATE TABLE `respuesta` (
  `respuesta_id` int(11) NOT NULL,
  `texto_respuesta` varchar(100) NOT NULL,
  `estado_respuesta` tinyint(1) NOT NULL,
  `pregunta_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `skin`
--

CREATE TABLE `skin` (
  `skin_id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `url_imagen` varchar(255) NOT NULL,
  `precio` int(10) UNSIGNED NOT NULL,
  `vigencia` tinyint(1) NOT NULL DEFAULT 1,
  `skinDefault` tinyint(1) NOT NULL DEFAULT 0,
  `categoria` char(1) NOT NULL CHECK (`categoria` in ('N','E','L'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Volcado de datos para la tabla `skin`
--

INSERT INTO `skin` (`skin_id`, `nombre`, `url_imagen`, `precio`, `vigencia`, `skinDefault`, `categoria`) VALUES
(1, 'Skin default chico', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761277844/Skin_default_hombre_dd8uud.png', 250, 1, 1, 'N'),
(2, 'Skin Default Chica', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761277843/Skin_default_chica_tdx1wn.png', 0, 1, 1, 'N'),
(3, 'Skin ing. Civil', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761265960/ingcivil_l70gwl.png', 250, 1, 0, 'N'),
(4, 'Skin Doctor', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761266435/a81241a9-bc7e-44cb-add3-3567c2272bc5.png', 250, 1, 0, 'N'),
(5, 'Skin Developer', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761267295/4b793a2c-ce12-4fd2-b018-40a4facc7373.png', 250, 1, 0, 'N'),
(7, 'Skin Abogado', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761266580/8374a853-3de9-4793-9f76-849d73ffa400.png', 250, 1, 0, 'N'),
(10, 'Skin Enfermera', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761267158/873b8b0a-75b9-4d24-92a5-caee3fde709f.png', 250, 1, 0, 'N'),
(12, 'Rockero / Metalero', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761278458/Rockero_waaq9r.png', 1000, 1, 0, 'E'),
(14, 'L. Messi', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761278797/GOAT_wrvpzy.png', 1500, 1, 0, 'L'),
(15, 'C. Ronaldo', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761278947/CR7_qb6rro.png', 1500, 1, 0, 'L');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `skinaccesorio`
--

CREATE TABLE `skinaccesorio` (
  `id_accesorio` int(11) NOT NULL,
  `id_skin` int(11) NOT NULL,
  `default_accesorio` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tipo_accesorio`
--

CREATE TABLE `tipo_accesorio` (
  `id_tipo_accesorio` int(11) NOT NULL,
  `nombre_tipo` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Volcado de datos para la tabla `tipo_accesorio`
--

INSERT INTO `tipo_accesorio` (`id_tipo_accesorio`, `nombre_tipo`) VALUES
(1, 'Cabello'),
(2, 'Ropa'),
(3, 'Ropa'),
(4, 'Lentes'),
(5, 'Sombrero');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuario`
--

CREATE TABLE `usuario` (
  `usuario_id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `contrasena` varchar(100) NOT NULL,
  `correo` varchar(100) NOT NULL,
  `dni` char(8) NOT NULL,
  `tipo_usuario` char(1) NOT NULL CHECK (`tipo_usuario` in ('A','P','G')),
  `cant_monedas` int(11) NOT NULL,
  `verificado` int(1) NOT NULL DEFAULT 0,
  `vigencia` tinyint(1) NOT NULL DEFAULT 1,
  `url_foto_perfil` varchar(255) DEFAULT NULL,
  `url_avatar` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Volcado de datos para la tabla `usuario`
--

INSERT INTO `usuario` (`usuario_id`, `username`, `nombre`, `contrasena`, `correo`, `dni`, `tipo_usuario`, `cant_monedas`, `verificado`, `vigencia`, `url_foto_perfil`, `url_avatar`) VALUES
(1, 'profe', 'Profesor Ejemplo', '$2b$12$8sbg23vMlHwjMYJrqiISj.ybiuyO2hMErhplxpjPmst5zmjwSmwgi', 'profe@gmail.com', '12345678', 'P', 0, 1, 1, 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761266435/a81241a9-bc7e-44cb-add3-3567c2272bc5.png', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761266435/a81241a9-bc7e-44cb-add3-3567c2272bc5.png'),
(2, 'gestor', 'Gestor Ejemplo', '<HASH_BCRYPT>', 'gestor@example.com', '87654321', 'G', 0, 1, 1, NULL, NULL),
(3, 'Joestevil', 'JOE STEVEN VILLARREAL MEJIA', '$2b$12$9f0OJl.rIB6yhiGosA3D/uCAJgj9oCZi.uNhQUOFH6k1aCIRFDY9C', '72692046@usat.pe', '72692046', 'A', 3920, 1, 1, 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761278797/GOAT_wrvpzy.png', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761278797/GOAT_wrvpzy.png');

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vista_estado_partida`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vista_estado_partida` (
`partida_id` int(11)
,`codigo_partida` varchar(6)
,`estado` varchar(20)
,`pregunta_actual_index` int(11)
,`respuestas_recibidas` int(11)
,`tiempo_inicio_pregunta` datetime
,`updated_at` timestamp
,`cuestionario_id` int(11)
,`nombre_cuestionario` varchar(100)
,`total_participantes` bigint(21)
,`total_preguntas` bigint(21)
);

-- --------------------------------------------------------

--
-- Estructura para la vista `inventario_completo`
--
DROP TABLE IF EXISTS `inventario_completo`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `inventario_completo`  AS SELECT `i`.`id_inventario` AS `id_inventario`, `i`.`usuario_id` AS `usuario_id`, `i`.`equipada` AS `equipada`, `i`.`fecha_adquisicion` AS `fecha_adquisicion`, `i`.`id_item` AS `id_item`, `i`.`tipo_item` AS `tipo_item`, `s`.`nombre` AS `nombre_item`, `s`.`url_imagen` AS `url_imagen_base`, NULL AS `id_tipo_accesorio`, NULL AS `nombre_tipo_accesorio` FROM (`inventario` `i` join `skin` `s` on(`i`.`id_item` = `s`.`skin_id`)) WHERE `i`.`tipo_item` = 'SKIN'union all select `i`.`id_inventario` AS `id_inventario`,`i`.`usuario_id` AS `usuario_id`,`i`.`equipada` AS `equipada`,`i`.`fecha_adquisicion` AS `fecha_adquisicion`,`i`.`id_item` AS `id_item`,`i`.`tipo_item` AS `tipo_item`,`a`.`nombre` AS `nombre_item`,`a`.`url_imagen` AS `url_imagen_base`,`ta`.`id_tipo_accesorio` AS `id_tipo_accesorio`,`ta`.`nombre_tipo` AS `nombre_tipo_accesorio` from ((`inventario` `i` join `accesorio` `a` on(`i`.`id_item` = `a`.`accesorio_id`)) join `tipo_accesorio` `ta` on(`a`.`id_tipo_accesorio` = `ta`.`id_tipo_accesorio`)) where `i`.`tipo_item` = 'ACCESORIO'  ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vista_estado_partida`
--
DROP TABLE IF EXISTS `vista_estado_partida`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vista_estado_partida`  AS SELECT `pa`.`partida_id` AS `partida_id`, `pa`.`codigo_partida` AS `codigo_partida`, `pa`.`estado` AS `estado`, `pa`.`pregunta_actual_index` AS `pregunta_actual_index`, `pa`.`respuestas_recibidas` AS `respuestas_recibidas`, `pa`.`tiempo_inicio_pregunta` AS `tiempo_inicio_pregunta`, `pa`.`updated_at` AS `updated_at`, `c`.`cuestionario_id` AS `cuestionario_id`, `c`.`nombre_cuestionario` AS `nombre_cuestionario`, count(distinct `part`.`participante_id`) AS `total_participantes`, (select count(0) from `pregunta` where `pregunta`.`cuestionario_id` = `c`.`cuestionario_id`) AS `total_preguntas` FROM ((`partida` `pa` join `cuestionario` `c` on(`pa`.`cuestionario_id` = `c`.`cuestionario_id`)) left join `participante` `part` on(`pa`.`partida_id` = `part`.`partida_id`)) GROUP BY `pa`.`partida_id` ;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `accesorio`
--
ALTER TABLE `accesorio`
  ADD PRIMARY KEY (`accesorio_id`),
  ADD KEY `fk_accesorio_tipo` (`id_tipo_accesorio`);

--
-- Indices de la tabla `cuestionario`
--
ALTER TABLE `cuestionario`
  ADD PRIMARY KEY (`cuestionario_id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `inventario`
--
ALTER TABLE `inventario`
  ADD PRIMARY KEY (`id_inventario`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `participante`
--
ALTER TABLE `participante`
  ADD PRIMARY KEY (`participante_id`),
  ADD KEY `lider_id` (`lider_id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `partida_id` (`partida_id`);

--
-- Indices de la tabla `partida`
--
ALTER TABLE `partida`
  ADD PRIMARY KEY (`partida_id`),
  ADD UNIQUE KEY `codigo_partida` (`codigo_partida`),
  ADD KEY `cuestionario_id` (`cuestionario_id`),
  ADD KEY `usuario_creador_id` (`usuario_creador_id`),
  ADD KEY `idx_partida_estado` (`estado`),
  ADD KEY `idx_partida_codigo` (`codigo_partida`);

--
-- Indices de la tabla `password_reset_tokens`
--
ALTER TABLE `password_reset_tokens`
  ADD PRIMARY KEY (`prt_id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `pregunta`
--
ALTER TABLE `pregunta`
  ADD PRIMARY KEY (`pregunta_id`),
  ADD KEY `cuestionario_id` (`cuestionario_id`);

--
-- Indices de la tabla `pregunta_participante`
--
ALTER TABLE `pregunta_participante`
  ADD PRIMARY KEY (`pregunta_participante_id`),
  ADD KEY `participante_id` (`participante_id`),
  ADD KEY `pregunta_id` (`pregunta_id`),
  ADD KEY `respuesta_seleccionada_id` (`respuesta_seleccionada_id`);

--
-- Indices de la tabla `registro_temp`
--
ALTER TABLE `registro_temp`
  ADD PRIMARY KEY (`temp_id`);

--
-- Indices de la tabla `respuesta`
--
ALTER TABLE `respuesta`
  ADD PRIMARY KEY (`respuesta_id`),
  ADD KEY `pregunta_id` (`pregunta_id`);

--
-- Indices de la tabla `skin`
--
ALTER TABLE `skin`
  ADD PRIMARY KEY (`skin_id`);

--
-- Indices de la tabla `skinaccesorio`
--
ALTER TABLE `skinaccesorio`
  ADD PRIMARY KEY (`id_accesorio`,`id_skin`),
  ADD KEY `id_skin` (`id_skin`);

--
-- Indices de la tabla `tipo_accesorio`
--
ALTER TABLE `tipo_accesorio`
  ADD PRIMARY KEY (`id_tipo_accesorio`);

--
-- Indices de la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD PRIMARY KEY (`usuario_id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `correo` (`correo`),
  ADD UNIQUE KEY `dni` (`dni`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `accesorio`
--
ALTER TABLE `accesorio`
  MODIFY `accesorio_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT de la tabla `cuestionario`
--
ALTER TABLE `cuestionario`
  MODIFY `cuestionario_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `inventario`
--
ALTER TABLE `inventario`
  MODIFY `id_inventario` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `participante`
--
ALTER TABLE `participante`
  MODIFY `participante_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `partida`
--
ALTER TABLE `partida`
  MODIFY `partida_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `password_reset_tokens`
--
ALTER TABLE `password_reset_tokens`
  MODIFY `prt_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pregunta`
--
ALTER TABLE `pregunta`
  MODIFY `pregunta_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pregunta_participante`
--
ALTER TABLE `pregunta_participante`
  MODIFY `pregunta_participante_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `registro_temp`
--
ALTER TABLE `registro_temp`
  MODIFY `temp_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `respuesta`
--
ALTER TABLE `respuesta`
  MODIFY `respuesta_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `skin`
--
ALTER TABLE `skin`
  MODIFY `skin_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT de la tabla `usuario`
--
ALTER TABLE `usuario`
  MODIFY `usuario_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `accesorio`
--
ALTER TABLE `accesorio`
  ADD CONSTRAINT `fk_accesorio_tipo` FOREIGN KEY (`id_tipo_accesorio`) REFERENCES `tipo_accesorio` (`id_tipo_accesorio`);

--
-- Filtros para la tabla `cuestionario`
--
ALTER TABLE `cuestionario`
  ADD CONSTRAINT `cuestionario_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`usuario_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `inventario`
--
ALTER TABLE `inventario`
  ADD CONSTRAINT `inventario_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`usuario_id`);

--
-- Filtros para la tabla `participante`
--
ALTER TABLE `participante`
  ADD CONSTRAINT `participante_ibfk_1` FOREIGN KEY (`lider_id`) REFERENCES `participante` (`participante_id`) ON DELETE SET NULL,
  ADD CONSTRAINT `participante_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`usuario_id`),
  ADD CONSTRAINT `participante_ibfk_3` FOREIGN KEY (`partida_id`) REFERENCES `partida` (`partida_id`);

--
-- Filtros para la tabla `partida`
--
ALTER TABLE `partida`
  ADD CONSTRAINT `partida_ibfk_1` FOREIGN KEY (`cuestionario_id`) REFERENCES `cuestionario` (`cuestionario_id`),
  ADD CONSTRAINT `partida_ibfk_2` FOREIGN KEY (`usuario_creador_id`) REFERENCES `usuario` (`usuario_id`);

--
-- Filtros para la tabla `password_reset_tokens`
--
ALTER TABLE `password_reset_tokens`
  ADD CONSTRAINT `password_reset_tokens_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`usuario_id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `pregunta`
--
ALTER TABLE `pregunta`
  ADD CONSTRAINT `pregunta_ibfk_1` FOREIGN KEY (`cuestionario_id`) REFERENCES `cuestionario` (`cuestionario_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `pregunta_participante`
--
ALTER TABLE `pregunta_participante`
  ADD CONSTRAINT `pregunta_participante_ibfk_1` FOREIGN KEY (`participante_id`) REFERENCES `participante` (`participante_id`),
  ADD CONSTRAINT `pregunta_participante_ibfk_2` FOREIGN KEY (`pregunta_id`) REFERENCES `pregunta` (`pregunta_id`),
  ADD CONSTRAINT `pregunta_participante_ibfk_3` FOREIGN KEY (`respuesta_seleccionada_id`) REFERENCES `respuesta` (`respuesta_id`);

--
-- Filtros para la tabla `respuesta`
--
ALTER TABLE `respuesta`
  ADD CONSTRAINT `respuesta_ibfk_1` FOREIGN KEY (`pregunta_id`) REFERENCES `pregunta` (`pregunta_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `skinaccesorio`
--
ALTER TABLE `skinaccesorio`
  ADD CONSTRAINT `skinaccesorio_ibfk_1` FOREIGN KEY (`id_accesorio`) REFERENCES `accesorio` (`accesorio_id`),
  ADD CONSTRAINT `skinaccesorio_ibfk_2` FOREIGN KEY (`id_skin`) REFERENCES `skin` (`skin_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
