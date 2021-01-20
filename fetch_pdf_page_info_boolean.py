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

    wb = Workbook()

    articles_ws = wb.active
    articles_ws.title = "Articles"
    art_header = [
        'issue_id', 
        'art_id',
        'page_label_from_article_pdf',
        'page_label_from_article_meta',
        'page_count_from_article_pdf',
        'page_seq_from_article_pdf'
    ]

    articles_ws.append(art_header)

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

            art_id = "{}-{}-{}-{}".format(art_number, year, issue_no, language)
 
            status_code = art.get_status_code()
            if status_code != 200:
                #raise("Warning: failed to fetch {}".format(article_url)) 
                print("Warning: failed to fetch {}".format(article_url))

            article_end_page_info = art.get_end_page_info_from_pdf()
            if art_id in article_end_page_info:
                page_label_from_article_pdf = article_end_page_info[art_id]["end_page_label"]
                page_seq_from_article_pdf = article_end_page_info[art_id]["end_page_seq"]
                page_count_from_article_pdf = article_end_page_info[art_id]["page_count"]
            else:
                print("WARNING: Failed to find {} in article page info".format(art_id))
                page_label_from_article_pdf = ""
                page_seq_from_article_pdf = ""
                page_count_from_article_pdf = ""

            art_values = [
                issue_id,
                art_id,
                page_label_from_article_pdf,
                art.get_end_page(),
                page_count_from_article_pdf,
                page_seq_from_article_pdf
            ]

            articles_ws.append(art_values)

    wb.save("boolean_end_pages.xlsx".format(year, issue_no))
        
    