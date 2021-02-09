from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from pdfrw import PdfReader
from pdfrw.toreportlab import makerl
from pdfrw.buildxobj import pagexobj
import io
import base64

input_file = "05-fischaess-2008-01-de.pdf"
pdf_buffer = io.BytesIO() #"05-fischaess-2008-01-de_out.pdf"

    

# Get pages
reader = PdfReader(input_file)
pages = [pagexobj(p) for p in reader.pages]


# Compose new pdf
canvas = Canvas(pdf_buffer)
doi = "https://doi.org/10.1223/scenario.12.2"
for page_num, page in enumerate(pages, start=1):
    

    # Add page
    canvas.setPageSize((page.BBox[2], page.BBox[3]))
    canvas.doForm(makerl(canvas, page))

    # Draw footer
    if page_num == 1:
        footer_text = doi
        canvas.saveState()
        canvas.setFont("Helvetica-Bold",8)
        canvas.setFillColor(HexColor('#990100'))
        canvas.drawCentredString(page.BBox[2]/2, 20, footer_text)
        canvas.restoreState()

    canvas.showPage()

canvas.save()
#pdf_value = pdf_buffer.getvalue()
#pdf_buffer.close()
print(type(pdf_buffer.read()))
print(type(pdf_buffer.getbuffer()))

print(base64.b64encode(pdf_buffer.getbuffer()).decode('utf-8'))

with open("06-HeinKhatib-2016-01-de_io.pdf", "wb") as f:
    f.write(pdf_buffer.getbuffer())