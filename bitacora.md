# Bitácora de Desarrollo - Proyecto: Microrred con Batería

**Asignatura:** Fundamentos de Programación (2026)  
**Programa:** Ingeniería Energética - Universidad del Magdalena  
**Estudiante:** Samuel Gómez  

---

## 1. Registro Cronológico de Comandos Ejecutados

| Fecha y Hora | Comando Ejecutado | Descripción / Propósito |
| :--- | :--- | :--- |
| 2026-11-23 11:24 | `New-Item -ItemType Directory -Path ".\Proyecto"` | Creación de la carpeta del proyecto ejecutable. |
| 2026-11-23 11:27 | `& "C:\Users\samue\.local\bin\uv.exe" python list` | Verificación de versiones disponibles del intérprete de Python. |
| 2026-11-23 11:31 | `& "C:\Users\samue\.local\bin\uv.exe" venv .venv` | Creación del entorno virtual aislado `.venv` para el proyecto. |
| 2026-11-23 11:32 | `& "C:\Users\samue\.local\bin\uv.exe" pip install streamlit` | Instalación de Streamlit en el entorno virtual (única librería externa). |
| 2026-11-23 11:33 | `& ".\.venv\Scripts\streamlit.exe" --version` | Confirmación de instalación correcta de Streamlit v1.67.0. |
| 2026-11-23 11:36 | `python test_verificacion.py` | Ejecución del script de pruebas automáticas para comprobar los resultados del Caso de Verificación. |
| 2026-11-23 11:39 | `streamlit run app.py --server.headless true` | Lanzamiento del servidor web de la aplicación interactiva en el puerto 8501. |
| 2026-11-23 17:11 | `& ".\.venv\Scripts\streamlit.exe" run app.py` | Reinicio del servidor Streamlit en el puerto 8501. |
| 2026-11-23 17:11 | `Start-Process "http://localhost:8501"` | Apertura directa de la aplicación en el navegador web del sistema. |
| 2026-11-23 18:36 | `& ".\.venv\Scripts\python.exe" -m py_compile app.py logica.py test_verificacion.py` | Compilación y comprobación estricta de sintaxis de los scripts del proyecto. |
| 2026-11-23 18:36 | `& ".\.venv\Scripts\python.exe" test_verificacion.py` | Ejecución del banco de pruebas unitarias oficiales (Sección 5). |
| 2026-11-23 18:36 | `Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing` | Verificación de respuesta HTTP 200 del servidor web en vivo. |
| 2026-11-23 19:04 | `& ".\.venv\Scripts\python.exe" -m py_compile app.py` | Verificación de sintaxis de app.py tras corrección de badges y eficiencia. |
| 2026-11-23 19:04 | `& ".\.venv\Scripts\python.exe" test_verificacion.py` | Confirmación de 100% OK en banco de pruebas tras ajuste de simulación base. |
| 2026-11-23 19:05 | `Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing` | Confirmación de respuesta HTTP 200 del servidor activo. |

---

## 2. Prompts Clave y Proceso Iterativo con el Agente (Mínimo 5)

### Prompt 1: Creación de la Lógica Base y Caso de Verificación
* **Prompt del estudiante:**  
  > *"Construye la lógica de la microrred en un archivo `logica.py` usando solo conceptos vistos en clase (funciones con `return`, listas, diccionarios, condicionales y ciclos). Debe evaluar para cada hora la generación y carga: si sobra, cargar la batería hasta su capacidad y verter el resto; si falta, descargar la batería hasta 0 y comprar el faltante a la red. Comprueba que el caso oficial dé exactamente 3, 7, 10, 0 kWh, 2 kWh comprados, 4 kWh vertidos y 88.24% sin red."*
* **Qué se analizó y generó:**  
  Se crearon las funciones modulares `simular_hora()` y `simular_microrred()` en `logica.py`. Se escribió `test_verificacion.py` confirmando un 100% de coincidencia con la Sección 5 de la pauta.
* **Revisión del estudiante:**  
  Se revisó la función `simular_hora()` para entender el orden de prioridad: primero el sol alimenta la carga; luego el excedente va a la batería; lo que no cabe se vierte; y solo si el sol y la batería no alcanzan, se compra a la red.

---

### Prompt 2: Robustez, Manejo de Archivos JSON y Validaciones
* **Prompt del estudiante:**  
  > *"Implementa la lectura de `datos/entrada.json`, guardado automático de `datos/salida.json` y una función `validar_datos()` que revise si el SOC inicial está fuera de rango, si hay valores negativos o si hay una cantidad de horas diferente a 24, emitiendo alertas claras sin que el programa se caiga."*
