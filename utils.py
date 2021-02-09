
import io
import re
#reportlab
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
# pdfrw
from pdfrw import PdfReader
from pdfrw.toreportlab import makerl
from pdfrw.buildxobj import pagexobj
# PyPDF2
import PyPDF2 as pyPdf
from PyPDF2 import PdfFileWriter, PdfFileReader

def pdf_insert_doi_using_pdfrw(req_content, doi):
    input_file = io.BytesIO(req_content)
    pdf_buffer = io.BytesIO()
    reader = PdfReader(input_file)
    pages = [pagexobj(p) for p in reader.pages]

    canvas = Canvas(pdf_buffer)

    for page_num, page in enumerate(pages, start=1):
        canvas.setPageSize((page.BBox[2], page.BBox[3]))
        canvas.doForm(makerl(canvas, page))

        # Draw footer
        if page_num == 1:
            footer_text = "https://doi.org/{}".format(doi)
            canvas.saveState()
            canvas.setFont("Helvetica-Bold",8)
            canvas.setFillColor(HexColor('#990100'))
            canvas.drawCentredString(page.BBox[2]/2, 20, footer_text)
            canvas.restoreState()

        canvas.showPage()

    canvas.save()
    pdf_bytes = pdf_buffer.getbuffer()
    return pdf_bytes

def get_doi_canvas(doi, width, height, license_url):
    packet = io.BytesIO()

    canvas = Canvas(packet, pagesize=(width,height))

    footer_text = "https://doi.org/{}".format(doi)
    canvas.saveState()
    #canvas.setFont("Helvetica-Bold",8)
    canvas.setFont("Times-Roman",8)
    #canvas.setFillColor(HexColor('#990100'))
    canvas.drawCentredString(int(width)/2, 20, footer_text)
    if len(license_url.strip()) > 0:
        canvas.drawCentredString(int(width)/2, 10, license_url)
    canvas.restoreState()
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    new_pdf = PdfFileReader(packet)
    return new_pdf

def pdf_insert_doi(req_content, doi, license_url):
    input_file = io.BytesIO(req_content)
    existing_pdf = PdfFileReader(input_file)

    output = PdfFileWriter()
    num_of_pages = existing_pdf.getNumPages()
    for i in range(num_of_pages):
        page = existing_pdf.getPage(i)
        if i == 0:
            mediabox = page.mediaBox
            doi_canvas = get_doi_canvas(doi, mediabox[2],mediabox[3], license_url)
            page.mergePage(doi_canvas.getPage(0))
        output.addPage(page)

    pdf_buffer = io.BytesIO()
    output.write(pdf_buffer)
    pdf_bytes = pdf_buffer.getbuffer()
    return pdf_bytes


def get_pdf_reader(req_content):
    pdf_file = io.BytesIO(req_content)
    pdf_reader = pyPdf.PdfFileReader(pdf_file)
    return pdf_reader

def get_pdf_page_count(req_content):
    pdf_reader = get_pdf_reader(req_content)
    return int(pdf_reader.numPages)

def get_end_page_info_from_pdf(req_content):
    pdf_reader = get_pdf_reader(req_content)
    page_count = pdf_reader.numPages
    p = 1
    end_pages = {}
    for page in pdf_reader.pages:
        # pull out lines for the last 200 words from page text
        lines = page.extractText()[-200:].splitlines()
        
        l = 0
        for line in lines:
            # the last page of an article has the article id in form 00-foreword-2020-01-en
            pattern = re.compile(r"\d{2}-\D+-\d{4}-\d{2}-(en|de)", re.IGNORECASE)
            if pattern.match(line):
                # page_lable is the user-facing page, e.g. 'iv', '33'
                # it should be on the line before the article id
                page_label = lines[l-1].strip()
                id = line.lower().strip()
                id_parts = id.split("-",2)
                id_key = "{}-{}".format(id_parts[0], id_parts[2])
                print(id_key)
                end_pages[id_key] = {
                    "id" : id,
                    "end_page_seq": p,
                    "end_page_label": page_label,
                    "page_count": page_count
                }
            l += 1
        p += 1

    return (end_pages)

