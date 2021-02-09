import scenario
import argparse
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
import re
from unidecode import unidecode
import datetime
import requests


base_url = "http://research.ucc.ie/scenario"
year_range = range(2007, 2021)
#year_range = range(2007, 2008)
issue_urls = []
for year in year_range:
    issue_urls.append("{0}/{1}/01".format(base_url, year))
    issue_urls.append("{0}/{1}/02".format(base_url, year))

issue_urls.remove("http://research.ucc.ie/scenario/2020/02")

retrieve_urls = True

def get_wayback_api_url(scenario_url):
    return "http://archive.org/wayback/available?url={}".format(scenario_url)


def test_urls(url):
    resp = {
        "retrievable": "",
        "in_wayback": ""
    }
    req = requests.get(url)
    if req.status_code == 200:
        resp["retrievable"] = "true"
        return resp
    else:
        resp["retrievable"] = "false"
    
    # try to fetch from wayback
    wb_urls = [
        get_wayback_api_url(url), 
        get_wayback_api_url(url.replace("research.ucc.ie", "publish.ucc.ie"))
        ]
    for wb_url in wb_urls:
        wb_api = requests.get(wb_url)
        wb_api_resp = wb_api.json()
        print(wb_api_resp)
        if wb_api_resp["archived_snapshots"] != {}:
            wb_status = wb_api_resp["archived_snapshots"]["closest"]["status"]
            if wb_status == '200':
                resp["in_wayback"] = "true"
                return resp

    

if __name__ == '__main__':
    wb = Workbook()
    ws = wb.active
    ws.title = "TOC"
    header = ['issue_url', 'article_url', 'title', 'section', 'authors', 'start_page', 'pdf_url', 'media', 'html_retrievable', 'html_in_wayback', 'pdf_retrievable', 'pdf_in_wayback']
    ws.append(header)

    for url in issue_urls:
        issue = scenario.parseScenarioIssue(url)
        tocs = issue.get_articles_from_toc()
        print(tocs)
        for key in tocs:
            toc = tocs[key]
            print(toc)
            pdf_url = "{}/{}".format(toc['url'].rsplit("/", 1)[0], toc['pdf'])
            media = "\n".join(toc['media'])
            if retrieve_urls == True:
                fetches = test_urls(toc['url'])
                pdf_fetches = test_urls(pdf_url)
            else:
                fetches = {"retrievable": "", "in_wayback": ""}
                pdf_fetches = fetches
            values = [url, toc['url'], toc['title'], toc['section'], toc['authors'], toc['start_page'], pdf_url, media, fetches['retrievable'], fetches['in_wayback'], pdf_fetches['retrievable'], pdf_fetches['in_wayback']]
            print(values)
            ws.append(values)
    
    wb.save("scenario_tocs.xlsx")
        
        
