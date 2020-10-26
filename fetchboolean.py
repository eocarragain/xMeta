import scenario
import argparse
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
import re
from unidecode import unidecode
import datetime

class fetchUtils():
    def __init__(self):
        self.contrib_db = "contribs_boolean.xlsx"
        xl = pd.ExcelFile(self.contrib_db)
        self.contrib_df = xl.parse('Contributors')
        self.contrib_df['lookup'] = self.contrib_df.apply(lambda x: self.get_name_lookup(x['given_name'], x['surname']), axis=1)
        self.contrib_wb = load_workbook(self.contrib_db)
        self.contrib_ws =  self.contrib_wb.get_sheet_by_name("Contributors")

    def get_name_lookup(self, given_name, family_name):
        str = "{}{}".format(given_name, family_name).lower().replace(" ", "")
        str = re.sub(r'[^\w\s]', '', str)
        str = unidecode(str).strip()
        return str

    def get_contibs(self, contribs, affiliation = "University College Cork, Ireland."):
        contrib_keys = []


        if len(contribs) == 0:
            return ""

        for contrib in contribs:
            if contrib in ["Foreword", "Vorwort"]:
                contrib = "Manfred Schewe"
            contrib = " ".join(contrib.split()).strip()
            name_parts = contrib.split(" ", 1)
            if len(name_parts) < 2:
                continue
            else:
                if len(name_parts[0].strip()) == 0:
                    print(";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;")
                given_name = name_parts[0]
                family_name = name_parts[1]
            lookup = self.get_name_lookup(given_name, family_name)
            matches_df = self.contrib_df[self.contrib_df['lookup'].eq(lookup)]
            if len(matches_df) > 0: 
                contrib_keys.append(matches_df.iloc[0]['id'])
            else:
                df_row = {
                    'id': lookup,
                    'given_name': given_name,
                    'surname': family_name,
                    'orcid': '',
                    'primary_affiliation': affiliation,
                    'secondary_affiliation': '',
                    'email_for_ucc_authors': '',
                    'lookup': lookup
                } 
                self.contrib_df = self.contrib_df.append(df_row, ignore_index=True)
                self.contrib_ws.append([lookup, given_name,family_name, '', affiliation, '', ''])
                contrib_keys.append(lookup)

        contribs = '||'.join(contrib_keys)
        return contribs

    def save_wb(self):
        self.contrib_wb.save(self.contrib_db)

    def get_full_date(self, date, issue_no=''):
        if len(date) == 4:
            if issue_no == '01':
                mnt = '01'
            elif issue_no == '02':
                mnt = '07'
            else:
                mnt = '01'
            #return "{}-{}-01".format(date, mnt)
            return datetime.datetime(int(date), int(mnt), 1).date()
        elif len(date) == 7:
            #return "{}-{}-01".format(date[0:4], date[5:7])
            return datetime.datetime(int(date[0:4]), int(date[5:7]), 1).date()
        else:
            return date


issue_urls = [
    "http://research.ucc.ie/boolean/2010/00",
    "http://research.ucc.ie/boolean/2011/00",
    "http://research.ucc.ie/boolean/2012/00",
    "http://research.ucc.ie/boolean/2014/00",
    "http://research.ucc.ie/boolean/2015/00",
]

#issue_urls = ["http://research.ucc.ie/boolean/2010/00"]


