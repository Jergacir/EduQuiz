-- 1. Tabla Tipo_accesorio (Estaba correcta)
CREATE TABLE Tipo_accesorio (
    id_tipo_accesorio INT PRIMARY KEY,
    nombre_tipo VARCHAR(100) NOT NULL
);

-- 2. Modificar 'accesorios' (Corregido para tablas con datos)

-- CORRECCIÓN (Paso A): Añade la columna permitiendo nulos
ALTER TABLE `accesorios`
    ADD COLUMN `id_tipo_accesorio` INT NULL;

/*
-- CORRECCIÓN (Paso B): ¡IMPORTANTE!
-- Antes del siguiente paso, debes actualizar tus datos.
-- Reemplaza el '1' por un ID que SÍ exista en tu tabla 'Tipo_accesorio'.
UPDATE `accesorios` SET `id_tipo_accesorio` = 1 WHERE `id_tipo_accesorio` IS NULL;
*/

-- CORRECCIÓN (Paso C): Ahora que no hay nulos, modifica la columna a NOT NULL
ALTER TABLE `accesorios`
    MODIFY COLUMN `id_tipo_accesorio` INT NOT NULL;

-- CORRECCIÓN (Paso D): Añade la clave foránea
ALTER TABLE `accesorios`
    ADD CONSTRAINT `fk_accesorios_tipo`
        FOREIGN KEY (`id_tipo_accesorio`)
        REFERENCES `Tipo_accesorio`(`id_tipo_accesorio`);

-- CORRECCIÓN (Paso E): Renombra la tabla para que coincida con las referencias
-- La tabla SkinAccesorio la llama 'Accesorios' (mayúscula)
RENAME TABLE `accesorios` TO `Accesorios`;


-- 3. Tabla Skin (Bases Visuales)
-- CORRECCIÓN: Esta tabla faltaba. Es necesaria ANTES de crear SkinAccesorio.
CREATE TABLE Skin (
    skin_id INT PRIMARY KEY,
    nombre_skin VARCHAR(100) NOT NULL
    -- ...Otras columnas que necesites para la skin...
);


-- 4. Tabla SkinAccesorio (Composición Default)
-- Esta tabla ahora funcionará porque 'Accesorios' y 'Skin' existen.
CREATE TABLE SkinAccesorio (
    id_accesorio INT NOT NULL,
    id_skin INT NOT NULL,
    default_accesorio BOOLEAN,
    PRIMARY KEY (id_accesorio, id_skin),
    FOREIGN KEY (id_accesorio) REFERENCES Accesorios(accesorio_id),
    FOREIGN KEY (id_skin) REFERENCES Skin(skin_id)
);

-- 5. Tabla Usuario (Necesaria para Inventario)
-- CORRECCIÓN: Esta tabla faltaba. Es necesaria ANTES de crear Inventario.
CREATE TABLE Usuario (
    usuario_id INT PRIMARY KEY,
    nombre_usuario VARCHAR(100) NOT NULL
    -- ...Otras columnas de usuario...
);


-- 6. Tabla Inventario (Inventario Universal y Equipamiento)
-- Esta tabla ahora funcionará porque 'Usuario' existe.
CREATE TABLE Inventario (
    id_inventario INT PRIMARY KEY,
    usuario_id INT NOT NULL,
    equipada BOOLEAN,
    fecha_adquisicion DATE,
    id_item INT NOT NULL,
    tipo_item VARCHAR(20) NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES Usuario(usuario_id),
    CHECK(tipo_item IN ('SKIN', 'ACCESORIO'))
);

-- CORRECCIÓN: Se eliminó el texto basura (');p` WHERE 1') que estaba al final.

CREATE VIEW Inventario_Completo AS
SELECT
    I.id_inventario,
    I.usuario_id,
    I.equipada,
    I.fecha_adquisicion,
    I.id_item,
    I.tipo_item,
    -- Campos de la Skin
    S.nombre AS nombre_item,
    S.url_imagen AS url_imagen_base,
    NULL AS id_tipo_accesorio,
    NULL AS nombre_tipo_accesorio
FROM
    Inventario I
JOIN
    Skin S ON I.id_item = S.id_skin
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
    -- Campos del Accesorio
    A.nombre AS nombre_item,
    A.url_imagen AS url_imagen_base,
    TA.id_tipo_accesorio,
    TA.nombre_tipo AS nombre_tipo_accesorio
FROM
    Inventario I
JOIN
    Accesorios A ON I.id_item = A.id_accesorio
JOIN
    Tipo_accesorio TA ON A.id_tipo_accesorio = TA.id_tipo_accesorio
WHERE
    I.tipo_item = 'ACCESORIO';

SELECT *
FROM Inventario_Completo
WHERE usuario_id = 100
ORDER BY tipo_item DESC, equipada DESC;

--Usuario (username): profe
--Correo: profe@gmail.com
--Contraseña (texto plano): Profe123!

INSERT INTO `usuario`
  (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verificado, vigencia)
VALUES
  ('profe', 'Profesor Ejemplo', '$2b$12$8sbg23vMlHwjMYJrqiISj.ybiuyO2hMErhplxpjPmst5zmjwSmwgi', 'profe@gmail.com', '12345678', 'P', 0, 1, 1);

  --Usuario (username): gestor
  --Correo: gestor@example.com
  --Contraseña (texto plano): Gestor123!

INSERT INTO `usuario`
  (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verificado, vigencia)
VALUES
  ('gestor', 'Gestor Ejemplo', '<HASH_BCRYPT>', 'gestor@example.com', '87654321', 'G', 0, 1, 1);






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


INSERT INTO `skin` (`skin_id`, `nombre`, `url_imagen`, `precio`, `vigencia`, `skinDefault`, `categoria`) VALUES
(6, 'Miss universo', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541183/miss_txjipp.png', 3500, 1, 0, 'E'),
(8, 'Voleybolista', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541183/Voleybolista_qblsyl.png', 3500, 1, 0, 'E'),
(9, 'Astronauta', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541184/astronauta_rppbqi.png', 3500, 1, 0, 'E'),
(11, 'Militar', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541184/militar_az3ild.png', 3500, 1, 0, 'E'),
(13, 'Freddie Mercury', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541184/FreddieMercury_rovgmz.png', 5000, 1, 0, 'L'),
(16, 'Neymar', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541184/neymart_belhaz.png', 5000, 1, 0, 'L'),
(17, 'Michael Jackson', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541184/MJ_jnxcww.png', 5000, 1, 0, 'L'),
(18, 'Spiderman', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541183/Spiderman_qcxu2b.png', 5000, 1, 0, 'L'),
(19, 'Ironman', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541183/ironman_srrjri.png', 5000, 1, 0, 'L'),
(20, 'Superman', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541184/superman_yvlwxq.png', 5000, 1, 0, 'L'),
(21, 'Batman', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541183/batman_hfojlw.png', 5000, 1, 0, 'L'),
(22, 'Axl Rose', 'https://res.cloudinary.com/dpxslk02r/image/upload/v1761541183/axelrose_hvffnr.png', 5000, 1, 0, 'L');