# Veeduría Ciudadana Cicuco Transparente - Plataforma Oficial (Python)

Plataforma web institucional y ciudadana para la **Veeduría Ciudadana Cicuco Transparente** (Cicuco, Bolívar, Colombia), bajo el lema *«Fiscalización, Transparencia, Vigilancia de Recursos y Justicia Social»*, construida en **Python**, con base de datos local SQLite y almacenamiento persistente de contratos y evidencias.

Amparada en el marco legal de la **Ley 850 de 2003 (Estatuto de Veedurías Ciudadanas)**, la **Ley 1712 de 2014 (Transparencia y Acceso a la Información)** y los **Artículos 20, 74, 103 y 270 de la Constitución Política de Colombia**.

---

## 🏛️ Estructura en 4 Catálogos Principales

La plataforma se encuentra dividida en 4 módulos o catálogos accesibles desde la barra superior de navegación:

### 1. Catálogo de Inicio & Presentación
- **Presentación Institucional:** Misión cívica, principios rectores de autonomía e independencia de la veeduría en Cicuco.
- **La Ley que la Cubre:** Explicación detallada del amparo legal:
  - **Ley 850 de 2003 (Artículos 1, 6, 15 y 16):** Naturaleza jurídica, derechos para solicitar contratos e inspeccionar obras, y deberes de objetividad.
  - **Constitución Política (Artículos 103 y 270):** Mandato de la democracia participativa para que el pueblo vigile la gestión estatal.
  - **Ley 1712 de 2014:** Principio de Máxima Publicidad donde toda la contratación pública es de libre acceso.
- **Ficha Técnica Oficial:** Registro radicado ante la Personería Municipal de Cicuco y RUES (`VED-098842-CO`).
- **Directorio de Comités Técnicos:** Obras e Infraestructura, Alimentación Escolar (PAE), Salud y Saneamiento Básico.
- **Métricas en Vivo:** Presupuesto fiscalizado, contratos monitoreados y alertas preventivas emitidas.

### 2. Catálogo de Contratos Públicos Fiscalizados
- **Vista Pública:** Directorio de contratos del municipio con buscador en tiempo real por palabra clave, sector (Obras, PAE, Salud, Agua) y estado.
- **Indicadores Comparativos:** Barras interactivas de **Avance Físico (% de obra construida)** vs. **Ejecución Financiera (% del dinero girado al contratista)**.
- **Descarga de Contratos:** Botón directo para visualizar o descargar los documentos y pliegos contractuales (PDFs subidos por el administrador).
- **Ficha Técnica Detallada:** Modal con antecedentes, entidad contratante, contratista, valor y observaciones técnicas.

### 🔐 Apartado de Administrador (Oculto para los Usuarios)
- **Acceso Discreto:** No es visible en el menú general. Para acceder:
  - Haz clic en el icono discreto de candado **«Gestión Interna»** ubicado en el pie de página (footer), o
  - Presiona el atajo de teclado: `Ctrl + Shift + A`.
- **Autenticación Protegida:** Requiere contraseña de administrador: `Veduria1969`.
- **Funcionalidades del Administrador:**
  - **Subir Contratos Manualmente:** Formulario completo para ingresar código, objeto, entidad, contratista, monto, porcentajes de avance físico/financiero y **subir el archivo PDF o Word del contrato** directamente al servidor local.
  - **Editar y Eliminar Contratos:** Modificar avances o estados a medida que avanza la obra.
  - **Bandeja de Denuncias:** Revisar reportes enviados por la comunidad, ver fotografías de prueba adjuntas y actualizar el estado de seguimiento.
  - **Ajustes:** Cambiar el correo oficial o actualizar la contraseña maestra.

