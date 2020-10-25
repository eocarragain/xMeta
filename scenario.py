from bs4 import BeautifulSoup
import requests
import base64
import mimetypes
import roman
import pandas as pd
import copy
import PyPDF2 as pyPdf
import io
import re

class parseIssue():
    def __init__(self, issue_url):
        self.issue_url = issue_url.strip()   
        req = requests.get(self.issue_url)
        self.issue_page = req.text
        self.soup = BeautifulSoup(self.issue_page, 'html.parser')
        self.issue_cover_path = self.get_issue_cover_path()

    #todo dry this out. duplicate of xmet.py
    def is_int(self, val):
        try: 
            int(val)
            return True
        except ValueError:
            return False 
    
    #todo dry this out. duplicate of xmet.py
    def get_volume_as_int(self, vol):
        if self.is_int(vol):
            return vol
        elif self.is_int(roman.fromRoman(vol)):
            return str(roman.fromRoman(vol))
        else:
            return "0"

    def get_volume(self):
        return ""

    def get_issue(self):
        return ""

    def get_year(self):
        return ""

    def get_editors(self):
        return []

    def get_articles_from_toc(self):
        return {}

    def get_article_urls_all_languages(self):
        # return self.get_articles_from_toc().keys()
        # note can't use keys as they are normalised
        urls = []
        articles = self.get_articles_from_toc()
        for key in articles:
            article = articles[key]
            urls.append(article['url'])
        return urls

    def get_unique_article_urls(self):
        return []

    def get_issue_galley_path(self):
        return ""

    def get_issue_galley(self):
        req = requests.get(self.get_issue_galley_path())
        if req.status_code != 200:
            raise Exception("Failed to load issue galley for {0}".format(self.page_url))
        return req.content        

    def get_encoded_issue_galley(self):
        b64 = base64.b64encode(self.get_issue_galley()).decode('utf-8')
        return b64

    #def get_encoded_issue_cover(self):
        # todo

    #def get_issue_cover(self):
        # todo

    def get_issue_cover_path(self):
        return ""

    def get_issue_cover_filename(self):
        issue_cover_path = self.get_issue_cover_path() 
        if issue_cover_path == "":
            return ""
        else:
            return issue_cover_path.split("/")[-1]

    def get_encoded_issue_cover(self):
        b64 = base64.b64encode(self.get_issue_cover()).decode('utf-8')
        return b64

    def get_issue_cover(self):
        req = requests.get(self.issue_cover_path)
        if req.status_code != 200:
            raise Exception("Failed to load cover image for {0}".format(self.page_url))
        return req.content

    def get_sections_as_dict(self):
        art = [
            {'ref': 'ART', 
            'title_en': 'Articles', 
            'title_de': 'Artikel', 
            'abbrev': 'art', 
            'policy': 'nan', 
            'seq': 2, 
            'editor_restricted': 0, 
            'meta_indexed': 1, 
            'meta_reviewed': 1, 
            'abstracts_not_required': 0, 
            'hide_title': 0, 
            'hide_author': 0, 
            'abstract_word_count': 150, 
            'cora': 'Article'}]
        return art

    def get_section_ref(self, toc_section="article", toc_title="title"):
        return 'ART'

class parseBooleanIssue(parseIssue):
    def get_volume(self):
        return False

    def get_issue(self):
        return self.get_year()

    def get_year(self):
        return self.issue_url.split("/")[-2]

    def get_editors(self):
        year = self.get_year()
        editors = {
            "2010": ["Alan Kelly", "Graham Allen", "Orla Murphy", "Michelle Nelson"],
            "2011": ["Alan Kelly", "Graham Allen", "Orla Murphy", "Ruth Ramsay", "Michelle Nelson"],
            "2012": ["Alan Kelly", "Gordon Dalton", "Dara O'Sullivan", "Janette Walton"],
            "2014": ["Liam Marnane", "Fergus McAuliffe"],
            "2015": ["Liam Marnane"]
        }
        return editors[year]

    def get_articles_from_toc(self):
        # nb urls used for dict keys are normalised to lower
        # good for comparison but the url value should not be taken directly from key
        articles = {}
        article_rows = self.soup.select("table.toc tr")
        for row in article_rows:
            seq = row.select("td.seq")[0]
            title = row.select("td.title")[0]
            title_str = title.get_text()
            title_str = " ".join(title_str.split()).strip()
            author = row.select("td.author")[0]
            if len(author.get_text().strip()) == 0:
                author_str = "Liam Marnane"
            else:
                author_str = author.get_text()
                author_str = author_str.replace('\n', '').replace('\r', '')
                author_str = " ".join(author_str.split()).strip()
                # print(author_str)
            affiliation = row.select("td.affiliation")[0]
            affiliation_str = affiliation.get_text()
            affiliation_str = " ".join(affiliation_str.split()).strip()
            title_link = title.select("a")[0]
            url_html = title_link['href']
            if url_html.startswith("http"):
                url_html = url_html 
            else:
                url_html = "http://{0}{1}".format(self.issue_url.split("/")[-4], url_html)

            seq = url_html.split("/")[-2]
            article = {
                "seq": seq,
                "title": title_str,
                "authors": author_str,
                "affiliation": affiliation_str,
                "url": url_html,
                "pdf": url_html.replace("/boolean/", "/boolean/pdf/")
            }

            articles[url_html.lower()] = article
        return articles

    def get_unique_article_urls(self):
        all_urls = self.get_article_urls_all_languages()
        url_dict = {}
        unique_urls = []
        for url in all_urls:
            id = url.split("/")[-2]
            url_dict[id] = url
        return url_dict.values()

    def get_issue_galley_path(self):
        year = self.get_year()
        issue_galley_path = "http://publish.ucc.ie/boolean/pdf/{}/00/boolean-{}.pdf".format(year, year)
        return issue_galley_path     

    def get_issue_cover_path(self):
        year = self.get_year()
        issue_cover_path = "http://ojs.ucc.ie/public/site/boolean_covers/boolean-{}_border.png".format(year)
        return issue_cover_path

