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
    "http://research.ucc.ie/boolean/2010/00",
    "http://research.ucc.ie/boolean/2011/00",
    "http://research.ucc.ie/boolean/2012/00",
    "http://research.ucc.ie/boolean/2014/00",
    "http://research.ucc.ie/boolean/2015/00",
]


#issue_urls = ["http://research.ucc.ie/boolean/2010/00"]


if __name__ == '__main__':

    for url in issue_urls:
        url_parts = url.split('/')
        year = url_parts[-2]
        issue_no = url_parts[-1]
        issue_id = "{}_{}".format(year, issue_no)

        issue = scenario.parseBooleanIssue(url)
        #issue_end_page_info = issue.get_end_page_info_from_pdf()
        #print(issue_end_page_info)


        article_urls = issue.get_article_urls_all_languages()
        for article_url in article_urls:
            if "http" not in article_url:
                article_url = "{0}/{1}".format(url.rsplit("/", 1)[0], article_url)
            url_parts = article_url.split("/")
            art_number = url_parts[-2]
            language = url_parts[-1]
            art = scenario.parseBoolean(article_url)
            print(art.doi)
            filename = art.get_fallback_url('pdf').split("/")[-1]
            filepath = "boolean_pdfs/{}-00/{}".format(year, filename)
            with open(filepath, 'wb') as f:
                f.write(art.get_pdf())

