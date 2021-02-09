from PyPDF2 import PdfFileWriter, PdfFileReader
import io
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor

def get_doi_canvas(doi, width, height):
    packet = io.BytesIO()

    canvas = reportlab.pdfgen.canvas.Canvas(packet, pagesize=(width,height))

    footer_text = doi
    canvas.saveState()
    canvas.setFont("Helvetica-Bold",8)
    canvas.setFillColor(HexColor('#990100'))
    canvas.drawCentredString(int(width)/2, 20, footer_text)
    canvas.restoreState()

    canvas.save()
    packet.seek(0)
    new_pdf = PdfFileReader(packet)
    return new_pdf


# create a new PDF with Reportlab


#move to the beginning of the StringIO buffer

# read your existing PDF
existing_pdf = PdfFileReader(open("make.pdf", "rb"))# 07-wortspiel-2011-01-de.pdf

output = PdfFileWriter()
num_of_pages = existing_pdf.getNumPages()
for i in range(num_of_pages):
    page = existing_pdf.getPage(i)
    print(i)
    if i == 0:
        mediabox = page.mediaBox
        print(mediabox[2])
        new_pdf = get_doi_canvas("https://doi.org/10.233434/doi", mediabox[2],mediabox[3])
        page.mergePage(new_pdf.getPage(0))
    output.addPage(page)
# finally, write "output" to a real file
outputStream = open("destination.pdf", "wb")
output.write(outputStream)
outputStream.close()