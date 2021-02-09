import scenario
import argparse
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
import re
from unidecode import unidecode
import datetime

article_urls = [
    "http://research.ucc.ie/journals/chimera/2013/00/kukuliac/03/en",
    "http://research.ucc.ie/journals/chimera/2013/00/glynn/02/en",
    "http://research.ucc.ie/journals/chimera/2013/00/mccroy/04/en",
    "http://research.ucc.ie/journals/chimera/2013/00/osullivan/05/en",
    "http://research.ucc.ie/journals/chimera/2013/00/sheridanquantz/06/en",
    "http://research.ucc.ie/journals/chimera/2013/00/williams/07/en",
    "http://research.ucc.ie/journals/chimera/2013/00/scriven/08/en",
    "http://research.ucc.ie/journals/chimera/2013/00/kandrot/09/en",
    "http://research.ucc.ie/journals/chimera/2013/00/lennon/11/en"
]

#issue_urls = ["http://research.ucc.ie/ijpp/2009/01"]


#issue_urls = ["http://research.ucc.ie/boolean/2010/00"]


if __name__ == '__main__':



    #issue = scenario.parseIjppIssue(url)
    #issue_end_page_info = issue.get_end_page_info_from_pdf()
    #print(issue_end_page_info)

    for article_url in article_urls:
        url_parts = article_url.split('/')
        year = url_parts[-5]
        issue_no = url_parts[-4]
        issue_id = "{}_{}".format(year, issue_no)
        art_number = url_parts[-2]
        language = url_parts[-1]
        art = scenario.parseChimera(article_url)
        print(art.doi)
        filename = art.get_fallback_url('pdf').split("/")[-1]
        #filepath = "ijpp_pdfs/{}-{}/{}".format(year, issue_no, filename)
        filepath = "chimera_pdfs/{}".format(filename)
        with open(filepath, 'wb') as f:
            f.write(art.get_pdf())

