import glob
import os

import pandas as pd
from flask import (
    Flask,
    abort,
    after_this_request,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)
from werkzeug.utils import secure_filename

from constants import (
    OUTPUT_PATH,
    UPLOAD_INVOICE_PATH,
    UPLOAD_PATHS,
    UPLOAD_POINTAGES_PATH,
)
from data_processors.integrator import web_main
from utils import clear_dir

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB limit
app.config["UPLOAD_EXTENSION"] = [".xlsm", ".xlsx", ".csv", ".CSV"]
app.config["UPLOAD_POINTAGES_PATH"] = UPLOAD_POINTAGES_PATH
app.config["UPLOAD_INVOICE_PATH"] = UPLOAD_INVOICE_PATH
app.config["UPLOAD_PATHS"] = UPLOAD_PATHS


# Simple in-memory status store
download_status = {}


@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413


@app.route("/")
def index():
    # Clear previous uploads and outputs on loading the main page
    for path in app.config["UPLOAD_PATHS"]:
        clear_dir(path)
        # print(f"Cleared directory: {path}")
    clear_dir("./output")
    download_status["started"] = False

    # files = os.listdir(app.config['UPLOAD_PATHS'])
    print(glob.glob("./*"))
    return render_template("index.html", files=[])


# @app.route('/', methods=['POST'])
# def upload_files():
#     uploaded_file = request.files['file']
#     filename = secure_filename(uploaded_file.filename)
#     if filename != '':
#         file_ext = os.path.splitext(filename)[1]
#         if file_ext not in app.config['UPLOAD_EXTENSION']:
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
        if file_ext not in app.config["UPLOAD_EXTENSION"]:
            return "Invalid file", 400
        # TODO: determine the upload path based on the upload button used
        upload_path = (
            app.config["UPLOAD_POINTAGES_PATH"]
            if ".csv" in filename.lower()
            else app.config["UPLOAD_INVOICE_PATH"]
        )
        uploaded_file.save(os.path.join(upload_path, filename))
        print(f"Uploaded file: {filename}")
    return "", 204


@app.route("/", methods=["POST"])
def upload_invoice():
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename != "" and (".xlsm" in filename.lower() or ".xlsx" in filename.lower()):
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config["UPLOAD_EXTENSION"]:
            return "Invalid file", 400
        # TODO: determine the upload path based on the upload button used
        upload_path = (
            app.config["UPLOAD_POINTAGES_PATH"]
            if ".csv" in filename.lower()
            else app.config["UPLOAD_INVOICE_PATH"]
        )
        uploaded_file.save(os.path.join(upload_path, filename))
        print(f"Uploaded file: {filename}")
    return "", 204


@app.route("/upload/<filename>")
def upload_file(filename):
    return send_from_directory(app.config["UPLOAD_PATH"][0], filename)


# @app.route("/upload_pointages/<filename>")
# def upload_pointages(filename):
#     return send_from_directory(app.config["UPLOAD_POINTAGES_PATH"], filename)


# @app.route("/upload_invoices/<filename>")
# def upload_invoices(filename):
#     return send_from_directory(app.config["UPLOAD_INVOICE_PATH"], filename)


@app.route("/process")
def process():
    # Placeholder for processing logic
    files = []
    for path in app.config["UPLOAD_PATHS"]:
        files.extend(
            [
                f
                for f in glob.glob(path + "/*")
                if any(f.endswith(ext) for ext in app.config["UPLOAD_EXTENSION"])
            ]
        )
    if not files:
        abort(400, description="No files uploaded")

    # Process files
    output_dfs = web_main(
        pointages_paths=[f for f in files if f.endswith(".csv") or f.endswith(".CSV")],
        invoice_path=[f for f in files if f.endswith(".xlsm") or f.endswith(".xlsx")][
            0
        ],
    )

    # Save output
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        output_dfs[0].to_excel(
            writer, sheet_name="Normal Hours Difference", index=False
        )
        output_dfs[1].to_excel(writer, sheet_name="Extra Hours Difference", index=False)
        output_dfs[2].to_excel(
            writer,
            sheet_name="Plus de Nocturnidad Unitario Hours Difference",
            index=False,
        )
        output_dfs[3].to_excel(writer, sheet_name="Missing Information", index=False)
        output_dfs[4].to_excel(
            writer, sheet_name="Total Hours Invoice Normal", index=True
        )
        output_dfs[5].to_excel(
            writer, sheet_name="Total Hours Pointages Normal", index=True
        )
        output_dfs[6].to_excel(
            writer, sheet_name="Total Hours Invoice Extra", index=True
        )
        output_dfs[7].to_excel(
            writer, sheet_name="Total Hours Pointages Extra", index=True
        )
        output_dfs[8].to_excel(
            writer,
            sheet_name="Total Hours Invoice Plus de Nocturnidad Unitario",
            index=True,
        )
        output_dfs[9].to_excel(
            writer,
            sheet_name="Total Hours Pointages Plus de Nocturnidad Unitario",
            index=True,
        )

    download_status["started"] = True

    @after_this_request
    def remove_file(response):
        if not download_status.get("started"):
            return response

        for path in app.config["UPLOAD_PATHS"]:
            clear_dir(path)
        os.remove(OUTPUT_PATH)
        return response

    return send_file(OUTPUT_PATH, as_attachment=True)


@app.route("/download/status")
def download_status_check():
    return jsonify(download_status)


if __name__ == "__main__":
    app.run(debug=True)
