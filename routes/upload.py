from flask import Blueprint, render_template, request
import os
import tempfile
import logging
from werkzeug.utils import secure_filename

from services.utils_upload_meti import process_meti_file
from services.utils_upload_orika import process_orika_file
from services.utils_upload_vente_meti import process_vente_meti_file

upload_bp = Blueprint('upload', __name__)
logger = logging.getLogger(__name__)

@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        logger.info("Upload route accessed")
        error_message = None
        success_message = None

        meti_data = []
        meti_summary = {}
        orika_data = []
        orika_summary = {}
        vente_meti_data = []

        try:
            meti_file = request.files.get('meti_file')
            orika_file = request.files.get('orika_file')
            vente_meti_file = request.files.get('vente_meti_file')

            header_row = int(request.form.get('header_row', 3))
            data_row = int(request.form.get('data_row', 4))

            if not meti_file or not orika_file:
                raise ValueError("Les fichiers METI et ORIKA sont requis.")

            with tempfile.TemporaryDirectory() as tmpdir:
                meti_path = os.path.join(tmpdir, secure_filename(meti_file.filename))
                orika_path = os.path.join(tmpdir, secure_filename(orika_file.filename))
                meti_file.save(meti_path)
                orika_file.save(orika_path)

                vente_meti_path = None
                if vente_meti_file:
                    vente_meti_path = os.path.join(tmpdir, secure_filename(vente_meti_file.filename))
                    vente_meti_file.save(vente_meti_path)

                logger.info("Traitement METI...")
                meti_data, meti_summary = process_meti_file(meti_path, header_row, data_row)
                logger.info(f"✅ METI : {meti_summary}")

                logger.info("Traitement ORIKA...")
                orika_data, orika_summary = process_orika_file(orika_path)
                logger.info(f"✅ ORIKA : {orika_summary}")

                if vente_meti_path:
                    logger.info("Traitement Vente METI...")
                    vente_meti_data = process_vente_meti_file(vente_meti_path)
                    logger.info(f"✅ Vente METI : {len(vente_meti_data)} lignes")

                success_message = "✅ Import réalisé avec succès."

        except Exception as e:
            error_message = f"❌ Erreur lors de l'import : {str(e)}"
            logger.error(error_message)

        return render_template(
            "dashboard.html",
            error_message=error_message,
            success_message=success_message,
            meti_summary=meti_summary,
            orika_summary=orika_summary,
            meti_rows=meti_data[:10] if meti_data else [],
            orika_preview=[list(r.values()) for r in orika_data[:10]] if orika_data else [],
            orika_columns=list(orika_data[0].keys()) if orika_data else [],
            vente_meti_rows=[list(r.values()) for r in vente_meti_data[:10]] if vente_meti_data else [],
            vente_meti_columns=list(vente_meti_data[0].keys()) if vente_meti_data else []
        )

    return render_template("dashboard.html")