class parseScenarioIssue(parseIssue):
    def __init__(self, issue_url):
        parseIssue.__init__(self, issue_url)
        self.section_mapping_wb = "scenario_tocs.xlsx"

    def get_issn(self):
        return "1649-8526"

    def get_volume_no_label(self):
        vol = self.get_volume()
        vol = vol.split(" ")[-1]
        return vol

    def get_volume(self):
        vol = self.soup.select("span.volume")[0].get_text().strip()
        return vol

    def get_issue(self):
        return self.get_issue_year()["issue"]

    def get_year(self):
        return self.get_issue_year()["year"]

    def get_editors(self):
        return ["Manfred Schewe", "Susanne Even"]

    def get_issue_year(self):
        issue_year = {}
        joined = self.soup.select("span.issue")[0].get_text()
        joined = joined.replace("—", "-")
        parts = joined.split("-")
        issue_year["issue"] = parts[0].lower().replace("issue", "").strip()
        issue_year["year"] = parts[1].strip()

        return issue_year

    def get_fallback_section(self, toc_section, toc_title):
        if "about the authors" in toc_title.lower():
            toc_section = "biodata"
        elif "biodata" in toc_title.lower():
            toc_section = "biodata"
        elif "autorinnen" in toc_title.lower():
            toc_section = "biodata"
        elif "foreword" in toc_title.lower() or "vorwort" in toc_title.lower():
            toc_section = "foreword"
        elif toc_section == "":
            toc_section = "article"  

        return toc_section
 
    def get_articles_from_toc(self):
        # nb urls used for dict keys are normalised to lower
        # good for comparison but the url value should not be taken directly from key
        articles = {}
        article_rows = self.soup.select("div.metadata tr")
        for row in article_rows:
            if len(row.select("th")) > 0:
                continue
            # Can't rely on classnames here as they vary across issues
            # Just workd with col poisitions    
            cols = row.select("td")
            section = cols[0].get_text().strip()
            title_link = cols[1].select("span.doctitle a")[0]
            title = title_link.get_text().strip()
            section = self.get_fallback_section(section, title)
            url_html = title_link['href']
            if url_html.startswith("http"):
                url_html = url_html 
            else:
                url_html = "{0}/{1}".format(self.issue_url.rsplit("/", 1)[0], url_html)
            media_links = []
            media_anchors = cols[2].select("span.media a")
            for anchor in media_anchors:
                media_links.append(anchor['href'])
            authors = cols[3].get_text().strip()
            page_link = cols[4].select("a")[0]
            start_page = page_link.get_text().strip()
            url_pdf = page_link['href']
            article = {
                "section": section,
                "title": title,
                "url": url_html.strip(),
                "media": media_links,
                "authors": authors,
                "start_page": start_page,
                "pdf": url_pdf
            }

            articles[url_html.lower()] = article

        return articles

    def get_unique_article_urls(self):
        all_urls = self.get_article_urls_all_languages()
        url_dict = {}
        unique_urls = []
        for url in all_urls:
            lang = url.split("/")[-1]
            id = url.split("/")[-2]
            if id in url_dict:
                if lang == 'en' and url_dict[id].endswith("de"):
                    url_dict[id] = url
            else:
                url_dict[id] = url
        return url_dict.values()

    def get_article_urls_direct(self):
        # deprecated. use get_article_urls_all_languages and get_unique_article_urls
        articles = {}
        article_links = self.soup.select("div.toctitle > span.doctitle a")
        for article_link in article_links:
            title = article_link.get_text()
            link = article_link['href']
            articles[link] = title

        return articles

    def get_issue_galley_path(self):
        whole_issue_link = self.soup.find_all("a", string="Whole Issue")[0]["href"]
        if whole_issue_link.startswith("http"):
            return whole_issue_link 
        else:
            whole_issue_link ="{0}/{1}".format(self.issue_url.rsplit("/", 1)[0], whole_issue_link)
            return whole_issue_link

    def get_issue_cover_paths(self):
        paths = []
        year = self.get_year()
        issue_num = str(int(self.get_issue()))
        issue_str = issue_num.rjust(2, '0')
        paths.append("http://ojs.ucc.ie/public/site/scenario_covers/{}_{}.jpg".format(year, issue_str))
        paths.append("https://www.ucc.ie/en/media/electronicjournals/scenario/journal/{0}issue{1}-150x215.jpg".format(year, issue_num))
        paths.append("https://www.ucc.ie/en/media/electronicjournals/scenario/journal/{0}Issue{1}-150x215.jpg".format(year, issue_num))
        paths.append("https://www.ucc.ie/en/media/electronicjournals/scenario/journal/{0}Issue{1}psd-150x215.jpg".format(year, issue_num))
        paths.append("https://www.ucc.ie/en/media/electronicjournals/scenario/journal/{0}issue{1}psd-150x215.jpg".format(year, issue_num))
        return paths

    def get_issue_cover_path(self):
        paths = self.get_issue_cover_paths()
        for path in paths:
            req = requests.get(path)
            if req.status_code == 200:
                return path
        return ""

    def get_sections_as_dict(self):
        wb = self.section_mapping_wb
        xl = pd.ExcelFile(wb)
        section_df = xl.parse('section_meta')
        #print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        #print(section_df.to_dict('records'))
        return section_df.to_dict('records')
    
    def get_section_word_count(self, section_ref):
        wb = self.section_mapping_wb
        xl = pd.ExcelFile(wb)
        section_df = xl.parse('section_meta')
        matches_df = section_df[section_df['ref'].eq(section_ref)]
        if len(matches_df) > 0: 
            return matches_df.iloc[0]['abstract_word_count']
        else:
            return '0'

    def get_section_ref(self, toc_section, toc_title):
        toc_section = self.get_fallback_section(toc_section, toc_title)
        wb = self.section_mapping_wb
        xl = pd.ExcelFile(wb)
        map_df = xl.parse('section_map')
        matches_df = map_df[map_df['section'].eq(toc_section)]
        if len(matches_df) > 0: 
            return matches_df.iloc[0]['ref']
        else:
            return 'ART'
    
    def get_section_meta_for_non_ojs(self, ref):
        cora_meta = {}
        wb = self.section_mapping_wb
        xl = pd.ExcelFile(wb)
        section_df = xl.parse('section_meta')
        matches_df = section_df[section_df['ref'].eq(ref)]
        if len(matches_df) > 0: 
            cora_meta['ref'] = 'ref'
            cora_meta['type'] = matches_df.iloc[0]['cora']
            if matches_df.iloc[0]['meta_reviewed'] == 1:
                cora_meta['peer_reviewed'] = "Peer reviewed"
            else:
                cora_meta['peer_reviewed'] = "Not peer reviewed"
            if matches_df.iloc[0]['meta_indexed'] == 1:
                cora_meta['mint_doi'] = True
            else:
                cora_meta['mint_doi'] = False        
        return cora_meta

    def get_pages_from_ojs2(self):
        # return a dict with article idenifier as key, e.g. 00_en for foreword
        # and start_page as value
        # else return empty dict
        pages = {}
        year = self.get_year()
        issue_num = str(int(self.get_issue()))
        issue_str = issue_num.rjust(2, '0')
        xml_file = "./ojs2_exports/scenario_{}_{}_ojs2.xml".format(year, issue_str)
        # try to open xml
        try:
            print("about to open xml")
            with open(xml_file, encoding="utf8") as fp:
                soup = BeautifulSoup(fp, "xml")
                articles = soup.find_all("article")
                for article in articles:
                    start_page = article.find("pages").get_text().strip()
                    print(start_page)
                    embed = article.find("embed")
                    if "filename" in embed.attrs:
                        filename = embed["filename"]
                        filename = filename.split(".")[0]
                        filename_parts = filename.split("-")
                        key = "{}_{}".format(filename_parts[0], filename_parts[-1])
                        pages[key] = start_page
                    else:
                        continue

            return pages
        except Exception as e:
            print ("Failed to load or parse ojs2 xml for {}".format(xml_file))
            print ("Exception: {}".format(e))
            return {}