* **Qué se analizó y generó:**  
  Se implementaron `cargar_datos()`, `guardar_resultados()` y `validar_datos()` utilizando el módulo nativo `json`.
* **Revisión del estudiante:**  
  Se comprobó que si un usuario ingresa una capacidad de 0 o un SOC inicial mayor que la capacidad, el sistema lo detecta, lo notifica en el panel lateral y ajusta el cálculo de forma segura.

---

### Prompt 3: Integración del Diseño Visual en Streamlit
* **Prompt del estudiante:**  
  > *"Usa el diseño visual provisto con Tailwind CSS, tema oscuro/claro, diagrama de flujo energético en SVG con flechas animadas y badges de kWh, indicador de batería con nivel dinámico en kWh/% y línea de tiempo interactiva. La interfaz debe montarse en `app.py` conectada directamente a los datos calculados por `logica.py`."*
* **Qué se analizó y generó:**  
  Se integró el dashboard en `app.py` mediante `streamlit.components.v1.html`, pasando los resultados reales calculados por `logica.py` en formato JSON al cliente JavaScript.
* **Revisión del estudiante:**  
  Se ajustó la grilla de la línea de tiempo (`gridTemplateColumns`) para que si el perfil tiene 4 horas (caso de verificación) o 24 horas (caso rural), las celdas se distribuyan equitativamente sin cortarse.

---

### Prompt 4: Implementación de los Retos Funcionales
* **Prompt del estudiante:**  
  > *"Para el reto funcional (10 puntos), implementa en `logica.py` el cálculo de la capacidad mínima de batería para no comprar energía a la red en todo el día, y además una simulación con eficiencia de carga/descarga (90%) y un comparativo de variable global vs return para la sustentación."*
* **Qué se analizó y generó:**  
  Se añadieron las funciones `buscar_capacidad_minima_sin_red()`, `simular_con_eficiencia()` y `simular_hora_con_global()`, integrándolas como controles interactivos en la barra lateral de Streamlit.
* **Revisión del estudiante:**  
  Se comprendió que si la generación total es menor a la demanda total ($\sum Gen < \sum Dem$), físicamente ninguna batería puede evitar la compra de red.

---

### Prompt 5: Pruebas Unitarias Finales y Preparación de Sustentación
* **Prompt del estudiante:**  
  > *"Verifica que la aplicación corra de forma fluida a 60 FPS, que el botón de reproducir/pausar avance la simulación celda por celda y genera el archivo `LEEME.txt` con la explicación de cómo defender el proyecto ante el docente."*
* **Qué se analizó y generó:**  
  Se realizó la verificación de renderizado en navegador headless con captura de pantalla y se redactaron `LEEME.txt` y esta `bitacora.md`.

---

### Prompt 6 (Mejora del Estudiante): Simplificación Visual de la Interfaz
* **Prompt del estudiante:**  
  > *"Quita la guía de sustentación para el docente: fórmulas y lógicas de solución, no es necesario que lo muestres en la aplicación."*
* **Qué se analizó y ajustó:**  
  Se eliminó el bloque expandible inferior de `app.py` para dejar la pantalla completamente limpia, enfocada en el diseño visual de alto nivel, el diagrama de flujo y el monitor interactivo sin saturar al usuario con texto explicativo.
* **Revisión del estudiante:**  
  La interfaz quedó despejada y fiel al diseño original, conservando las explicaciones técnicas exclusivamente en `LEEME.txt` y `bitacora.md`.

---

### Prompt 7 (Ajuste de Diseño): Expansión a Pantalla Completa y Eliminación de Márgenes
* **Prompt del estudiante:**  
  > *"Haz que la sección que dice MICROGRID ocupe los espacios grises que hacen falta por cubrir, no cambies más nada."*
* **Qué se analizó y ajustó:**  
  Se eliminaron los márgenes y rellenos internos por defecto de Streamlit (`padding: 0` en `.block-container`, ocultamiento del `stHeader` superior y sincronización del color de fondo `#0B131E`). Además, se eliminó la restricción de ancho fijo (`max-w-[1440px]`) en el encabezado y cuerpo del dashboard, pasando a `w-full` para que ocupe el 100% del espacio visible hasta los bordes.
* **Revisión del estudiante:**  
  El monitor se expande de extremo a extremo cubriendo todos los espacios vacíos y unificando el fondo sin alterar ninguna otra funcionalidad.

---

### Prompt 8 (Ajuste de Continuidad y Enfoque en Reto Funcional): Flujo Continuo y Reto de Eficiencia
* **Prompt del estudiante:**  
  > *"Pero no hagas que se corte de esa manera el diseño, hazlo que sea continuo, también solo deja el reto funcional de Agregar eficiencia de carga y descarga (por ejemplo 90 %) y quita esas opciones de la barra lateral de la izquierda, no cambies más nada solo eso."*
