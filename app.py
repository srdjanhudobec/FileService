from flask import Flask, render_template, send_file, request,jsonify,abort
from PyPDF2 import PdfMerger
from flask_weasyprint import HTML, render_pdf
from io import BytesIO
import time
import json
import os
import fitz
app = Flask(__name__)

def load_silabusi():
    with open('silabusi.json', 'r', encoding='utf-8') as file:
        return json.load(file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pdf')
def pdf():
    silabus = load_silabusi()
    html = render_template('pdf_template.html', silabus=silabus[3])
    base_url = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')

    pdf = HTML(string=html, base_url=base_url).write_pdf()

    pdf_io = BytesIO(pdf)

    return send_file(pdf_io, as_attachment=False, download_name="silabus.pdf", mimetype='application/pdf')


@app.route('/pdfs')
def pdfs():
    silabus = load_silabusi()
    pdf_merger = PdfMerger()
    base_url = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')


    html_start_page = render_template('start_page.html', time=time)
    pdf_start_page = HTML(string=html_start_page, base_url=base_url).write_pdf()
    pdf_merger.append(BytesIO(pdf_start_page))

    pdf_buffers = []
    for item in silabus:
        html = render_template('pdf_template.html', silabus=item)
        pdf_data = HTML(string=html, base_url=base_url).write_pdf()
        pdf_buffers.append(BytesIO(pdf_data))

    final_pdf = BytesIO()
    doc = fitz.open()

    first_pdf = fitz.open(stream=pdf_start_page, filetype="pdf")
    doc.insert_pdf(first_pdf)

    page_number = 1
    for pdf_buffer in pdf_buffers:
        pdf_buffer.seek(0)
        pdf_doc = fitz.open(stream=pdf_buffer.read(), filetype="pdf")

        for i, page in enumerate(pdf_doc):
            text = f"{page_number}"
            page.insert_text((page.rect.width - 50, page.rect.height - 30), text, fontsize=12, color=(0, 0, 0))
            page_number += 1
        
        doc.insert_pdf(pdf_doc)

    doc.save(final_pdf)
    final_pdf.seek(0)

    return send_file(final_pdf, as_attachment=False, download_name="silabus_combined.pdf", mimetype='application/pdf')

def load_rasporedi():
    with open('rasporedi.json', 'r', encoding='utf-8') as f:
        return json.load(f)
    
smerovi = {
    "softversko_inzenjerstvo" : "Softversko i informaciono inzenjerstvo",
    "informacione_tehnologije": "Informacione tehnologije"
}
    
@app.route('/pdfsmera')
def pdfsmera():
    smer = request.args.get('smer')
    
    if smer is None or smer not in load_rasporedi():
        return "Studijski smer nije validan!", 400
    
    rasporedi = load_rasporedi()[smer]
    
    html = render_template('raspored_template.html', raspored=rasporedi, smer=smerovi[smer])
    
    pdf = HTML(string=html).write_pdf()
    
    return send_file(BytesIO(pdf), download_name=f"raspored_{smer}.pdf", as_attachment=True)

def izracunaj_bodove(student):
    k1 = student.get("k1")
    k2 = student.get("k2")
    ispit = student.get("ispit")
    
    if k1 == "" or k2 == "" or ispit == "":
        student["ukupno"] = ""
        student["ocena"] = ""
        return student

    ukupno = k1 + k2 + ispit
    student["ukupno"] = ukupno

    if ukupno >= 91:
        student["ocena"] = 10
    elif ukupno >= 81:
        student["ocena"] = 9
    elif ukupno >= 71:
        student["ocena"] = 8
    elif ukupno >= 61:
        student["ocena"] = 7
    elif ukupno >= 51:
        student["ocena"] = 6
    else:
        student["ocena"] = "Nije položio"

    return student

def load_studenti():
    with open('studenti_smer.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route("/studenti", methods=["GET"])
def studenti():
    smer = request.args.get("smer", "Softversko inženjerstvo")

    studenti_podaci = load_studenti()
    
    if smer not in studenti_podaci:
        return jsonify({"error": "Smer ne postoji"}), 404

    studenti = [izracunaj_bodove(student) for student in studenti_podaci[smer]]
    html =  render_template("studenti.html", smer=smer, studenti=studenti)
    
    pdf = HTML(string=html).write_pdf()
    
    return send_file(BytesIO(pdf), download_name=f"studenti_{smer}.pdf", as_attachment=True)

def load_potvrda():
    with open('potvrda_studenti.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/potvrda/<broj_indeksa>')
def potvrda(broj_indeksa):
    studenti = load_potvrda()

    student = next((s for s in studenti if s['broj_indeksa'] == broj_indeksa), None)
    
    if not student:
        abort(404, description="Student nije pronađen")

    html = render_template('potvrda_o_redovnom_studiranju.html', student=student)
    pdf = HTML(string=html).write_pdf()
    
    return send_file(BytesIO(pdf), download_name=f"potvrda_{broj_indeksa}.pdf", as_attachment=True)

def load_studenti_fakultet():
    with open('studenti.json', 'r', encoding='utf-8') as f:
        return json.load(f)
    
def load_nastavnici():
    with open('nastavnici.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/export', methods=['POST'])
def export():
    data = request.get_json()
    univerzitet = data.get('univerzitet')
    fakultet = data.get('fakultet')

    studenti = load_studenti_fakultet()
    nastavnici = load_nastavnici()

    filtrirani_studenti = [s for s in studenti if s['univerzitet'] == univerzitet and s['fakultet'] == fakultet]
    filtrirani_nastavnici = [p for p in nastavnici if p['univerzitet'] == univerzitet and p['fakultet'] == fakultet]

    html =  render_template('export_template.html', studenti=filtrirani_studenti, nastavnici=filtrirani_nastavnici, univerzitet=univerzitet, fakultet=fakultet)
    pdf = HTML(string=html).write_pdf()
    
    return send_file(BytesIO(pdf), download_name=f"export.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
