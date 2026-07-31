# Hoja de ruta: seguimiento de alimentación sólida

## 1. Objetivo

Añadir a Baby Buddy una sección de **Alimentación** que permita registrar, consultar y analizar qué alimentos ha comido cada niño cada día.

La nueva sección seguirá los patrones ya utilizados por el proyecto para los registros de sueño, pañales, tomas, medicación y notas:

- modelos y migraciones de Django;
- formularios de alta y edición;
- listado, filtros y paginación;
- permisos de consulta, alta, modificación y borrado;
- integración en la cronología diaria;
- API;
- importación y exportación;
- pruebas automatizadas;
- interfaz adaptable a móvil;
- textos visibles en castellano.

## 2. Principios del desarrollo

### 2.1. Registro rápido

Registrar una comida debe requerir pocos pasos. Los campos secundarios se mostrarán como opciones avanzadas cuando sea posible.

### 2.2. Datos estructurados

Los alimentos no se guardarán como una lista de texto libre. Existirá un catálogo reutilizable para poder buscar, filtrar y calcular primeras introducciones.

### 2.3. Cantidades flexibles

No será obligatorio pesar la comida. La primera versión utilizará cantidades aproximadas comprensibles y rápidas de registrar.

### 2.4. Castellano e internacionalización

Toda la funcionalidad nueva se mostrará en castellano cuando el usuario tenga seleccionado este idioma. La implementación conservará el sistema de internacionalización de Django utilizado por Baby Buddy.

Las pruebas verificarán los textos y formatos relevantes en castellano. Las traducciones nuevas se incorporarán al catálogo `locale/es/LC_MESSAGES/django.po`.

### 2.5. Desarrollo incremental

Cada fase debe quedar funcional y probada antes de comenzar la siguiente. Las mejoras no imprescindibles no bloquearán la primera versión utilizable.

## 3. Modelo funcional

### 3.1. Alimento

Representa un alimento reutilizable del catálogo.

Campos iniciales:

- **nombre**: obligatorio y único sin distinguir mayúsculas y minúsculas;
- **categoría**: fruta, verdura, carne, pescado, huevo, lácteo, cereal, legumbre, frutos secos u otro;
- **alérgeno**: indicador opcional;
- **notas**: texto opcional;
- **activo**: permite ocultar un alimento sin perder su historial.

Decisiones acordadas:

- el catálogo será común para toda la instalación;
- los usuarios autorizados podrán añadir alimentos;
- los alimentos usados podrán desactivarse, pero no eliminarse, para conservar el historial;
- las categorías iniciales serán opciones fijas;
- se incluirá posteriormente un catálogo inicial de alimentos frecuentes en castellano.

### 3.2. Comida

Representa una ingesta realizada por un niño en una fecha y hora determinadas.

Campos iniciales:

- **niño**: obligatorio;
- **fecha y hora**: obligatoria;
- **tipo de comida**:
  - desayuno;
  - almuerzo;
  - comida;
  - merienda;
  - cena;
  - tentempié;
  - otro;
- **alimentos**: uno o varios;
- **cantidad aproximada**:
  - solo lo probó;
  - poco;
  - normal;
  - bastante;
  - todo;
  - sin indicar;
- **preparación**, opcional:
  - triturado;
  - puré;
  - trozos;
  - alimentación autorregulada o BLW;
  - líquido;
  - otro;
- **notas**: texto opcional;
- **etiquetas**: integración con el sistema actual de etiquetas.

La relación entre comidas y alimentos será de muchos a muchos: una comida puede contener varios alimentos y un alimento puede aparecer en muchas comidas.

La cantidad aproximada será única y global para toda la comida. El valor vacío representará «sin indicar».

### 3.3. Perfil de alimento por niño

Cada combinación de niño y alimento podrá tener una ficha propia, independiente del catálogo común.

Campos iniciales:

- **niño**;
- **alimento**;
- **gusto**:
  - sin valorar;
  - le gusta mucho;
  - le gusta;
  - indiferente;
  - no le gusta;
  - no le gusta nada;
- **tolerancia**:
  - sin valorar;
  - le sienta bien;
  - le sienta mal;
  - posible alergia;
  - alergia confirmada;
- **notas**, opcionales;
- **fecha de actualización**, mantenida automáticamente.

El gusto y la tolerancia se almacenarán por separado. Solo podrá existir una ficha por cada combinación de niño y alimento.

### 3.4. Primera introducción

La fecha de primera introducción de un alimento no se introducirá manualmente. Se calculará a partir de la comida más antigua del niño que contenga ese alimento.

Esto permitirá mostrar:

- si un alimento es nuevo en el momento de registrar la comida;
- fecha de la primera vez;
- fecha de la última vez;
- número de veces consumido.

