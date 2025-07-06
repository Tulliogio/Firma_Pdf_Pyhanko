import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, send_from_directory, url_for

from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.writer import copy_into_new_writer
from pyhanko.sign.fields import SigFieldSpec, append_signature_field
from pyhanko.sign.signers.pdf_signer import PdfSignatureMetadata
from pyhanko.sign.signers import SimpleSigner
from pyhanko.sign import signers as pdf_signers

# --- Configuración de Flask ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SIGNED_FOLDER'] = 'signed_pdfs'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # Límite de 32 MB para subidas

# --- Configuración del Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Lógica de Firma (Adaptada del script original) ---

# Diccionario de posiciones para no tener que calcularlo en el frontend
POSITIONS = {
    "bottom_left": {"name": "Esquina inferior izquierda", "box": (50, 50, 200, 100)},
    "bottom_right": {"name": "Esquina inferior derecha", "box": (400, 50, 550, 100)},
    "top_left": {"name": "Esquina superior izquierda", "box": (50, 700, 200, 750)},
    "top_right": {"name": "Esquina superior derecha", "box": (400, 700, 550, 750)},
    "center": {"name": "Centro del documento", "box": (250, 350, 400, 400)},
}

def get_pdf_page_count(reader):
    """Función para obtener el número de páginas de un PDF (sin cambios)."""
    try:
        return len(reader.root['/Pages']['/Kids'])
    except (KeyError, TypeError):
        try:
            return len(reader.root.pages)
        except (AttributeError, TypeError):
            try:
                return reader.get_num_pages()
            except AttributeError:
                pages_obj = reader.root.get('/Pages')
                if pages_obj and '/Count' in pages_obj:
                    return int(pages_obj['/Count'])
                return 1 # Fallback
    return 1


def sign_single_pdf(input_pdf_path, output_pdf_path, signer, signature_box, page_number):
    """
    Firma un único archivo PDF. Esta función es llamada para cada archivo subido.
    Devuelve (True, mensaje_exito) o (False, mensaje_error).
    """
    try:
        with open(input_pdf_path, 'rb') as inf:
            reader = PdfFileReader(inf)
            total_pages = get_pdf_page_count(reader)

            if page_number >= total_pages:
                error_msg = f"La página {page_number + 1} no existe en '{os.path.basename(input_pdf_path)}' (tiene {total_pages} páginas)."
                logger.error(error_msg)
                return False, error_msg

            sig_field = SigFieldSpec(
                sig_field_name=f"Signature-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                box=signature_box,
                on_page=page_number
            )

            writer = copy_into_new_writer(reader)
            append_signature_field(writer, sig_field)

            with open(output_pdf_path, 'wb') as outf:
                pdf_signer = pdf_signers.PdfSigner(
                    signature_meta=PdfSignatureMetadata(
                        field_name=sig_field.sig_field_name,
                        reason="Firma electrónica",
                        location="Documento digital"
                    ),
                    signer=signer
                )
                pdf_signer.sign_pdf(writer, output=outf)
            
            success_msg = f"'{os.path.basename(input_pdf_path)}' firmado correctamente en la página {page_number + 1}."
            logger.info(success_msg)
            return True, os.path.basename(output_pdf_path)

    except Exception as e:
        error_msg = f"Error al firmar '{os.path.basename(input_pdf_path)}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


# --- Rutas de la Aplicación Web ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # --- 1. Recoger datos del formulario ---
        pfx_file = request.files.get('pfx_file')
        pfx_password = request.form.get('pfx_password')
        pdf_files = request.files.getlist('pdf_files')
        position_choice = request.form.get('position')
        page_number_str = request.form.get('page_number', '1')

        # --- 2. Validaciones básicas ---
        if not pfx_file or not pfx_password or not pdf_files:
            return render_template('index.html', error="Por favor, completa todos los campos y sube los archivos necesarios.", positions=POSITIONS)
        
        # --- 3. Procesar y guardar archivos subidos ---
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['SIGNED_FOLDER'], exist_ok=True)

        pfx_filename = secure_filename(pfx_file.filename)
        pfx_path = os.path.join(app.config['UPLOAD_FOLDER'], pfx_filename)
        pfx_file.save(pfx_path)

        # --- 4. Cargar el firmante (Signer) ---
        try:
            signer = SimpleSigner.load_pkcs12(
                pfx_file=pfx_path,
                passphrase=pfx_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error al cargar el certificado PFX: {e}")
            return render_template('index.html', error=f"Error con el certificado o la contraseña: {e}", positions=POSITIONS)

        # --- 5. Determinar la posición de la firma ---
        if position_choice == 'custom':
            try:
                x1 = int(request.form.get('x1'))
                y1 = int(request.form.get('y1'))
                x2 = int(request.form.get('x2'))
                y2 = int(request.form.get('y2'))
                if x1 >= x2 or y1 >= y2:
                    raise ValueError("Coordenadas inválidas (x1>=x2 o y1>=y2)")
                signature_box = (x1, y1, x2, y2)
            except (ValueError, TypeError):
                return render_template('index.html', error="Las coordenadas personalizadas deben ser números válidos.", positions=POSITIONS)
        else:
            signature_box = POSITIONS[position_choice]['box']

        # --- 6. Procesar cada PDF ---
        page_number = int(page_number_str) - 1 if page_number_str.isdigit() and int(page_number_str) > 0 else 0
        
        signed_files = []
        error_messages = []

        for pdf_file in pdf_files:
            pdf_filename = secure_filename(pdf_file.filename)
            input_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            output_pdf_path = os.path.join(app.config['SIGNED_FOLDER'], f"signed_{pdf_filename}")
            pdf_file.save(input_pdf_path)

            success, message = sign_single_pdf(
                input_pdf_path, output_pdf_path, signer, signature_box, page_number
            )
            if success:
                signed_files.append(message)
            else:
                error_messages.append(message)

        # Limpiar archivos subidos después de usarlos
        try:
            os.remove(pfx_path)
            for pdf_file in pdf_files:
                 os.remove(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pdf_file.filename)))
        except OSError as e:
            logger.warning(f"No se pudo limpiar un archivo temporal: {e}")

        return render_template('result.html', signed_files=signed_files, errors=error_messages)

    # Método GET: simplemente muestra el formulario
    return render_template('index.html', positions=POSITIONS)


@app.route('/download/<path:filename>')
def download_file(filename):
    """Ruta para descargar los archivos firmados."""
    return send_from_directory(app.config['SIGNED_FOLDER'], filename, as_attachment=True)


if __name__ == "__main__":
    # Crear carpetas si no existen
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SIGNED_FOLDER'], exist_ok=True)
    # Ejecutar la aplicación
    app.run(debug=True, host='0.0.0.0')