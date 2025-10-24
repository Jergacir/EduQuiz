-- Migración: asignar skins por defecto (skinDefault=1) a todos los usuarios verificados
-- Instrucciones:
-- 1) Revisa qué nombre tiene tu tabla de inventario: `inventario` o `Inventario`.
-- 2) Ejecuta solo la sección correspondiente a tu nombre de tabla.
-- 3) Realiza un backup antes de ejecutar.

-- ==========================
-- Para tabla `inventario` (minúsculas)
-- ==========================

INSERT INTO inventario (usuario_id, id_item, tipo_item, equipada, fecha_adquisicion)
SELECT u.usuario_id AS usuario_id, s.skin_id AS id_item, 'SKIN' AS tipo_item, 0 AS equipada, NOW() AS fecha_adquisicion
FROM usuario u
CROSS JOIN skin s
WHERE u.verificado = 1
  AND COALESCE(s.skinDefault, 0) = 1
  AND NOT EXISTS (
    SELECT 1 FROM inventario i
    WHERE i.usuario_id = u.usuario_id
      AND i.id_item = s.skin_id
      AND i.tipo_item = 'SKIN'
  );

-- ==========================
-- Para tabla `Inventario` (mayúscula)
-- ==========================

INSERT INTO `Inventario` (usuario_id, id_item, tipo_item, equipada, fecha_adquisicion)
SELECT u.usuario_id AS usuario_id, s.skin_id AS id_item, 'SKIN' AS tipo_item, 0 AS equipada, NOW() AS fecha_adquisicion
FROM usuario u
CROSS JOIN skin s
WHERE u.verificado = 1
  AND COALESCE(s.skinDefault, 0) = 1
  AND NOT EXISTS (
    SELECT 1 FROM `Inventario` i
    WHERE i.usuario_id = u.usuario_id
      AND i.id_item = s.skin_id
      AND i.tipo_item = 'SKIN'
  );

-- Nota:
-- - Si tu tabla `inventario` utiliza un esquema distinto de columnas (p. ej. nombres de columnas diferentes), ajusta las columnas objetivo.
-- - Si `id_inventario` no es AUTO_INCREMENT en tu tabla, estas inserciones crearán filas sin especificar id_inventario (dependiendo del esquema). Si tu esquema requiere id_inventario explícito, tendrás que ajustar la sentencia para proporcionar valores únicos.
-- - Recomiendo ejecutar en un entorno de staging primero.
-- - Alternativamente, usa el endpoint administrador POST /admin/assign_default_skins desde una sesión de gestor para aplicar la asignación desde la app.