## 4. Experiencia de usuario prevista

### 4.1. Formulario de registro

Flujo inicial:

1. Seleccionar al niño.
2. Indicar fecha y hora.
3. Seleccionar el tipo de comida.
4. Buscar y seleccionar uno o varios alimentos.
5. Indicar la cantidad aproximada.
6. Añadir, opcionalmente, preparación, notas y etiquetas.
7. Guardar.

El selector de alimentos deberá facilitar el uso cotidiano mediante:

- búsqueda por nombre;
- selección múltiple;
- alimentos utilizados recientemente;
- posibilidad de crear un alimento sin abandonar el flujo, si resulta viable con los componentes actuales;
- funcionamiento cómodo en pantallas móviles.

Decisión de interfaz aplicada: el selector inicial será un panel siempre visible
con casillas de selección de tamaño destacado, búsqueda por nombre y
distribución adaptable en tres, dos o una columna según el ancho de pantalla.

### 4.2. Vista diaria

La vista principal mostrará las comidas ordenadas y agrupadas por día.

Ejemplo:

```text
Hoy, 30 de julio

08:30 · Desayuno
Plátano, avena y yogur · Cantidad normal

13:15 · Comida
Pollo, patata y calabacín · Comió poco
```

Cada registro permitirá editar y borrar según los permisos del usuario.

### 4.3. Filtros

El listado permitirá filtrar por:

- niño;
- intervalo de fechas;
- alimento;
- categoría;
- tipo de comida;
- cantidad aproximada;
- etiqueta.

### 4.4. Resumen diario

En una fase posterior al listado básico se mostrará:

- número de comidas;
- número de alimentos diferentes;
- distribución por categorías;
- alimentos probados por primera vez ese día.

## 5. Fases de implementación

### Fase 0. Validación del diseño

Antes de modificar la base de datos:

- confirmar nombres definitivos de las entidades;
- decidir el alcance del catálogo de alimentos;
- confirmar categorías, cantidades y preparaciones;
- preparar bocetos sencillos del formulario y del listado;
- revisar cómo encaja la nueva sección en el menú actual.

**Resultado:** diseño funcional acordado.

### Fase 1. Base de datos y administración

- crear el modelo de alimento;
- crear el modelo de comida;
- crear la relación entre comidas y alimentos;
- crear el perfil de alimento por niño;
- añadir etiquetas a las comidas;
- generar la migración;
- añadir restricciones e índices necesarios;
- crear pruebas de modelos y migraciones.

**Criterios de aceptación:**

- se pueden crear alimentos y comidas;
- una comida admite varios alimentos;
- cada niño puede tener una valoración diferente del mismo alimento;
- gusto y tolerancia se conservan como valores independientes;
- al borrar un niño se elimina su historial de comidas;
- eliminar o desactivar un alimento no deja datos inconsistentes;
- el orden predeterminado muestra primero las comidas más recientes.

### Fase 2. Operaciones básicas en la interfaz

- crear formularios;
- crear vistas de listado, alta, edición y borrado;
- crear rutas;
- crear plantillas siguiendo el estilo existente;
- registrar los modelos en la administración de Django;
- añadir permisos;
- añadir el acceso a la sección en la navegación;
- incorporar los textos en castellano;
- crear pruebas de formularios, vistas y permisos.

**Criterios de aceptación:**

- un usuario autorizado puede registrar una comida desde móvil y escritorio;
- los errores de validación se muestran en castellano;
- se puede editar y borrar un registro;
- un usuario sin permisos no puede realizar acciones no autorizadas;
- el listado mantiene el estilo visual de Baby Buddy.

### Fase 3. Catálogo y selector de alimentos

- crear listado y mantenimiento del catálogo;
- implementar búsqueda;
- implementar selección múltiple;
- mostrar alimentos recientes;
- estudiar la creación rápida de alimentos desde el formulario;
- impedir duplicados por diferencias de mayúsculas o espacios;
- añadir pruebas del selector y del catálogo.

**Criterios de aceptación:**

- localizar un alimento frecuente requiere pocos pasos;
- no se crean duplicados como `Plátano` y `plátano`;
- el selector funciona correctamente mediante teclado y pantalla táctil;
- los alimentos inactivos no aparecen para nuevas comidas, pero permanecen en el historial.

### Fase 4. Vista diaria, filtros y cronología

- agrupar las comidas por fecha;
- añadir los filtros definidos;
- integrar las comidas en la cronología del niño;
- mostrar un resumen diario;
- identificar visualmente los alimentos nuevos;
- añadir pruebas de consultas, filtros y cronología.

**Criterios de aceptación:**

