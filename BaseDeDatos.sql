CREATE TABLE `USUARIO` (
  `usuario_id` INT(11) NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(100) NOT NULL UNIQUE,
  `nombre` VARCHAR(100) NOT NULL,
  `contrasena` VARCHAR(100) NOT NULL,
  `correo` VARCHAR(100) NOT NULL UNIQUE,
  `dni` CHAR(8) NOT NULL UNIQUE,
  `tipo_usuario` CHAR(1) NOT NULL CHECK (`tipo_usuario` IN ('A', 'P')),
  `cant_monedas` INT(11) NOT NULL,
  PRIMARY KEY (`usuario_id`)
);

INSERT INTO `USUARIO` (`username`, `nombre`, `contrasena`, `correo`, `dni`, `tipo_usuario`, `cant_monedas`) VALUES
('yamir_zamora', 'Yamir Zamora', 'pass123', 'zamora@gmail.com', '12345678', 'A', 0),
('sebastian_henckell', 'Sebastián Henckell', 'pass456', 'sebastian@gmail.com', '87654321', 'P', 0),
('jeremy_garcia', 'Jeremy García', 'pass789', 'jeremy@gmail.com', '11223344', 'P', 0);

