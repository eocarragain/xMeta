import sys
import PyPDF2 as pyPdf
import re

"""Open your pdf"""
pdf = pyPdf.PdfFileReader(open(sys.argv[1], "rb"))

"""Explore the /PageLabels (if it exists)"""
#page = pdf.getPage(21)
#print(type(page))
#print(page.extractText())
#print(pdf.trailer["/Root"]["/Pages"]["/Kids"][0].getObject())
#print(pdf.trailer["/Root"]["/Outlines"]["/First"]["/Next"])

p = 1
end_pages = {}
for page in pdf.pages:
    #print(page.extractText()[:100])
    lines = page.extractText()[-200:].splitlines()
    #print(lines)
    l = 0
    for line in lines:
        #print (page.extractText()[-200:])
        pattern = re.compile("\d{2}-\D+-\d{4}-\d{2}-(en|de)", re.IGNORECASE)
        if pattern.match(line):
            page_print = lines[l-1].strip()
            print(p)
            print(page_print)
            print(line)
            if page_print.isnumeric():
                if p - int(page_print) != 5:
                    print("@@@@@@@@@@@@@@@ warning ")
            id = line.lower().strip()
            end_pages[id] = {
                "id" : id,
                "page_count": p,
                "page_print": page_print
            }
        l += 1
    p += 1

print(end_pages)

try:
    page_label_type = pdf.trailer["/Root"]["/PageLabels"]
    print(page_label_type)
except:
    print("No /PageLabel object")

"""Select the item that is most likely to contain the information you desire; e.g.
       {'/Nums': [0, IndirectObject(42, 0)]}
   here, we only have "/Num". """

try:
    page_label_type = pdf.trailer["/Root"]["/PageLabels"]["/Nums"]
    print(page_label_type)
except:
    print("No /PageLabel object")

"""If you see a list, like
       [0, IndirectObject(42, 0)]
   get the correct item from it"""

try:
    page_label_type = pdf.trailer["/Root"]["/PageLabels"]["/Nums"][1]
    print(page_label_type)
except:
    print("No /PageLabel object")

"""If you then have an indirect object, like
       IndirectObject(42, 0)
   use getObject()"""

try:
    page_label_type = pdf.trailer["/Root"]["/PageLabels"]["/Nums"][1].getObject()
    print(page_label_type)
except:
    print("No /PageLabel object")

"""Now we have e.g.
       {'/S': '/r', '/St': 21}
   meaning roman numerals, starting with page 21, i.e. xxi. We can now also obtain the two variables directly."""

try:
    page_label_type = pdf.trailer["/Root"]["/PageLabels"]["/Nums"][1].getObject()["/S"]
    print(page_label_type)
    start_page = pdf.trailer["/Root"]["/PageLabels"]["/Nums"][1].getObject()["/St"]
    print(start_page)
except:
    print("No /PageLabel object")