- se puede responder rápidamente a “¿qué ha comido hoy?”;
- el cambio de día respeta la zona horaria configurada;
- la cronología mezcla correctamente las comidas con el resto de eventos;
- la primera introducción se calcula por niño.

### Fase 5. API e importación/exportación

- crear serializadores y endpoints;
- aplicar los permisos existentes de la API;
- documentar los nuevos endpoints;
- actualizar el esquema OpenAPI;
- añadir exportación;
- definir e implementar el formato de importación;
- añadir pruebas de API e importación/exportación.

**Criterios de aceptación:**

- las operaciones principales pueden realizarse mediante la API;
- la documentación describe campos y valores admitidos;
- una exportación conserva la relación entre comidas y alimentos;
- una importación rechaza datos inválidos con mensajes claros.

### Fase 6. Informes

- crear la vista “Alimentos probados”;
- mostrar primera vez, última vez y frecuencia;
- crear gráficos por categorías y periodos;
- evaluar un calendario de variedad alimentaria;
- añadir pruebas de cálculos e informes.

Posibles informes:

- alimentos diferentes por semana;
- frecuencia por alimento;
- distribución por categorías;
- nuevas introducciones;
- días desde la última vez que tomó un alimento.

### Fase 7. Reacciones

Esta fase se tratará como seguimiento observacional, no como diagnóstico médico.

Posibles campos:

- reacción observada;
- descripción;
- fecha y hora aproximada;
- imagen opcional;
- relación con una comida concreta.

Antes de implementarla habrá que definir claramente:

- cómo se presenta la información sin hacer interpretaciones médicas;
- qué permisos y privacidad necesita;
- si una reacción puede asociarse a uno o varios alimentos de la comida.

### Fase 8. Optimización y accesibilidad

- revisar el número de consultas del listado y la cronología;
- comprobar formularios y tablas en móvil;
- revisar navegación mediante teclado;
- añadir etiquetas accesibles;
- revisar contraste e iconos;
- probar con un historial de datos grande;
- actualizar la documentación de usuario.

## 6. Trabajo transversal

Estas tareas acompañarán a todas las fases:

- mantener compatibilidad con las convenciones del proyecto;
- utilizar migraciones reversibles;
- no introducir cambios incompatibles en la API sin documentarlos;
- ejecutar las pruebas existentes además de las nuevas;
- mantener el formato y las comprobaciones automáticas del repositorio;
- actualizar traducciones;
- revisar rendimiento y consultas a la base de datos;
- documentar decisiones que afecten a futuras ampliaciones.

## 7. Elementos fuera del MVP

No formarán parte de la primera entrega:

- cálculo de calorías;
- análisis automático de nutrientes;
- recomendaciones médicas o nutricionales;
- recetas completas;
- planificación de menús;
- cantidades obligatorias en gramos;
- interpretación automática de alergias;
- integración con bases de datos nutricionales externas.

Podrán estudiarse una vez validado el registro cotidiano.

## 8. Orden de entrega recomendado

1. Diseño y decisiones pendientes.
2. Modelos y migración.
3. Alta, edición, borrado y listado básico.
4. Catálogo y selector cómodo.
5. Vista diaria y cronología.
6. Filtros y primeras introducciones.
7. API e importación/exportación.
8. Informes.
9. Reacciones y otras ampliaciones.

## 9. Definición de MVP completado

La primera versión se considerará terminada cuando:

- exista un catálogo de alimentos;
- se pueda registrar una comida con varios alimentos;
- todos los campos y mensajes nuevos se visualicen en castellano;
- se pueda consultar qué comió cada niño en un día determinado;
- las comidas aparezcan en su cronología;
- se pueda detectar la primera introducción de un alimento;
- funcionen alta, consulta, edición y borrado con sus permisos;
- existan pruebas automatizadas para los casos principales;
- la experiencia sea usable desde un teléfono móvil.

## 10. Decisiones cerradas y próximo incremento

Quedan acordadas para la Fase 1 las siguientes decisiones:

1. El catálogo de alimentos es común para toda la instalación.
2. Los usuarios autorizados podrán ampliarlo.
3. Los alimentos con historial se desactivarán en lugar de eliminarse.
4. El catálogo inicial frecuente en castellano se añadirá en un incremento posterior.
5. Cada comida admite varios alimentos y una única cantidad aproximada global.
6. Cada niño dispone de una valoración propia por alimento.
7. El gusto y la tolerancia son valoraciones independientes.

El primer incremento se limita a los modelos `Food`, `Meal`, `MealFood` y `ChildFoodProfile`, su migración y sus pruebas.

El segundo incremento incorpora la administración básica de estos datos y las traducciones castellanas. Permite buscar, filtrar, crear y desactivar alimentos; gestionar los alimentos de una comida; y consultar o editar los perfiles por niño.