### 3. Catálogo de Blindaje Legal contra Demandas
Compendio exhaustivo de herramientas jurídicas diseñado para **proteger e inmunizar a los veedores y ciudadanos contra demandas por calumnia, injuria o censura previa**:
- **Constitución Política (Artículos 20, 74 y 270):** Libertad irrestricta de información, prohibición absoluta de la censura y acceso público incondicional a documentos oficiales.
- **Jurisprudencia Vinculante de la Corte Constitucional:**
  - **Sentencia C-292 de 2003:** Los funcionarios públicos y contratistas estatales están sujetos a un mayor umbral de tolerancia y escrutinio público.
  - **Sentencia T-263 de 2010:** Prohibición del acoso judicial (*SLAPP*). Se prohíbe el uso de denuncias penales como mecanismo de amedrentamiento hacia los veedores.
  - **Sentencia T-063 de 2017:** Las denuncias y alertas ciudadanas formuladas de buena fe basadas en datos del SECOP o hechos observables no configuran delito de calumnia ni injuria.
- **Ley 2195 de 2022:** Medidas de protección e indemnidad al denunciante de actos de presunta corrupción.
- **Decálogo del Veedor Inmune:** Reglas prácticas de redacción para formular alertas blindadas técnicamente.
- **Modelos y Minutas Descargables con 1 Clic:**
  - Modelo de Derecho de Petición de Información Contractual (Ley 1755 / Ley 1712).
  - Formato de Alerta Temprana Comunitaria de Obra.
  - Minuta de Blindaje y Rechazo a Intimidaciones o Amenazas de Demanda.

### 4. Catálogo de Contacto, Denuncias y Reportes Municipales
- **Correo Oficial Central:** `veduriaciudadanatransparente@gmail.com` destacado en la cabecera, pie de página y formulario, con botón de copia rápida con 1 clic.
- **Ventanilla de Radicación Ciudadana:**
  - Formulario para denunciar irregularidades en obras viales, retrasos, alimentos del PAE, puestos de salud o servicios públicos.
  - **Opción de Radicación 100% Anónima y Confidencial:** Protegida bajo la Ley 1712 de 2014 y Ley 2195 de 2022.
  - **Carga de Evidencia:** Posibilidad de adjuntar fotos de la obra o archivos PDF (guardados en el servidor para que el veedor los revise).
  - **Código de Radicado Oficial:** Generación automática de código único (ej. `RAD-2026-3589`).
  - **Integración con Correo:** Botón para generar y abrir directamente el correo con todo el reporte prellenado para remitirlo a `veduriaciudadanatransparente@gmail.com`.
- **Rastreador de Radicados en Línea:** Cualquier ciudadano puede ingresar su código y consultar el estado y las notas de actuación del comité veedor.

---

## 🚀 Puesta en Marcha en tu Equipo

### Opción 1: Inicio Rápido (Recomendado)
Simplemente haz doble clic en el archivo:
```
iniciar.bat
```
El script verificará Python, arrancará el servidor local y abrirá automáticamente tu navegador en:
**`http://127.0.0.1:5000/`**

### Opción 2: Inicio por Línea de Comandos
```bash
# 1. Asegúrate de tener Python instalado (Python 3.10 o superior)
python --version

# 2. Instalar dependencias requeridas (Flask)
python -m pip install -r requirements.txt

# 3. Iniciar el servidor web
python app.py
```

---

## 🔑 Credenciales de Acceso al Panel de Administrador

- **Ubicación:** Pie de página (footer) -> Enlace discreto con icono de candado **«Gestión Interna»** o atajo **`Ctrl + Shift + A`**.
- **Contraseña de Acceso:** `Veduria1969`
- *(Puedes cambiar esta contraseña en cualquier momento dentro de la pestaña "Ajustes & Contraseña" del panel de administrador).*

---

## 🛠️ Tecnologías Empleadas

- **Lenguaje Backend:** Python 3 (Flask 3.1)
- **Base de Datos:** SQLite local (`veeduria.db`) con transacciones seguras y hashing de contraseñas (`Werkzeug Security`)
- **Almacenamiento de Archivos:** Gestión local de subida de contratos y evidencias en `/uploads/`
- **Frontend:** HTML5 semántico, Tailwind CSS y Vanilla JavaScript nativo
- **Iconografía:** Lucide Icons
