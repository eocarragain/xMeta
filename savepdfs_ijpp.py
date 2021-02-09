import scenario
import argparse
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
import re
from unidecode import unidecode
import datetime

issue_urls = [
    "http://research.ucc.ie/ijpp/2009/01",
    "http://research.ucc.ie/ijpp/2010/01",
    "http://research.ucc.ie/ijpp/2011/01",
    "http://research.ucc.ie/ijpp/2011/02",
    "http://research.ucc.ie/ijpp/2012/01"
]

#issue_urls = ["http://research.ucc.ie/ijpp/2009/01"]


#issue_urls = ["http://research.ucc.ie/boolean/2010/00"]


if __name__ == '__main__':

    for url in issue_urls:
        url_parts = url.split('/')
        year = url_parts[-2]
        issue_no = url_parts[-1]
        issue_id = "{}_{}".format(year, issue_no)

        issue = scenario.parseIjppIssue(url)
        #issue_end_page_info = issue.get_end_page_info_from_pdf()
        #print(issue_end_page_info)


        article_urls = issue.get_article_urls_all_languages()
        for article_url in article_urls:
            if "http" not in article_url:
                article_url = "{0}/{1}".format(url.rsplit("/", 1)[0], article_url)
            url_parts = article_url.split("/")
            art_number = url_parts[-2]
            language = url_parts[-1]
            art = scenario.parseIjpp(article_url)
            print(art.doi)
            filename = art.get_fallback_url('pdf').split("/")[-1]
            #filepath = "ijpp_pdfs/{}-{}/{}".format(year, issue_no, filename)
            filepath = "ijpp_pdfs/{}/{}".format(year, filename)
            with open(filepath, 'wb') as f:
                f.write(art.get_pdf())

