import scenario
from openpyxl import Workbook
from openpyxl import load_workbook
from urllib.parse import urlparse

out_wb = Workbook()
out_ws = out_wb.active
out_ws.title = "links"
header = ['page_url', 'url', 'host', 'ext', 'link_type', 'text']
out_ws.append(header)



wb = load_workbook("scenario_tocs.xlsx")
ws =  wb.get_sheet_by_name("TOC")
for row in ws.iter_rows():
    url = row[1].value 
    if url == "article_url":
        continue

    art = scenario.parseScenario(url)
    links = art.get_html_links()
    for link_dict in links:
        link = links[link_dict]
        url = link["url"]
        host = urlparse(url).netloc
        url_end = url.split("/")[-1]
        if "." in url_end:
            ext = url_end.split(".")[-1]
        else:
            ext = ""
        out_ws.append([link["page_url"], url, host, ext, link["link_type"], link["text"] ])

    
out_wb.save("scenario_links.xlsx")