El tercer incremento incorpora el catálogo de alimentos a la interfaz normal de Baby Buddy:

- listado paginado;
- búsqueda por nombre;
- filtros por categoría, alérgeno y estado;
- alta y edición según permisos;
- desactivación sin borrado ni pérdida de historial;
- acceso desde la navegación;
- textos y mensajes en castellano.

El cuarto incremento incorpora las operaciones básicas de comidas:

- formulario con niño, fecha y hora, tipo, varios alimentos, cantidad global, preparación, notas y etiquetas;
- alta, edición y borrado según permisos;
- listado básico ordenado de más reciente a más antigua;
- selección exclusiva de alimentos activos en comidas nuevas;
- conservación de alimentos inactivos que ya formen parte de una comida histórica;
- navegación y textos en castellano.

Los filtros avanzados, la vista diaria, la cronología y la edición de perfiles por niño se abordarán en los siguientes incrementos.

El quinto incremento añade:

- un catálogo inicial de 66 alimentos frecuentes en castellano, sin sobrescribir alimentos existentes;
- filtros de comidas por niño, fechas, alimento, categoría, tipo, cantidad y etiqueta;
- agrupación del listado de comidas por fecha local.

La cronología, los cálculos de primera y última ingesta y la edición de perfiles por niño quedan para los siguientes incrementos.

El sexto incremento incorpora:

- listado, filtros, alta y edición de perfiles de alimento por niño;
- valoración independiente de gusto y tolerancia, con notas y fecha de actualización;
- cálculo dinámico de primera ingesta, última ingesta y número de comidas en las que se consumió cada alimento;
- identificación visual de la primera introducción de cada alimento para cada niño en el listado de comidas;
- conservación de alimentos inactivos en perfiles históricos.

Los perfiles de alimentos se ubican en el menú «Mediciones». Las etiquetas de
las comidas se muestran siempre en el formulario de alta y edición, utilizando
el editor de etiquetas común de Baby Buddy.

Estos datos se calculan a partir de las comidas y no se almacenan de forma duplicada. La cronología y el resumen diario continúan pendientes.

El séptimo incremento incorpora:

- comidas integradas en la cronología general y en la cronología de cada niño;
- detalles de alimentos, cantidad, preparación, notas y etiquetas;
- visibilidad y edición condicionadas por los permisos de comidas;
- resumen por día con número de comidas, alimentos diferentes, distribución por categorías y primeras introducciones;
- cálculos sobre el día completo filtrado aunque el listado esté paginado.

El octavo incremento completa las mejoras iniciales del selector:

- los ocho alimentos distintos consumidos más recientemente por cada niño se colocan al principio y se identifican como recientes;
- el orden se actualiza inmediatamente al cambiar de niño;
- los usuarios con permiso para añadir alimentos pueden crearlos sin abandonar el formulario de comida;
- el alta rápida reutiliza la validación del catálogo, impide duplicados y selecciona automáticamente el alimento creado;
- se mantienen casillas nativas, etiquetas asociadas y búsqueda compatible con teclado y pantalla táctil.

El noveno incremento inicia la Fase 5 con la API de alimentación:

- operaciones de consulta, alta, edición y borrado para alimentos, comidas y perfiles de alimento por niño;
- comidas con varios alimentos y etiquetas mediante los formatos habituales de la API;
- filtros por los campos principales, alimentos, categorías, fechas y etiquetas;
- validación de duplicados del catálogo y de alimentos inactivos;
- permisos de modelo y documentación automática mediante el esquema OpenAPI existente.

La importación y exportación se abordarán en un incremento independiente.

Para la importación y exportación se acuerda mantener el funcionamiento común
del código original mediante `django-import-export` y la administración de
Django. Los archivos usarán valores técnicos e identificadores para que puedan
reimportarse sin ambigüedades. Los nombres del niño y de los alimentos se
incluirán como columnas auxiliares de solo lectura.

El siguiente incremento integra la alimentación en la portada de cada niño
mediante una tarjeta con la última comida, el número de comidas y alimentos
diferentes del día, las primeras introducciones y un acceso rápido para añadir
una comida. La tarjeta respeta los permisos de comidas y la opción existente
para ocultar tarjetas vacías.

El informe «Alimentos probados» muestra primera y última ingesta, frecuencia,
variedad semanal, distribución de alimentos diferentes por categorías y
primeras introducciones. Puede limitarse por categoría e intervalo de fechas y
mantiene los cálculos de primera introducción sobre todo el historial del niño.

La documentación de importación y exportación especifica las columnas técnicas
y el orden necesario para reimportar niños, etiquetas, alimentos, comidas y
perfiles conservando sus relaciones.
