import PyPDF2 as pyPdf
import io
import re
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from pdfrw import PdfReader
from pdfrw.toreportlab import makerl
from pdfrw.buildxobj import pagexobj

def pdf_insert_doi(req_content, doi):
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


def get_pdf_reader(req_content):
    pdf_file = io.BytesIO(req_content)
    pdf_reader = pyPdf.PdfFileReader(pdf_file)
    return pdf_reader

def get_pdf_page_count(req_content):
    pdf_reader = get_pdf_reader(req_content)
    return int(pdf_reader.numPages)

def get_end_page_info_from_pdf(req_content):
    pdf_reader = get_pdf_reader(req_content)
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
                    "end_page_label": page_label
                }
            l += 1
        p += 1

    return (end_pages)