* **Qué se analizó y ajustó:**  
  1. **Continuidad del diseño sin cortes:** Se eliminó la barra de desplazamiento interna del iframe (`scrolling=False`) y se aumentó la altura base a 1700px con auto-redimensionamiento dinámico vía `streamlit:setFrameHeight`. Se adaptó además la grilla a `md:grid-cols-12` para mantener el Diagrama de Flujo y el Indicador de Batería alineados lado a lado, permitiendo una lectura vertical continua y natural de toda la página sin divisiones ni cortes.
  2. **Reto Funcional exclusivo:** Se limpió la barra lateral eliminando el selector de múltiples retos y dejando únicamente el deslizador de **Eficiencia de Batería (η)** (con valor predeterminado de 0.90 / 90%), conectado directamente al modelo matemático en `logica.py`.
* **Revisión del estudiante:**  
  La interfaz ahora es completamente fluida y continua, y la barra lateral contiene solo el control de eficiencia solicitado sin opciones adicionales innecesarias.

---

### Prompt 9 (Resolución de Error en Caliente): Recarga Dinámica de Módulo y Sincronización
* **Prompt del estudiante:**  
  > *"Me sale este error: TypeError: simular_microrred() got an unexpected keyword argument 'eficiencia', corrígelo."*
* **Causa técnica del error:**  
  Streamlit mantenía en memoria (`sys.modules`) la versión anterior de `logica.py` que no recibía el argumento `eficiencia`, ya que el recargador automático de Streamlit solo observa `app.py` y no invalida automáticamente los módulos importados en caché.
* **Solución aplicada:**  
  Se añadió `importlib.reload(logica)` al inicio de `app.py` para forzar la sincronización en vivo del módulo, se limpió la caché de compilación `__pycache__` y se reinició el proceso de Streamlit, restableciendo la comunicación exitosa (código HTTP 200).

---

### Prompt 10 (Corrección de Solapamiento y Rediseño Tipográfico Moderno): Diagrama Responsivo y Plus Jakarta Sans
* **Prompt del estudiante:**  
  > *"Esta parte sale mal, corrige, también cambia el estilo de letra a una más simple y profesional, que no se vea tan genérica y el diseño hazlo diferente y más moderno, no cambies más nada solo eso."*
* **Causa del solapamiento en el diagrama:**  
  Los nodos de "Carga Eléctrica" y "Red Externa" utilizaban posicionamiento con píxeles fijos (`left-[305px]` y `right-[25px]`) dentro de un lienzo responsivo; al reducirse el ancho en pantalla, colisionaban entre sí y el texto quedaba cortado.
* **Solución aplicada:**  
  1. **Distribución geométrica proporcional:** Se reorganizaron los cuatro nodos en columnas porcentuales equidistantes (Sol y Batería al 14%, Carga al 50% y Red al 86%), recalculando los vectores SVG de flujo y las etiquetas numéricas para garantizar que nunca colisionen en ninguna resolución.
  2. **Nueva tipografía profesional:** Se reemplazó la fuente genérica por **Plus Jakarta Sans** (estilo moderno de ingeniería de software) combinada con **JetBrains Mono** para todas las lecturas de telemetría y valores en kWh.
  3. **Estilo visual elevado:** Se implementó una estética SCADA de alta tecnología con micro-bordes luminosos, tarjetas con efecto cristal templado y mejor contraste para proyección en aula.

---

### Prompt 11 (Corrección de Capas y Espaciado de Etiquetas): Badges con Prioridad Z-30 y Despeje de Canales
* **Prompt del estudiante:**  
  > *"Sale así, algunos datos salen detrás de los cuadrados, corrige eso."*
* **Causa técnica identificada:**  
  Las etiquetas numéricas flotantes (badges de kWh sobre los flujos de flechas) tenían un orden de apilamiento inferior (`z-10`) al de las tarjetas de los nodos (`z-20`). Al haber poco espacio horizontal, los bordes de las tarjetas tapaban el inicio de los números (por ejemplo, mostrando `.00 kWh` o `.93 kWh`).
* **Solución implementada:**  
  1. **Prioridad de capa absoluta:** Se elevó el nivel de apilamiento de todas las etiquetas de flujo a `z-30`, asegurando que siempre se dibujen por encima de cualquier otro elemento sin quedar ocultas.
  2. **Ajuste de dimensiones y canales de flujo:** Se compactaron los anchos de los bloques a 90px–100px y se abrieron los canales de separación (`Sol/Bat` al 12%, `Carga` al 48% y `Red` al 90%), situando cada badge en el punto medio exacto de su trayectoria con márgenes libres a ambos costados.