if __name__ == '__main__':
    utils = fetchUtils()
    base_doi = '10.33178/boolean'
    for url in issue_urls:
        url_parts = url.split('/')
        year = url_parts[-2]

        issue = scenario.parseBooleanIssue(url)

        wb = Workbook()

        # grab the active worksheet
        journal_ws = wb.active
        journal_ws.title = "Journal"
        journal_header = ['doi', 'journal_title', 'short_title', 'journal_issn', 'journal_url', 'reference_distribution_opts', 'publisher', 'license_url']
        journal_values = [base_doi, 'The Boolean: Snapshots of Doctoral Research at University College Cork','The Boolean', '', 'https://research.ucc.ie/boolean/home', 'any', 'University College Cork', '']
        journal_ws.append(journal_header)
        journal_ws.append(journal_values)
 
        volume_ws = wb.create_sheet("Volume")
        volume_header = ['doi', 'volume_number', 'volume_url']
        volume_values = ['', '', '']
        volume_ws.append(volume_header)
        volume_ws.append(volume_values)

        issue_ws = wb.create_sheet("Issue")
        issue_header = ['doi', 'issue_title', 'editors', 'publication_date', 'issue_number', 'issue_url', 'collection', 'rights_statement','languages'] 
        issue_doi = "{0}.{1}".format(base_doi, year)
        issue_values = [
            issue_doi,
            '',
            utils.get_contibs(issue.get_editors()),
            utils.get_full_date(issue.get_year()),
            year,
            url,
            '',
            'en'
        ]
        issue_ws.append(issue_header)
        issue_ws.append(issue_values)
        issue_ws['D1'].number_format = 'yyyy-mm-dd'

        articles_ws = wb.create_sheet("Articles")
        art_header = ['doi','language','title','subtitle','authors','editors','publication_date','url','abstract','abstract_translated_to_en','first_page','last_page','keywords','keywords_de','type','peer_reviewed','Recommended citation for item', "mint_doi"]
        articles_ws.append(art_header)
        
        citations_ws = wb.create_sheet("Citations")
        citations_header = ["Article DOI ","Complete reference","DOI for reference"]
        citations_ws.append(citations_header)

        article_urls = issue.get_unique_article_urls()
        for article_url in article_urls:
            if "http" not in article_url:
                article_url = "{0}/{1}".format(url.rsplit("/", 1)[0], article_url)
            url_parts = article_url.split("/")
            art_id = str(int(url_parts[-2]))
            art_doi = "{0}.{1}".format(issue_doi, art_id)
            language = url_parts[-1]
            art = scenario.parseBoolean(article_url)
            title = art.title
            status_code = art.get_status_code()

            #Get affiliation. Only one per article
            affil = "University College Cork, Ireland."
            arts_from_toc = issue.get_articles_from_toc()
            if article_url.lower() in arts_from_toc:
                art_from_toc = arts_from_toc[article_url.lower()]
                affil_from_toc =  art_from_toc["affiliation"]
                if len(affil_from_toc.strip()) > 10:
                    affil = "{0}, {1}".format(affil_from_toc, affil)
                
            #print(affil)
            
            if status_code != 200:
                #raise Exception("Warning: failed to fetch {}".format(article_url)) 
                print("Warning: failed to fetch {}".format(article_url))
                cite = ''
            else:
                cite = art.get_cite()

            #toc_section = art.get_section()
            #section_ref = issue.get_section_ref(toc_section, title)
            #non_ojs_meta = issue.get_section_meta_for_non_ojs(section_ref)
            
            authors = art.get_authors()
            author_keys = utils.get_contibs(authors, affil)
            if len(author_keys.strip()) == 0:
                print("@@@@@ {}".format(authors))
                raise Exception("No authors found when fetching {}".format(art_doi))
            art_values = [
                art_doi,
                language,
                title,
                '',
                author_keys, #todo
                utils.get_contibs(issue.get_editors()), #todo
                '',#utils.get_full_date(art.get_meta_tag("citation_publication_date")),
                article_url,
                art.get_abstract(),
                '',
                art.get_start_page(),
                art.get_end_page(),# art.get_meta_tag("citation_lastpage"),
                '',# keywords
                '',# keywords_de
                'Article',# type
                'Non peer-reviewed',# peer_reviewed
                cite, # recommended citation
                'True' # skip doi
            ]
            
            citations = art.get_citations()
            for citation in citations:
                citations_ws.append([art_doi, citation, ''])

            articles_ws.append(art_values)

        contributors_ws = wb.create_sheet("Contributors")
        contributors_header = ['id', 'given_name', 'surname', 'orcid', 'primary_affiliation', 'secondary_affiliation', 'email_for_ucc_authors']
        contributors_ws.append(contributors_header)
        for r in dataframe_to_rows(utils.contrib_df, index=False, header=False):
            contributors_ws.append(r)

        wb.save("boolean_{}.xlsx".format(year))
        utils.save_wb()
        
    