class parseArticle():
    def __init__(self, url):
        self.page_url = url.strip()   
        req = requests.get(self.page_url)
        self.page = self.get_page(req)
        self.soup = BeautifulSoup(self.page, 'html.parser')
        self.issue_url = self.get_issue_url()
        self.doi_prefix = "10.33178"
        self.issue = self.get_issue_obj()
        self.title = self.get_title()
        self.doi = self.get_doi()
        self.pages = self.get_pages()

    def get_issue_obj(self):
        return parseIssue(self.issue_url)

    def get_doi(self):
        return ""

    def has_doi(self):
        return False

    def get_issue_url(self):
        url = self.page_url.rsplit("/", 3)[0]
        url = self.strip_wayback(url)
        return url

    def strip_wayback(self, url):
        url = url
        if "web.archive.org" in url:
            url = url.split("/", 5)[5]
        return url

    def get_status_code(self):
        return self.status_code

    def get_page(self, req):
        if req.status_code == 200:
            self.status_code = 200
            return req.text
        
        # try to fetch from wayback
        wb_urls = [
            self.get_wayback_api_url(self.page_url), 
            self.get_wayback_api_url(self.page_url.replace("research.ucc.ie", "publish.ucc.ie"))
            ]
        for wb_url in wb_urls:
            wb_api = requests.get(wb_url)
            wb_api_resp = wb_api.json()
            print(wb_api_resp)
            if wb_api_resp["archived_snapshots"] != {}:
                wb_url = wb_api_resp["archived_snapshots"]["closest"]["url"]
                wb_page_req = requests.get(wb_url)
                if wb_page_req.status_code == 200:
                    self.status_code = 200
                    self.page_url = wb_url
                    return wb_page_req.text
                else:
                    print("Warning: failed to load from wayback: {}".format(wb_url))

        self.status_code = 500
        raise Exception("Failed to load html for {0}".format(self.page_url))
        return req.text


    def get_wayback_api_url(self, journal_url):
        return "http://archive.org/wayback/available?url={}".format(journal_url)

    #def get_pdf(self):
        #todo

    def get_toc_elements(self):
        url = self.strip_wayback(self.page_url)
        toc = self.issue.get_articles_from_toc()[url.lower()]
        return toc

    def get_start_page(self):
        return self.pages["start_page"]

    def get_end_page(self):
        return self.pages["end_page"]

    #todo dry this out. duplicate of xmet.py and above class
    def is_int(self, val):
        try: 
            int(val)
            return True
        except ValueError:
            return False 
    
    #todo dry this out. duplicate of xmet.py and above class
    def get_page_as_int(self, page):
        if self.is_int(page):
            return int(page)
        elif self.is_int(roman.fromRoman(page.upper())):
            return int(roman.fromRoman(page.upper()))
        else:
            return 0

    def get_pdf_page_count(self):
        # open pdf & get page count
        pdf_file = io.BytesIO(self.get_pdf())
        pdf_reader = pyPdf.PdfFileReader(pdf_file)
        num_pages = int(pdf_reader.numPages)
        return num_pages

    def get_title_from_toc(self):
        title = self.get_toc_elements()["title"]
        title = " ".join(title.split()).strip()
        if len(title.strip()) == 0:
            raise Exception("Failed to get title for {}".format(self.page_url))
        return title

    def get_title(self):
        return self.get_title_from_toc()

    def get_word_list(self, str):
        str = " ".join(str.split()).strip()
        #res = re.findall(r'\w+', str)
        res.split( )
        return res       

    def get_word_count(self, str):
        res = len(self.get_word_list(str))
        return res

    def get_language(self):
        lang = self.page_url.split("/")[-1]
        if lang in ['en', 'de']:
            return lang
        else:
            return 'en'

    def get_pages(self):
        return {}

    def get_abstract(self):
        return ""

    def get_citations(self):
        return []

    def get_encoded_pdf(self):
        return base64.b64encode(self.get_pdf()).decode('utf-8')

    def get_encoded_html(self):
        return base64.b64encode(self.get_html().encode('ascii')).decode('utf-8')

    def get_absolute_url(self, frag):
        if frag.startswith("http"):
            url = frag
        elif frag.startswith("/web/"):
            url ="{0}{1}".format("http://web.archive.org", frag) 
        else:
            url ="{0}/{1}".format(self.page_url.rsplit("/", 1)[0], frag)
        return url

    def strip_wb(self, url):
        if  "web.archive.org" in url:
            parts = url.split("//")
            if len(parts) < 3:
                orig_url = url
            else:
                orig_url = "http://{}".format(parts[2])
        else: 
            orig_url = url
        return orig_url

    def get_html(self):
        return ""

