# 📖 Manual de Uso · Sistema de Inventario Tecnológico Cusiana

Bienvenido al manual oficial del **Sistema de Inventario Tecnológico del Colegio**. Este documento detalla cómo utilizar cada función de la plataforma para registrar, consultar, asignar y gestionar los equipos y usuarios de la institución.

---

## 📑 Tabla de Contenido
1. [Acceso al Sistema y Roles de Usuario](#1-acceso-al-sistema-y-roles-de-usuario)
2. [Estructura del Panel Principal](#2-estructura-del-panel-principal)
3. [Cómo Filtrar y Escoger qué Equipos Ver](#3-cómo-filtrar-y-escoger-qué-equipos-ver)
4. [Cómo Registrar un Nuevo Equipo (Paso a Paso)](#4-cómo-registrar-un-nuevo-equipo-paso-a-paso)
5. [Asistente Inteligente de Salón y Ubicación](#5-asistente-inteligente-de-salón-y-ubicación)
6. [Asignación y Reasignación de Equipos](#6-asignación-y-reasignación-de-equipos)
7. [Edición y Eliminación de Equipos](#7-edición-y-eliminación-de-equipos)
8. [Gestión de Usuarios y Solicitudes](#8-gestión-de-usuarios-y-solicitudes)
9. [Cambio de Contraseña y Seguridad](#9-cambio-de-contraseña-y-seguridad)
10. [Solución de Problemas Frecuentes](#10-solución-de-problemas-frecuentes)

---

## 1. Acceso al Sistema y Roles de Usuario

### Ingreso
1. Abre tu navegador e ingresa a:
   - Desde el computador servidor: `http://localhost:5000`
   - Desde otro dispositivo conectado a la misma red: `http://<IP-del-servidor>:5000`.
     Consulta la IPv4 del servidor con `ipconfig`.
2. Escribe tu **correo institucional** y **contraseña**.
3. Haz clic en **Ingresar al inventario**.

### Roles y Permisos
- **👑 Administrador:** Control total. Puede registrar, editar, reasignar y eliminar equipos; registrar usuarios nuevos; aprobar o rechazar solicitudes de acceso; y consultar el historial completo de movimientos.
- **🛠️ Encargado de Inventario:** Puede registrar y editar equipos. Puede consultar y filtrar por salón, pero la gestión de salones está reservada al administrador.
- **🎓 Rector / Coordinador:** Perfil de solo consulta. Puede visualizar en tiempo real todos los equipos, sus salones, responsables, fotos y estadísticas, sin modificar información.

---

## 2. Estructura del Panel Principal

El panel está organizado en cuatro zonas clave:
1. **Barra Superior (Header):**
   - Logos institucionales.
   - Estado de conexión en vivo (punto verde pulsante).
   - Indicador de tu usuario y rol actual.
   - Botón **📖 Manual de uso** para consultar ayuda en cualquier momento.
   - Botones de acceso rápido según tu rol (**Actividad**, **Solicitudes**, **Registrar usuario**, **Cambiar contraseña** y **Salir**).
2. **Tarjetas de Resumen Interactivas:**
   - Muestran el conteo en tiempo real de:
     - **Total equipos** (con selector de vista rápida).
     - **Buen estado** (verde).
     - **En reparación** (marrón).
     - **Sin asignar** (amarillo).
     - **Salas / áreas** (rosado).
3. **Barra de Filtros y Búsqueda:**
   - Buscador por texto (código, marca, modelo).
   - Selectores por tipo de equipo, estado y salón.
   - Todos los roles pueden filtrar por salón; solo el administrador puede agregar, renombrar o eliminar salones desde el botón **Salas**.
4. **Tabla de Inventario:**
   - Lista detallada con foto, código, nombre del equipo, estado, ubicación, sección y persona responsable.

---

## 3. Cómo Filtrar y Escoger qué Equipos Ver

El sistema te permite elegir exactamente qué equipos deseas ver de **dos formas muy rápidas**:

### Método A: Clic directo en las Tarjetas de Resumen
Haz clic sobre cualquiera de las tarjetas superiores para filtrar de inmediato:
- Haz clic en **Total equipos** 👉 Muestra todos los equipos registrados.
- Haz clic en **Buen estado** 👉 Muestra únicamente los equipos operativos (color verde).
- Haz clic en **En reparación** 👉 Muestra únicamente los que están en mantenimiento (color marrón).
- Haz clic en **Sin asignar** 👉 Muestra solo los equipos que no tienen un salón o responsable asignado (color amarillo).
- Haz clic en **Salas / áreas** 👉 Muestra solo los equipos que ya tienen una sala asignada (color rosado).

### Método B: Selector desplegable en la tarjeta de Total
En la primera tarjeta (**Total equipos**), utiliza el menú desplegable integrado para elegir:
- *Ver todos los equipos*
- *Solo en Buen estado*
- *Solo En reparación*
- *Solo Dañados*
- *Solo Sin asignar*
- *Solo Computadores, Pantallas, Torres, Tablets o Televisores*

Al escoger una opción, la tabla se actualizará al instante y aparecerá una barra superior que dice:
> **Mostrando solo: [Opción elegida]** con un botón para **Quitar filtro** cuando quieras volver a ver todo.

---

## 4. Cómo Registrar un Nuevo Equipo (Paso a Paso)

1. En la parte superior derecha de la página, haz clic en el botón **`＋ Registrar equipo`**.
2. Se abrirá el formulario de registro:
   - **Código (*):** Escribe el código de inventario institucional (Ejemplo: `EQ-101`, `532`, `COMP-01`).
   - **Tipo (*):** Selecciona el tipo de equipo en la lista desplegable:
     - *Computador, Tablet, Televisor, Aire acondicionado, Torre, Teclado, Mouse, Router, Estabilizador o Pantalla.*
   - **Foto del equipo:** Haz clic para adjuntar una imagen (`JPG`, `PNG`, `WEBP` o `GIF`). Verás una vista previa instantánea.
   - **Estado (*):** Elige entre *Buen estado*, *Dañado* o *En reparación*.
   - **Marca y Modelo:** (Ejemplo: `Lenovo`, `ThinkPad E14`, `Janus`).
   - **Número de serie:** El número serial del fabricante (opcional).
   - **Características:** Notas técnicas (procesador, memoria RAM, puertos, observaciones).
   - **Ubicación y Sección:** Utiliza el **Asistente Inteligente de Salón** (ver sección 5).
3. Haz clic en **Guardar equipo**. El equipo quedará guardado de inmediato en la base de datos y visible en la tabla.

---

## 5. Asistente Inteligente de Salón y Ubicación

Para que no tengas que escribir ni adivinar a qué salón corresponde cada equipo, el sistema incluye un **Asistente Inteligente**:

1. Al seleccionar el **Tipo de equipo** en el formulario, el asistente activará una caja de sugerencias rápidas:
   - Si seleccionas **Computador, Torre o Pantalla**: Te sugerirá con botones rápidos `Sala 204`, `Sala 108`, `AULA 21` o `Sala de Sistemas`, y preseleccionará el área de `Sistemas`.
   - Si seleccionas **Televisor**: Te sugerirá `Biblioteca`, `Sala de profesores` o `Auditorio`.
   - Si seleccionas **Tablet**: Te sugerirá `Biblioteca`, `Sala 108` o `Carrito Móvil`.
   - Si seleccionas **Router o Estabilizador**: Te sugerirá `Sala de Servidores`, `Dirección` o `Sala 204`.
2. **Asignación en 1 Clic:**
   - Solo haz clic sobre el botón del salón que deseas (por ejemplo, `[📍 Sala 204]`) y los campos de **Salón** y **Sección** se llenarán automáticamente sin que tengas que escribir.
   - También puedes presionar el botón **`✨ Sugerir automáticamente`** para que el sistema elija la ubicación más recomendada.

---

## 6. Asignación y Reasignación de Equipos

1. En la tabla de inventario, **haz clic sobre cualquier equipo** para abrir su panel lateral de detalles.
2. En la sección **Asignar equipo**:
   - **Responsable:** Selecciona el encargado o docente responsable en la lista.
   - **Salón:** Elige o escribe el salón donde quedará ubicado.
   - **Fecha de asignación:** Selecciona la fecha en que se entrega el equipo.
3. Haz clic en **Guardar asignación**.
4. En la parte inferior podrás consultar el **Historial de asignaciones**, donde queda registrado quién tuvo el equipo anteriormente y desde qué fecha.

---

## 7. Edición y Eliminación de Equipos

### Para Editar un Equipo:
1. Haz clic sobre el equipo en la tabla para abrir el panel lateral.
2. Haz clic en **Editar información**.
3. Se abrirá el formulario con los datos actuales del equipo. Corrige los campos necesarios (puedes actualizar la foto, la sección, el estado, etc.).
4. Haz clic en **Guardar equipo**.

### Para Eliminar un Equipo:
*(Disponible solo para el Administrador)*
1. Abre el panel lateral del equipo haciendo clic en su fila.
2. Haz clic en el botón rojo **Eliminar equipo**.
3. Confirma la acción. El equipo y sus asignaciones quedarán eliminados.

---

## 8. Gestión de Usuarios y Solicitudes

### Crear un nuevo usuario directamente:
1. Haz clic en el botón **Registrar usuario** en el encabezado.
2. Ingresa el nombre, apellido, correo institucional, contraseña inicial (mínimo 8 caracteres) y rol (*Encargado, Rector o Coordinador*).
3. Haz clic en **Crear usuario**.

### Aprobar Solicitudes Pendientes:
- Cuando una persona se registra desde la pantalla de login, queda en estado **Pendiente**.
- El botón **Solicitudes** del encabezado mostrará un número amarillo indicando cuántas solicitudes esperan revisión.
- Haz clic en **Solicitudes** y selecciona **Aprobar** o **Rechazar**.

---

## 9. Cambio de Contraseña y Seguridad
1. Haz clic en el botón **Cambiar contraseña** en el encabezado superior.
2. Escribe tu contraseña actual.
3. Escribe tu nueva contraseña (mínimo 8 caracteres) y confírmala.
4. Haz clic en **Guardar contraseña**.

---

## 10. Solución de Problemas Frecuentes

- **¿No carga la lista de equipos o dice "No se pudo conectar"?**  
  Asegúrate de que MySQL esté iniciado en XAMPP y que Flask esté ejecutándose
  desde la raíz del proyecto con `.\.venv\Scripts\python.exe app.py` o mediante
  `iniciar.bat`.
- **¿Puedo entrar desde mi teléfono o tablet?**  
  Sí. Conéctate a la misma red Wi-Fi del colegio y abre `http://<IP-del-servidor>:5000`.
  La portada de XAMPP también redirige usando el nombre del servidor actual.
- **¿Qué hago si olvidé mi contraseña de administrador?**  
  Pídele al equipo técnico que configure temporalmente la variable `INVENTARIO_ADMIN_PASSWORD` o restablezca el hash en la base de datos MySQL.
