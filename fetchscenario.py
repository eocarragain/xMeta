import scenario
import argparse
from openpyxl import Workbook
#import xlsxwriter

base_url = "http://research.ucc.ie/scenario"
#year_range = range(2007, 2019)
year_range = range(2007, 2008)
issue_urls = []
for year in year_range:
    issue_urls.append("{0}/{1}/01".format(base_url, year))
    issue_urls.append("{0}/{1}/02".format(base_url, year))

if __name__ == '__main__':
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

        wb = Workbook()

        # grab the active worksheet
        journal_ws = wb.active
        journal_ws.title = "Journal"
        journal_header = ['doi', 'journal_title', 'short_tile', 'journal_issn', 'journal_url', 'reference_distribution_opts', 'publisher', 'license_url']
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
            '',#issue.get_editors(), # todo needs to be handled
            issue.get_year(),
            issue_no_as_int,
            url,
            "© {}, The Author(s). This work is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License.".format(issue.get_year()),
            'en||de'
        ]
        issue_ws.append(issue_header)
        issue_ws.append(issue_values)

        articles_ws = wb.create_sheet("Articles")
        art_header = ['doi','language','title','subtitle','authors','editors','publication_date','url','abstract','abstract_translated_to_en','first_page','last_page','keywords','keywords_de','type','peer_reviewed','Recommended citation for item']
        articles_ws.append(art_header)
        
        citations_ws = wb.create_sheet("Citations")
        citations_header = ["Article DOI","Complete reference"]
        citations_ws.append(citations_header)

        article_urls = issue.get_article_urls()
        for article_url in article_urls:
            if "http" not in article_url:
                article_url = "{0}/{1}".format(url.rsplit("/", 1)[0], article_url)
            url_parts = article_url.split("/")
            art_id = str(int(url_parts[-2]))
            art_doi = "{0}.{1}".format(issue_doi, art_id)
            language = url_parts[-1]
            art = scenario.parseScenario(article_url)
            status_code = art.get_status_code()
            if status_code != 200:
                print("Warning: failed to fetch {}".format(article_url))

            art_values = [
                art_doi,
                language,
                art.get_meta_tag("citation_title"),
                '',
                '', #todo
                '', #todo
                art.get_meta_tag("citation_publication_date"),
                article_url,
                art.get_abstract(),
                '',
                art.get_meta_tag("citation_firstpage"),
                art.get_meta_tag("citation_lastpage"),
                '',
                '',
                '',
                '',
                ''
            ]
            
            citations = art.get_citations()
            for citation in citations:
                citations_ws.append([art_doi, citation])

            articles_ws.append(art_values)



        wb.save("scenario_{}_{}.xlsx".format(year, issue_no))
        
        

        #crossref_job.generate()