class parseBoolean(parseArticle):
    def __init__(self, issue_url):
        parseArticle.__init__(self, issue_url)
        self.issue = self.get_issue_obj() 
        self.title = self.get_title()
        self.doi = self.get_doi()
        self.pages = self.get_pages()

    def has_doi(self):
        return True

    def get_page(self, req):
        if req.status_code == 200:
            self.status_code = 200
            return req.text
        
        # try to fetch from wayback
        wb_urls = [
            self.get_wayback_api_url(self.page_url), 
            self.get_wayback_api_url(self.page_url.replace("research.ucc.ie", "publish.ucc.ie"))
            ]
        for wb_url in wb_urls:
            wb_api = requests.get(wb_url)
            wb_api_resp = wb_api.json()
            print(wb_api_resp)
            if wb_api_resp["archived_snapshots"] != {}:
                wb_url = wb_api_resp["archived_snapshots"]["closest"]["url"]
                wb_page_req = requests.get(wb_url)
                if wb_page_req.status_code == 200:
                    self.status_code = 200
                    self.page_url = wb_url
                    return wb_page_req.text
                else:
                    print("Warning: failed to load from wayback: {}".format(wb_url))

        self.status_code = 500
        #raise Exception("Failed to load html for {0}".format(self.page_url))
        return req.text

    def get_issue_obj(self):
        return parseBooleanIssue(self.issue_url)

    def url_in_wb(self, url):
        wb_api_url = self.get_wayback_api_url(url)
        wb_api_resp = requests.get(wb_api_url).json()
        if wb_api_resp["archived_snapshots"] != {}:
            wb_url = wb_api_resp["archived_snapshots"]["closest"]["url"]
            if wb_api_resp["archived_snapshots"]["closest"]["status"] == "200":
                return wb_url
        return False

    def get_pdf(self):
        pdf_url = self.page_url.replace("/boolean/", "/boolean/pdf/")
        pdf_urls = [pdf_url]
        alt_base = pdf_url.rsplit("/", 3)[0]
        url_parts = pdf_url.rsplit("/", 5)

        alt_filename = "{0}-{1}-{2}-{3}-{4}.pdf".format(
            url_parts[-2], #art_id
            url_parts[-3], #name
            url_parts[-5], #year
            url_parts[-4], #issue, ie. 00
            url_parts[-1]  #lang
        )
        alt_pdf_url = "{0}/{1}".format(alt_base, alt_filename)
        pdf_urls.append(alt_pdf_url)

        poss_urls = copy.deepcopy(pdf_urls)
        for poss_url in poss_urls:
            check_wb = self.url_in_wb(poss_url) 
            if check_wb != False:
                wb_url = check_wb
                pdf_urls.append(wb_url)

        alt_base2 = "http://ojs.ucc.ie/public/site/boolean_covers"
        alt_pdf_url2 = "{0}/{1}".format(alt_base2, alt_filename)
        pdf_urls.append(alt_pdf_url2)

        for url in pdf_urls:
            print(url)
            req = requests.get(url)
            if req.status_code == 200:
                return req.content

        raise Exception("Failed to load pdf for {0}".format(self.page_url))

    def get_cite(self):
        cite = self.soup.select("div.citetext")[0].get_text()
        cite = " ".join(cite.split()).strip()
        return cite

    def get_pages(self):
        pages = {}
        if self.status_code != 200:
            return {"start_page": "0", "end_page": "0"}

        cite = self.get_cite()
        cite = cite.lower().replace(" ", "").replace(".", "")
        reg = "pp?\d+(-\d+)?"
        match = re.search(reg, cite)
        if match:
            pages_str = match.group(0)
            pages_str = pages_str.replace("p", "")
            page_parts = pages_str.split("-")
            start_page = page_parts[0]
            pages["start_page"] = start_page
            if len(page_parts) > 1:
                end_page = page_parts[1]
            else:
                end_page = start_page 
            pages["end_page"] = end_page
        else:
            # raise Exception("Failed to find pages for {}".format(self.page_url))
            print("WARNING: Failed to find pages for {}".format(self.page_url))
            return {"start_page": "0", "end_page": "0"}
        return pages

    def get_abstract(self):
        abstract = ""
        section_limit = 150        
        wc = 0
        els = self.soup.select('div#content p')
        if len(els) > 0:
            el_no = 0
            while wc < section_limit and el_no < len(els):
                abstract = "{} {}".format(abstract, els[el_no].get_text())
                wc = self.get_word_count(abstract)
                el_no += 1

        if wc > section_limit:
            word_list = self.get_word_list(abstract)
            abstract = " ".join(word_list[:section_limit])
            abstract = "{} ...".format(abstract)

        abstract = " ".join(abstract.split()).strip()
        return abstract

    def parse_authors(self, authors_str, fallback_author=''):
        authors = [authors_str]
        if len(authors) == 0:
            if fallback_author != '':
                authors.append(fallback_author)
        return authors
  
    def get_authors_from_toc(self, fallback_author=''):
        toc = self.get_toc_elements()
        authors_str = toc["authors"]
        authors = self.parse_authors(authors_str, fallback_author)
        return authors

    def get_authors(self, fallback_author=''):
        return self.get_authors_from_toc(fallback_author)

    def get_html(self):
        if self.status_code != 200:
            return ""
        html_template = """<!DOCTYPE html><html><head>
                           <link rel="stylesheet" href="../../../../../public/site/boolean_html.css" />
                           <script src="../../../../../public/site/boolean_html.js" />
                           </head><body><span /></body></html>"""
        template = BeautifulSoup(html_template, 'html.parser')
        header = self.soup.new_tag("div")
        header["id"] = "header"


        title = self.soup.new_tag("h1")
        title_str = self.soup.select("h1.title")[0].get_text()
        title["id"] = "title"
        title.string = title_str

        author = self.soup.new_tag("div")
        author_str = self.soup.select("h2.author")[0].get_text()
        author["id"] = "author"
        author.string = author_str

        affil = self.soup.new_tag("div")
        affil_str = self.soup.select("h3.affiliation")[0].get_text()
        affil["id"] = "affiliation"
        affil.string = affil_str

        doi = self.get_doi()
        mint_doi = self.has_doi()
        citation_str = self.get_cite()
        if len(doi) > 0 and mint_doi == True:
            citation_str = "{0}, doi:{1}".format(citation_str, doi)
        citation = self.soup.new_tag("div")
        citation["id"] = "citation"
        citation.string = citation_str
        
        header.append(title)
        header.append(author)
        header.append(affil)
        header.append(citation)

        content_box = self.soup.select("#content")[0]

        for img in content_box.find_all('img'):
            if "src" not in img.attrs:
                continue   
            img_url = self.get_absolute_url(img["src"])
            print("########################## {0}".format(img_url))
            # horrible hack for broken image
            bad_images = [
                "http://research.ucc.ie/boolean/2011/00/Murray/35/35-Murray-2011-00-en/media/image3.png"
            ]
            if img_url in bad_images:
                continue
            image_req = requests.get(img_url)
            if image_req.status_code != 200:
                if  "web.archive.org" in img_url:
                    orig_img_url = "http://{}".format(img_url.split("//")[2])
                    image_req = requests.get(orig_img_url)
                    print("retrying image download from original: {}".format(orig_img_url))
                    if image_req.status_code != 200:
                        raise Exception("Unable to download image {0} from research.ucc.ie or from {1}".format(img_url, self.page_url))
                else:        
                    raise Exception("Unable to download image {0} for page {1}".format(img_url, self.page_url))
            image_data = image_req.content

            mimetype = mimetypes.guess_type(img_url)[0]
            img['src'] = "data:%s;base64,%s" % (mimetype, base64.b64encode(image_data).decode('utf-8'))


        body = template.find("body")
        body.append(header)
        body.append(content_box)
        return template

