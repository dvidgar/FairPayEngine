import os
from flask import (
    Flask,
    render_template,
    request,
    abort,
    send_from_directory,
    after_this_request,
    jsonify,
)
from werkzeug.utils import secure_filename
from utils import clear_dir
import glob
from constants import (
    OUTPUT_PATH,
    UPLOAD_INVOICE_PATH,
    UPLOAD_POINTAGES_PATH,
    UPLOAD_PATH,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB limit
app.config["UPLOAD_EXTENSION"] = ".xlsm"
app.config["UPLOAD_PATH"] = UPLOAD_PATH


# Simple in-memory status store
download_status = {}


@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413


@app.route("/")
def index():
    # Clear previous uploads and outputs on loading the main page
    clear_dir(app.config["UPLOAD_PATH"])
    clear_dir("./output")
    download_status["started"] = False

    # files = os.listdir(app.config['UPLOAD_PATH'])
    print(glob.glob("./*"))
    return render_template("index.html", files=[])


# @app.route('/', methods=['POST'])
# def upload_files():
#     uploaded_file = request.files['file']
#     filename = secure_filename(uploaded_file.filename)
#     if filename != '':
#         file_ext = os.path.splitext(filename)[1]
#         if file_ext != app.config['UPLOAD_EXTENSION']:
#             return "Invalid file", 400
#         uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
#         print(f"Uploaded file: {filename}")
#     return '', 204


@app.route("/", methods=["POST"])
def upload_pointages():
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename != "":
        file_ext = os.path.splitext(filename)[1]
        if file_ext != app.config["UPLOAD_EXTENSION"]:
            return "Invalid file", 400
        uploaded_file.save(os.path.join(app.config["UPLOAD_POINTAGES_PATH"], filename))
        print(f"Uploaded file: {filename}")
    return "", 204


@app.route("/", methods=["POST"])
def upload_invoice():
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename != "":
        file_ext = os.path.splitext(filename)[1]
        if file_ext != app.config["UPLOAD_EXTENSION"]:
            return "Invalid file", 400
        uploaded_file.save(os.path.join(app.config["UPLOAD_INVOICE_PATH"], filename))
        print(f"Uploaded file: {filename}")
    return "", 204


@app.route("/uploads/<filename>")
def upload(filename):
    return send_from_directory(app.config["UPLOAD_INVOICE_PATH"], filename)


@app.route("/process")
def process():
    # Placeholder for processing logic
    files = glob.glob(app.config["UPLOAD_PATH"] + "/*" + app.config["UPLOAD_EXTENSION"])
    if not files:
        abort(400, description="No files uploaded")

    # # Process files
    # atc_processing(files, OUTPUT_PATH)

    # download_status["started"] = True

    # @after_this_request
    # def remove_file(response):
    #     clear_dir(app.config['UPLOAD_PATH'])
    #     os.remove(OUTPUT_PATH)
    #     return response

    return send_from_directory("./output", "output.xlsm", as_attachment=True)


@app.route("/download/status")
def download_status_check():
    return jsonify(download_status)


if __name__ == "__main__":
    app.run(debug=True)
