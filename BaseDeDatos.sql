CREATE TABLE `USUARIO` (
  `usuario_id` INT(11) NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(100) NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `contrasena` VARCHAR(100) NOT NULL,
  `correo` VARCHAR(100) NOT NULL,
  `tipo_usuario` CHAR(1) NOT NULL,
  `cant_monedas` INT(11) NOT NULL,
  PRIMARY KEY (`usuario_id`)
);

INSERT INTO `USUARIO` (`username`, `nombre`, `contrasena`, `correo`, `tipo_usuario`, `cant_monedas`) VALUES
('yamir_zamora', 'Yamir Zamora', 'pass123', 'zamora@gmail.com', 'A', 0),
('sebastian_henckell', 'Sebastián Henckell', 'pass456', 'sebastian@gmail.com', 'P', 0),
('jeremy_garcia', 'Jeremy García', 'pass789', 'jeremy@gmail.com', 'P', 0);