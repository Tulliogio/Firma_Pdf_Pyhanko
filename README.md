# ✒️ Aplicación Web de Firma Digital de PDFs

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.x-black.svg)
![PyHanko](https://img.shields.io/badge/PyHanko-0.20.0-green.svg)


Una aplicación web sencilla y autocontenida para firmar digitalmente documentos PDF. Sube tu certificado PFX, tus documentos, elige la posición y ¡listo!

Este proyecto fue desarrollado como una solución práctica para aplicar firmas digitales visibles a documentos PDF sin necesidad de instalar software de escritorio pesado.

## ✨ Vista Previa


*(Imagen de ejemplo del dashboard principal)*

## 🚀 Características Principales

-   **Firma en Lote:** Sube y firma múltiples archivos PDF en una sola operación.
-   **Certificado PFX:** Utiliza certificados estándar de la industria en formato `.pfx` (PKCS#12).
-   **Firma Visible:** Añade una firma visible en el documento, no solo una firma criptográfica invisible.
-   **Posicionamiento Flexible:**
    -   Elige entre posiciones predefinidas (esquinas, centro).
    -   Define coordenadas personalizadas para un control total.
-   **Selección de Página:** Especifica en qué página del documento quieres que aparezca la firma.
-   **Interfaz Limpia:** Una interfaz web sencilla y directa construida con Flask y HTML5.
-   **Seguridad Efímera:** Los certificados y documentos subidos se eliminan del servidor inmediatamente después de ser procesados.

## 🔧 Pila Tecnológica (Tech Stack)

-   **Backend:** Python 3
-   **Framework Web:** Flask
-   **Librería de Firma PDF:** PyHanko
-   **Frontend:** HTML5, CSS3, JavaScript (vanilla)

## ⚙️ Instalación y Puesta en Marcha

Sigue estos pasos para ejecutar el proyecto en tu máquina local.

**1. Clona el Repositorio**
```bash
git clone https://github.com/tu_usuario/tu_repositorio.git
cd tu_repositorio
```
*(Reemplaza `tu_usuario/tu_repositorio` con la URL de tu repositorio si lo subes a GitHub)*

**2. Crea y Activa un Entorno Virtual**
Es una buena práctica para aislar las dependencias del proyecto.
```bash
# Crear el entorno
python -m venv venv

# Activarlo (Windows)
.\venv\Scripts\activate

# Activarlo (macOS/Linux)
source venv/bin/activate
```

**3. Instala las Dependencias**
El archivo `requirements.txt` contiene todo lo necesario.
```bash
pip install -r requirements.txt
```

**4. Ejecuta la Aplicación**
```bash
python app.py
```

**5. ¡Listo!**
Abre tu navegador web y ve a la siguiente dirección:
[**http://127.0.0.1:5000**](http://127.0.0.1:5000)

## 📋 Modo de Uso

1.  **Carga tu Certificado:** Selecciona tu archivo `.pfx`.
2.  **Introduce la Contraseña:** Escribe la contraseña de tu certificado.
3.  **Sube tus Documentos:** Selecciona uno o varios archivos PDF que deseas firmar.
4.  **Configura la Firma:**
    -   Elige el número de página.
    -   Selecciona una posición predefinida o introduce coordenadas personalizadas.
5.  **Haz clic en "Firmar Documentos"**.
6.  En la página de resultados, descarga tus archivos firmados uno por uno.

## ⚠️ Consideraciones de Seguridad IMPORTANTES

Este proyecto es una excelente **prueba de concepto**, pero para un uso en **producción**, se deben abordar las siguientes vulnerabilidades:

-   **TRÁFICO NO CIFRADO (HTTP):**
    > **¡Advertencia!** La aplicación se ejecuta sobre HTTP. Esto significa que tu certificado `.pfx` y, más importante aún, **tu contraseña**, viajan en **texto plano** a través de la red. Un atacante en la misma red podría interceptarlos.
    > **Solución:** Es **obligatorio** configurar un servidor de producción (como Gunicorn o Nginx) y habilitar **HTTPS (TLS/SSL)** para cifrar toda la comunicación.

-   **Protección contra Fuerza Bruta:** No hay límite de intentos de inicio de sesión. Un atacante podría intentar adivinar la contraseña del certificado repetidamente. Se recomienda implementar un sistema de **limitación de intentos (rate limiting)**.

-   **Validación de Archivos:** La validación de los archivos subidos es básica. Para mayor seguridad, se debería realizar un análisis más profundo para detectar archivos PDF maliciosos.

-   **Mensajes de Error:** Los mensajes de error en modo `debug` pueden revelar información sensible sobre la estructura interna de la aplicación. En producción, el modo `debug` debe estar desactivado.

### 1. Dashboard Principal
El usuario accede a la interfaz principal donde debe proporcionar todos los datos necesarios.

![Dashboard de la aplicación](./img/dashboard.png)

### 2. Página de Resultados
Tras el procesamiento, la aplicación muestra una lista de los documentos firmados y los posibles errores.

![Página de resultados](./img/resultado.png)

### 3. PDF Firmado
El documento final contiene una firma digital visible que puede ser validada en cualquier lector de PDF.

![Ejemplo de PDF firmado](./img/firma.png)