---

### Prompt 12 (Espaciado Estético de Nodos y Conmutación en Tiempo Real sin Parpadeo): Margen de Bordes y Transición Instantánea
* **Prompt del estudiante:**  
  > *"Ahora algunos datos salen muy cerca a los cuadrados, aléjalos un poco para que se vea un poco separado y estético, no cambies más nada de la animación, también el cuadro de red externa se ve un poco recortado, haz que quepa todo ampliando el espacio y el de paneles solares y almacén también se ven muy pegados al borde, corrige eso.*  
  > *Otra cosa, también en la barra lateral, cuando cambio de microrred rural a caso de verificación el programa parpadea, hazlo de tal manera que no parpadee y solo se cambie la información en tiempo real."*
* **Causas identificadas:**  
  1. **Espaciado y márgenes de nodos:** Los nodos de la izquierda estaban fijados al 12% (muy cerca del borde exterior del contenedor) y la Red Externa al 90% (provocando desborde y recorte en resoluciones compactas). Las etiquetas flotantes se encontraban en posiciones intermedias que colisionaban visualmente con las esquinas de las tarjetas.
  2. **Parpadeo al alternar escenarios:** Al cambiar la selección en el `st.selectbox` de la barra lateral, Streamlit reejecutaba el script Python de principio a fin, destruyendo el `iframe` y reconstruyéndolo, lo que generaba un destello o parpadeo blanco visible durante la recarga del documento HTML y sus fuentes.
* **Soluciones implementadas:**  
  1. **Rebalanceo geométrico simétrico del diagrama (ViewBox 600x320):**  
     - **Columna izquierda (Paneles Solares y Almacén):** Se desplazaron al `18%` (X=108), dejando más de 60px de margen respecto al borde izquierdo.
     - **Columna central (Carga Eléctrica):** Centrada exactamente al `50%` (X=300).
     - **Columna derecha (Red Externa):** Reposicionada al `82%` (X=492), garantizando un margen amplio de más de 60px respecto al borde derecho y eliminando cualquier recorte.
     - **Separación de badges de flujo:** Se reubicaron en los puntos medios libres de los canales (`34%` para flujos solares y de descarga, `66%` para red y vertido, y `18% / top:50%` para el vector solar-batería), con propiedad `whitespace-nowrap` y holgura de más de 40px a cada lado respecto a las cajas.
  2. **Alternancia instantánea en tiempo real sin parpadeo (0 ms de latencia):**  
     - Se precalculan en Python ambos escenarios estándar (`scenarios_payload` con *Microrred Rural 1* y *Caso de Verificación*) y se inyectan en el cliente JavaScript.
     - Se integró un selector rápido de escenarios tipo *pill* (`☀️ Rural 1 (24h)` / `⭐ Verificación (4h)`) directamente en la barra superior del monitor.
     - La función `switchScenario(key)` en JavaScript actualiza en caliente los datos de las 24h / 4h, totales acumulados, capacidad de batería, celdas de la línea de tiempo y gráficas de flujo al instante, sin recargar la página, sin destruir el iframe y sin ningún parpadeo.
     - Se fijó el fondo persistente del `iframe` y contenedor a `#0B131E`, eliminando cualquier destello en caso de utilizar también el selector de la barra lateral.

---

## 3. Preparación para Preguntas y Cambios en Vivo del Docente

| Posible Cambio del Docente | Archivo a Modificar | Línea / Función | Explicación Técnica |
| :--- | :--- | :--- | :--- |
| **Cambiar umbral de color de batería** (ej. advertencia al 30% en vez del 20%) | `app.py` | Función JS `updateHour()` (aprox. línea 835) | Cambiar la condición `data.battPct >= 20` por `data.battPct >= 30`. |
| **Cambiar capacidad o SOC inicial** | Barra Lateral Streamlit / `datos/entrada.json` | Controles numéricos o archivo JSON | La función `simular_microrred()` recalcula instantáneamente todas las 24 horas. |
| **Añadir una hora extra al perfil** | `datos/entrada.json` | Lista `"horas"` | Agregar un par `[gen, carga]`. La línea de tiempo pasa dinámicamente de $N$ a $N+1$ celdas. |
| **Explicar por qué `return` es mejor que `global`** | `logica.py` | Función `simular_hora()` vs `simular_hora_con_global()` | `return` evita efectos colaterales (funciones puras), permite testear funciones de forma aislada y no genera conflictos en aplicaciones web concurrentes. |
