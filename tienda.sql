-- DDL (Data Definition Language) para crear la estructura de la BD

-- 1. Tabla Tipo_accesorio (Slots/Regiones)
CREATE TABLE Tipo_accesorio (
    id_tipo_accesorio INT PRIMARY KEY,
    nombre_tipo VARCHAR(100) NOT NULL
);

-- 2. Tabla Accesorios (Catálogo de Ítems Individuales)
CREATE TABLE Accesorios (
    id_accesorio INT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    url_imagen VARCHAR(200) NOT NULL,
    precio INT,
    vigencia BOOLEAN, -- Campo 'vigencia' para disponibilidad
    id_tipo_accesorio INT NOT NULL,
    FOREIGN KEY (id_tipo_accesorio) REFERENCES Tipo_accesorio(id_tipo_accesorio)
);

-- 3. Tabla Skin (Bases Visuales)
CREATE TABLE Skin (
    id_skin INT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion VARCHAR(200),
    url_imagen VARCHAR(200) NOT NULL,
    precio INT,
    vigencia BOOLEAN -- Campo 'vigencia' para disponibilidad
);

-- 4. Tabla SkinAccesorio (Composición Default)
-- Clave compuesta (id_skin, id_accesorio) para asegurar unicidad
CREATE TABLE SkinAccesorio (
    id_accesorio INT NOT NULL,
    id_skin INT NOT NULL,
    default_accesorio BOOLEAN, -- Renombrado de 'default' para evitar conflicto con palabra reservada
    PRIMARY KEY (id_accesorio, id_skin),
    FOREIGN KEY (id_accesorio) REFERENCES Accesorios(id_accesorio),
    FOREIGN KEY (id_skin) REFERENCES Skin(id_skin)
);

-- 6. Tabla Inventario (Inventario Universal y Equipamiento)
CREATE TABLE Inventario (
    id_inventario INT PRIMARY KEY,
    usuario_id INT NOT NULL,
    equipada BOOLEAN,
    fecha_adquisicion DATE,
    id_item INT NOT NULL, -- FK a Skin o Accesorios
    tipo_item VARCHAR(20) NOT NULL, -- 'SKIN' o 'ACCESORIO'
    FOREIGN KEY (usuario_id) REFERENCES Usuario(usuario_id),
    -- Nota: Las FK a Skin y Accesorios para id_item deben ser gestionadas
    -- a nivel de aplicación, ya que el campo id_item es polimórfico.
    CHECK (tipo_item IN ('SKIN', 'ACCESORIO'))
);

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

-- correo: profe@gmail.com
-- contraseña: Profe123!