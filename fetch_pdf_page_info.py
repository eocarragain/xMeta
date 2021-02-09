import scenario
import argparse
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
import re
from unidecode import unidecode
import datetime


base_url = "http://research.ucc.ie/scenario"
year_range = range(2007, 2021)

issue_urls = []
for year in year_range:
    issue_urls.append("{0}/{1}/01".format(base_url, year))
    issue_urls.append("{0}/{1}/02".format(base_url, year))

next_issue = "http://research.ucc.ie/scenario/2020/02"
if next_issue in issue_urls:
    issue_urls.remove(next_issue)

#issue_urls = ["http://research.ucc.ie/scenario/2013/02"]


if __name__ == '__main__':

    wb = Workbook()

    articles_ws = wb.active
    articles_ws.title = "Articles"
    art_header = [
        'issue_id', 
        'art_id',
        'page_label_from_whole_pdf',
        'page_label_from_article_pdf',
        'page_label_from_issue_toc',
        'page_label_from_article_meta',
        'page_seq_from_whole_pdf',
        'page_seq_from_article_pdf'
    ]

    articles_ws.append(art_header)

    for url in issue_urls:
        url_parts = url.split('/')
        year = url_parts[-2]
        issue_no = url_parts[-1]
        issue_id = "{}_{}".format(year, issue_no)

        issue = scenario.parseScenarioIssue(url)
        issue_end_page_info = issue.get_end_page_info_from_pdf()
        print(issue_end_page_info)


        article_urls = issue.get_article_urls_all_languages()
        for article_url in article_urls:
            if "http" not in article_url:
                article_url = "{0}/{1}".format(url.rsplit("/", 1)[0], article_url)
            url_parts = article_url.split("/")
            art_number = url_parts[-2]
            language = url_parts[-1]
            art = scenario.parseScenario(article_url)

            art_id = "{}-{}-{}-{}".format(art_number, year, issue_no, language)
            if art_id in issue_end_page_info:
                page_label_from_whole_pdf = issue_end_page_info[art_id]["end_page_label"]
                page_seq_from_whole_pdf = issue_end_page_info[art_id]["end_page_seq"]
            else:
                print("WARNING: Failed to find {} in issue page info".format(art_id))
                page_label_from_whole_pdf = ""
                page_seq_from_whole_pdf= ""

            status_code = art.get_status_code()
            if status_code != 200:
                raise("Warning: failed to fetch {}".format(article_url)) 
                # print("Warning: failed to fetch {}".format(article_url))

            article_end_page_info = art.get_end_page_info_from_pdf()
            if art_id in issue_end_page_info:
                page_label_from_article_pdf = issue_end_page_info[art_id]["end_page_label"]
                page_seq_from_article_pdf = issue_end_page_info[art_id]["end_page_seq"]
            else:
                print("WARNING: Failed to find {} in article page info".format(art_id))
                page_label_from_article_pdf = ""
                page_seq_from_article_pdf = ""

            art_values = [
                issue_id,
                art_id,
                page_label_from_whole_pdf,
                page_label_from_article_pdf,
                art.get_end_page(),
                art.get_end_page_from_meta(),
                page_seq_from_whole_pdf,
                page_seq_from_article_pdf
            ]

            articles_ws.append(art_values)

    wb.save("scenario_end_pages.xlsx".format(year, issue_no))
        
    