class parseScenario(parseArticle):
    def __init__(self, issue_url):
        parseArticle.__init__(self, issue_url)
        self.meta_tags = self.get_meta_tags()
        self.issue = self.get_issue_obj()
        self.title = self.get_title()
        self.doi = self.get_doi()
        self.pages = self.get_pages()

    def get_issue_obj(self):
        return parseScenarioIssue(self.issue_url)

    def get_doi(self):
        base = "{}/scenario".format(self.doi_prefix)
        vol = self.issue.get_volume_no_label()
        vol_int = self.issue.get_volume_as_int(vol)
        issue = int(self.issue.get_issue())
        art = int(self.page_url.rsplit("/", 2)[1])
        doi = "{}.{}.{}.{}".format(base, vol_int, issue, art)
        return doi

    def has_doi(self):
        toc_section = self.get_section()
        section_ref = self.issue.get_section_ref(toc_section, self.title)
        non_ojs_meta = self.issue.get_section_meta_for_non_ojs(section_ref)
        mint_doi = non_ojs_meta["mint_doi"]
        return mint_doi
        
    def get_pdf(self):
        form_data = {}
        f = self.soup.select("form")
        form = self.soup.select("div.print > form")[0]
        for child in form.descendants:
            if "name" in child.attrs:
                name = child["name"]
                value = child["value"]
                form_data[name] = value
        response = requests.post("http://minerva2.ucc.ie/cgi-bin/uncgi/make.pdf", data=form_data)
        if response.status_code != 200:
            raise Exception("Failed to load pdf for {0}".format(self.page_url))
        return response.content

    def get_meta_tags(self):
        meta_tags = {}
        meta_tags["citation_author"] = []
        tags = self.soup.select('head > meta')
        #print(tags)
        for tag in tags:
            if "name" in tag.attrs:
                name = tag["name"]
                content = tag["content"].strip()
                if tag["name"] == "citation_author":
                    if content == "/":
                        continue
                    meta_tags[name].append(content)
                    #print(meta_tags[name])
                else:               
                    meta_tags[name] = content

        return meta_tags

    def get_meta_tag(self, tag):
        if tag in self.meta_tags:
            return self.meta_tags[tag]
        else:
            if tag == "citation_author":
                return []
            else:
                return ""

    def get_start_page_from_toc(self):
        toc = self.get_toc_elements()
        return toc["start_page"]

    def get_start_page_from_ojs2(self):
        art_id = int(self.page_url.rsplit("/", 2)[1])
        art_id_str = str(art_id).rjust(2, '0')
        key = "{}_{}".format(art_id_str, self.get_language())
        issue_pages = self.issue.get_pages_from_ojs2()
        print(issue_pages)
        # if valid return start_page else return False
        if key in issue_pages:
            print("found {} in issue pages".format(key))
            start_page = issue_pages[key]
            if self.get_page_as_int(start_page) > 0:
                print("start page from ojs2: {}".format(start_page))
                return start_page
            else:
                return False
        else:
            print("Failed to find key {} in issue pages".format(key))
            return False 

    def get_pages(self):
        pages = {}
        start_page = self.get_start_page_from_ojs2()
        if start_page == False:
            print("getting start page from toc")
            start_page = self.get_start_page_from_toc()  
        pages["start_page"] = str(start_page)

        if self.is_int(start_page) == False:
            is_roman = True
        else:
            is_roman = False
    
        try:
            num_pages = self.get_pdf_page_count()
        
            if self.get_language() == 'en':
                url = self.page_url
                de_url = url.replace ("/en", "/de")
                de_url_lower = de_url.lower()
                if "/foreword/" in url.lower():
                    de_url_lower = de_url_lower.replace("/foreword/", "/vorwort/")
                print(de_url)
                articles_from_toc = self.issue.get_articles_from_toc()
                if de_url_lower in articles_from_toc.keys():
                    de_article_from_toc = articles_from_toc[de_url_lower]
                    de_url = de_article_from_toc["url"]
                    print("found de url {}".format(de_url))
                    art_de = parseScenario(de_url)
                    art_de_sp = art_de.get_start_page()
                    art_de_sp_as_int = art_de.get_page_as_int(art_de_sp)
                    num_pages = num_pages + art_de.get_pdf_page_count()

                    # sometimes the de verrsion comes first. if so, use it as start page        
                    if art_de_sp_as_int < self.get_page_as_int(start_page):
                        start_page =  art_de_sp
                        pages["start_page"] = start_page
                    
            # calculate last_page including roman numerals
            start_page_int = self.get_page_as_int(start_page)

            end_page = start_page_int + (num_pages - 1)
            if is_roman == True:
                end_page = roman.toRoman(end_page).lower()
        except Exception as e:
            print ("Failed to load number of pages from pdf: {}".format(e))
            raise(e)
            #fallback to article meta element (unreliable)
            end_page = self.get_end_page_from_meta()

        pages["end_page"] = str(end_page)
        print(pages)
        return pages

    def get_end_page_from_meta(self):
        end_page = self.get_meta_tag("citation_lastpage")
        return end_page

    def get_title_from_meta(self):
        title = self.get_meta_tag("citation_title")
        # remove dois from titles
        doi_reg = "\s?http(s)://doi.org/10.33178/scenario.\d\d.\d.\d"
        title = re.sub(doi_reg, "", title)

        return title   
   
    def get_section(self):
        section = self.get_toc_elements()["section"]
        return section

    def get_authors_from_meta(self, fallback_author=''):
        authors = []
        meta_authors = self.get_meta_tag("citation_author")
        print(meta_authors)
        for author in meta_authors:
            print(author)
            if "," in author:
                parts = author.split(",", 1)
                author = "{} {}".format(parts[1], parts[0]).strip()

            authors.append(author)
        
        authors = list(map(str.strip, authors)) 
        authors = list(filter(None, authors))
        if len(authors) == 0:
            if fallback_author != '':
                authors.append(fallback_author)
        return authors

    def parse_authors(self, authors_str, fallback_author=''):
     #known patterns
        #John Doe/Jane Doe/Jenny Doe
        #John Doe & Jane Doe
        #John Doe and Jane Doe
        #John Doe und Jane Doe
        #John Doe; Jane Doe; Jenny Doe
        #John Doe, Jane Doe, Jenny Doe
        #John Doe, Jane Doe & Jenny Doe
        #John Doe, Jane Doe and Jenny Doe

        #if author in bad_names:
        #    parts = author.split(",")
        #    author = "{} {}".format(parts[1], parts[0]).strip()
        authors = []
        authors_str = self.clean_authors_str(authors_str)
        authors_str = " ".join(authors_str.split()).strip()
        parts = []
        if "/" in authors_str:
            parts = authors_str.split("/")
        elif ";" in authors_str:
            parts = authors_str.split(";")
        elif "," in authors_str:
            parts = authors_str.split(",")
        else:
            parts = [authors_str]

        for part in parts:
            part = part.replace(" and ", "&")
            part = part.replace("&amp;", "&")
            part = part.replace(" und ", "&")
            part_parts = part.split("&")
            authors = authors + part_parts

        authors = list(map(str.strip, authors)) 
        authors = list(filter(None, authors))
        authors = self.remove_non_authors(authors)
        if len(authors) == 0:
            if fallback_author != '':
                authors.append(fallback_author)
        return authors

    def clean_authors_str(self, authors_str):        
        bad_strs = [
            "Konferenzbericht von",
            "(Université Grenoble Alpes)",
            "mit Unterstützung von Julia Collazo, Paul Schneeberger und Jeruna Tiemann"]
        for bad_str in bad_strs:
            authors_str = authors_str.replace(bad_str, "").strip()

        return authors_str

    def remove_non_authors(self, authors):
        non_author_strs = [
            "4th SCENARIO FORUM SYMPOSIUM Participants",
            "aus: FAUST von Johann Wolfgang von Goethe",
            "from: FAUST by Johann Wolfgang von Goethe"
        ]

        for author in authors:
            if author in non_author_strs:
                authors.remove(author)
            elif "Johann Wolfgang" in author:
                authors.remove(author)
            elif "Participants" in author:
                authors.remove(author)
        return authors

    def get_authors_from_body(self, fallback_author=''):
        authors_str = self.soup.find(class_="docauthor").get_text()
        authors = self.parse_authors(authors_str, fallback_author)
        return authors

    def get_authors_from_toc(self, fallback_author=''):
        toc = self.get_toc_elements()
        authors_str = toc["authors"]
        authors = self.parse_authors(authors_str, fallback_author)
        return authors

    def get_authors(self, fallback_author=''):
        return self.get_authors_from_toc(fallback_author)

    def get_toc_section(self):
        toc = self.get_toc_elements()
        section = toc["section"]
        return section

    def get_abstract(self):
        els = self.soup.select('div.abstract p')
        abstract = ""
        toc_section = self.get_section()
        section_ref = self.issue.get_section_ref(toc_section, self.title)
        section_limit = int(self.issue.get_section_word_count(section_ref))
        if section_limit == 0:
            return abstract

        wc = 0
        if len(els) > 0:
            for el in els:
                abstract = "{} {}".format(abstract, el.get_text())
        
        wc = self.get_word_count(abstract)
        if wc < 20:
            els = self.soup.select('div.text p')
            if len(els) > 0:
                el_no = 0
                while wc < section_limit and el_no < len(els):
                    abstract = "{} {}".format(abstract, els[el_no].get_text())
                    wc = self.get_word_count(abstract)
                    el_no += 1

            if wc > section_limit:
                word_list = self.get_word_list(abstract)
                abstract = " ".join(word_list[:section_limit])
                abstract = "{} ...".format(abstract)

        abstract = " ".join(abstract.split()).strip()
        return abstract

    def get_citations(self):
        content_box = self.soup.select("div.content")[0]
        citations = []
        heading = content_box.find_all(['a', 'div', 'p'], string="Bibliography")
        if len(heading) > 0:
            #print(heading)
            first_entry = heading[0].find_next("p")
            #print(first_entry)
            first = first_entry.get_text()
            first = " ".join(first.split()).strip()
            citations.append(first)
            # others = first_entry.find_next_siblings('p')
            others = first_entry.find_next_siblings()
            for other in others:
                if other.name == 'p':
                    text = other.get_text()
                    text = " ".join(text.split()).strip()
                    #print(text)
                    if "[SCBibliograpySection]" in text:
                        continue
                    if 'appendix' in text.lower():
                        break
                    citations.append(text)
                else:
                    break
        return citations

    def get_html_links(self):
        links = {}
        src_types = ["embed", "source", "track"]

        content_box = self.soup.select("div.content")[0]
        for a in content_box.find_all('a'):
            if "href" in a.attrs:
                if a["href"].startswith("#"):
                    continue
                url = self.get_absolute_url(a["href"])
                url = self.strip_wb(url)
                links[url] = {"link_type": "a", "page_url": self.page_url, "text": a.get_text(), "url": url}

        for src_type in src_types:
            for el in content_box.find_all(src_type):
                if "src" in el.attrs:
                    url = self.get_absolute_url(el["src"])
                    url = self.strip_wb(url)
                    links[url] = {"link_type": "src", "page_url": self.page_url, "text": a.get_text(), "url": url}
        return links

    def get_html(self):
        html_template = """<!DOCTYPE html><html><head>
                           <link rel="stylesheet" href="../../../../../public/site/scenario_html.css" />
                           <script src="../../../../../public/site/scenario_html.js" />
                           </head><body><span /></body></html>"""
        template = BeautifulSoup(html_template, 'html.parser')
        doi = self.get_doi()
        mint_doi = self.has_doi()
        #doi = self.soup.select('span[class="doi"] > a')
        #if len(doi) > 0:
        #    doi = doi[0].get_text()
        vol = self.soup.select('span[class="volume"]')[0].get_text()
        issue = self.soup.select('span[class="issue"]')[0].get_text()
        year = self.soup.select('span[class="date"]')[0].get_text().replace("Year", "").replace("Jahrgang", "").strip()
        citation_str = "{0}, {1}, {2}".format(vol, issue, year)
        if len(doi) > 0 and mint_doi == True:
            citation_str = "{0}, doi:{1}".format(citation_str, doi)
        citation = self.soup.new_tag("div")
        citation["id"] = "citation"
        citation.string = citation_str
        cc_statement = "© {}, The Author(s). This work is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License.".format(year)
        cc = self.soup.new_tag("div")
        cc["class"] = "cc_statement"
        cc["id"] = "cc_top"
        cc.string = cc_statement
        metadata = self.soup.select('div[class="metadata"]')[0]
        metadata.append(citation)
        metadata.append(cc)
        content_box = self.soup.select("div.content")[0]
        if len(self.soup.select("ol.toc")) > 0:
            toc = self.soup.select("ol.toc")[0]
            if len(toc.get_text().strip()) > 0: 
                container = self.soup.new_tag("div")
                toc_head = self.soup.new_tag("h3")
                toc_head.string = "Contents"
                container.insert(1, toc_head)
                container.insert(2, toc)
                first_heading = self.soup.select("div.text h1")[0]
                first_heading.insert_before(container)
        # convert images to inline base6
        postnav = self.soup.select("div.postnav")[0]
        postnav.decompose()
        for img in content_box.find_all('img'):
            if "src" not in img.attrs:
                continue
            if "scenario-back.png" in img["src"]:
                img.replace_with("[Back]")
                continue    
            img_url = self.get_absolute_url(img["src"])
            print("########################## {0}".format(img_url))
            # horrible hack for broken image
            bad_images = [
                "http://research.ucc.ie/scenario/2018/02/TrimmisKalogirou/03/en/media/image6.jpeg",
                "http://research.ucc.ie/journals/scenario/2019/02/PrivasBreaute/10/en/media/image6.png",
                "http://research.ucc.ie/scenario/2019/02/PrivasBreaute/10/en/media/image6.png",
                "http://web.archive.org/web/20161214045437im_/http://research.ucc.ie/scenario/2010/02/donnery/03/en/image7.png image9.png image6.png image8.png image4.png image5.png",
                "http://web.archive.org/web/20161214045437im_/http://research.ucc.ie/scenario/2010/02/donnery/03/en/image7.png%20image9.png%20image6.png%20image8.png%20image4.png%20image5.png",
                "http://web.archive.org/web/20161214045437/http://research.ucc.ie/scenario/2010/02/donnery/03/en/image7.png%20image9.png%20image6.png%20image8.png%20image4.png%20image5.png",
                "http://web.archive.org/web/20161214045437/http://research.ucc.ie/scenario/2010/02/donnery/03/en/image7.png image9.png image6.png image8.png image4.png image5.png",
                "http://research.ucc.ie/scenario/2010/02/donnery/03/en/image7.png%20image9.png%20image6.png%20image8.png%20image4.png%20image5.png",
                "http://research.ucc.ie/scenario/2010/02/donnery/03/en/image7.png image9.png image6.png image8.png image4.png image5.png",
                "http://research.ucc.ie/scenario/2015/01/Berghoff/05/de/media/image3.jpeg",
                "http://research.ucc.ie/scenario/2019/02/VillanuevaOSullivan/06/en/media/image3.jpg media/image4.jpg",
                "http://research.ucc.ie/scenario/2019/02/VillanuevaOSullivan/06/en/media/image3.jpg%20media/image4.jpg"
            ]
            if img_url in bad_images:
                continue
            image_req = requests.get(img_url)
            if image_req.status_code != 200:
                if  "web.archive.org" in img_url:
                    orig_img_url = "http://{}".format(img_url.split("//")[2])
                    image_req = requests.get(orig_img_url)
                    print("retrying image download from original: {}".format(orig_img_url))
                    if image_req.status_code != 200:
                        raise Exception("Unable to download image {0} from research.ucc.ie or from {1}".format(img_url, self.page_url))
                else:        
                    raise Exception("Unable to download image {0} for page {1}".format(img_url, self.page_url))
            image_data = image_req.content

            mimetype = mimetypes.guess_type(img_url)[0]
            img['src'] = "data:%s;base64,%s" % (mimetype, base64.b64encode(image_data).decode('utf-8'))

            # parent a tag
            parent = img.parent
            if parent.name == "a":
                if "target" in parent.attrs:
                    del parent["target"]

                if "title" in parent.attrs:
                    del parent["title"]

                if "href" in parent.attrs:
                    parent["href"] = "#"

        media = [
            "en/04-retzlaff-2008-01-en/04-retzlaff-2008-01-en-p1.pdf",
            "de/wortspiel.mp3",
            "de/Renate%20Breitig%20Interview.mp3",
            "en/Peadar-Interview.mp3",
            "de/Nunes-Interview-11-04-13.mp3",
            "de/InterviewwithHanneSeitz.mp3"
            ]

        for a in content_box.find_all('a'):
            if "href" not in a.attrs:
                continue
            link = a["href"]
            if link.strip() in media:
                ab_url = self.get_absolute_url(link)
                wb_api_url = self.get_wayback_api_url(ab_url)
                wb_api_resp = requests.get(wb_api_url).json()
                if wb_api_resp["archived_snapshots"] != {}:
                    wb_url = wb_api_resp["archived_snapshots"]["closest"]["url"]
                    if wb_api_resp["archived_snapshots"]["closest"]["status"] == "200":
                        a["href"] = wb_url
                    else:
                        raise Exception("No wayback snapshot found for {0} from {1}".format(ab_url, self.page_url))
                else:
                    raise Exception("No wayback snapshot found for {0} from {1}".format(ab_url, self.page_url))



        body = template.find("body")
        body.append(content_box)
        cc_bottom = self.soup.new_tag("div")
        cc_bottom["class"] = "cc_statement"
        cc_bottom["id"] = "cc_bottom"
        cc_bottom.string = cc_statement
        body.append(cc_bottom)
        return template
