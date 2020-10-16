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
        self.contrib_db = "contribs.xlsx"
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

    def get_contibs(self, contribs):
        print(type(contribs))
        contrib_keys = []
        print(len(contribs))
        print(contribs)
        if len(contribs) == 0:
            return ""

        for contrib in contribs:
            if contrib in ["Foreword", "Vorwort"]:
                contrib = "Manfred Schewe"
            print(contrib)
            name_parts = contrib.split(" ", 1)
            if len(name_parts) < 2:
                continue
            else:
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
                    'primary_affiliation': '',
                    'secondary_affiliation': '',
                    'email_for_ucc_authors': '',
                    'lookup': lookup
                } 
                self.contrib_df = self.contrib_df.append(df_row, ignore_index=True)
                self.contrib_ws.append([lookup, given_name,family_name, '', '', '', ''])
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

base_url = "http://research.ucc.ie/scenario"
year_range = range(2017, 2018)
#year_range = range(2007, 2008)
issue_urls = []
for year in year_range:
    issue_urls.append("{0}/{1}/01".format(base_url, year))
    issue_urls.append("{0}/{1}/02".format(base_url, year))

next_issue = "http://research.ucc.ie/scenario/2020/02"
if next_issue in issue_urls:
    issue_urls.remove(next_issue)


if __name__ == '__main__':
    utils = fetchUtils()
    #parser = argparse.ArgumentParser(description='Fetch metadata from old scenario journal')
    #parser.add_argument('input_filename', nargs=1, help='the filename to process')
    #args = vars(parser.parse_args())
    #print(args)
    #input_file = args['input_filename'][0]
    base_doi = '10.33178/scenario'
    for url in issue_urls:
        url_parts = url.split('/')
        year = url_parts[-2]
        issue_no = url_parts[-1]
        issue_no_as_int = str(int(issue_no))

        issue = scenario.parseScenarioIssue(url)
        vol = issue.get_volume()
        vol = vol.replace("Volume ", "").strip()
        vol_as_int = issue.get_volume_as_int(vol)

        cc_statement = "© {}, The Author(s). This work is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License.".format(issue.get_year())

        wb = Workbook()

        # grab the active worksheet
        journal_ws = wb.active
        journal_ws.title = "Journal"
        journal_header = ['doi', 'journal_title', 'short_title', 'journal_issn', 'journal_url', 'reference_distribution_opts', 'publisher', 'license_url']
        journal_values = [base_doi, 'Scenario: A Journal of Performative Teaching, Learning, Research','Scenario', '1649-8526', 'https://www.ucc.ie/en/scenario/scenariojournal/', 'any', 'Department of German, University College Cork', 'https://creativecommons.org/licenses/by-nc-nd/4.0/']
        journal_ws.append(journal_header)
        journal_ws.append(journal_values)
 
        volume_ws = wb.create_sheet("Volume")
        volume_header = ['doi', 'volume_number', 'volume_url']
        volume_values = ['', vol, '']
        volume_ws.append(volume_header)
        volume_ws.append(volume_values)

        issue_ws = wb.create_sheet("Issue")
        issue_header = ['doi', 'issue_title', 'editors', 'publication_date', 'issue_number', 'issue_url', 'collection', 'rights_statement','languages'] 
        issue_doi = "{0}.{1}.{2}".format(base_doi, vol_as_int, issue_no_as_int)
        issue_values = [
            issue_doi,
            '',
            utils.get_contibs(issue.get_editors()),#issue.get_editors(), # todo needs to be handled
            utils.get_full_date(issue.get_year(), issue_no),
            issue_no_as_int,
            url,
            cc_statement,
            'en||de'
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
            art = scenario.parseScenario(article_url)
            title = art.get_meta_tag("citation_title")
            status_code = art.get_status_code()
            if status_code != 200:
                print("Warning: failed to fetch {}".format(article_url))

            toc_section = art.get_section()
            section_ref = issue.get_section_ref(toc_section, title)
            non_ojs_meta = issue.get_section_meta_for_non_ojs(section_ref)
            
            authors = art.get_authors('Manfred Schewe')
            author_keys = utils.get_contibs(authors)
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
                utils.get_full_date(art.get_meta_tag("citation_publication_date")),
                article_url,
                art.get_abstract(),
                '',
                art.get_start_page(),
                '',# art.get_meta_tag("citation_lastpage"),
                '',# keywords
                '',# keywords_de
                non_ojs_meta['type'],# type
                non_ojs_meta['peer_reviewed'],# peer_reviewed
                '',# recommended citation
                non_ojs_meta['mint_doi']# skip doi
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

        wb.save("scenario_{}_{}.xlsx".format(year, issue_no))
        utils.save_wb()
        
        

        #crossref_job.generate()

