from bs4 import BeautifulSoup
import requests
import base64
import mimetypes
import roman

class parseScenarioIssue():
    def __init__(self, issue_url):
        print(issue_url)
        self.issue_url = issue_url.strip()   
        req = requests.get(self.issue_url)
        self.issue_page = req.text
        self.soup = BeautifulSoup(self.issue_page, 'html.parser')

    def get_issn(self):
        return "1649-8526"

    def get_volume(self):
        vol = self.soup.select("span.volume")[0].get_text()
        return vol

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
        issue_year["issue"] = parts[0].strip()
        issue_year["year"] = parts[1].strip()

        return issue_year

    def get_article_urls(self):
        articles = {}
        article_links = self.soup.select("div.toctitle > span.doctitle a")
        for article_link in article_links:
            title = article_link.get_text()
            link = article_link['href']
            articles[link] = title
            print(link)

        return articles

            #if exclude_vorwort and "Vorwort" in title:
             #   continue

    def get_issue_galley(self):
        whole_issue = self.soup.find_all("a", string="Whole Issue")[0]
        return whole_issue["href"]


class parseScenario():
    def __init__(self, url):
        print(url)
        self.page_url = url.strip()   
        req = requests.get(self.page_url)
        print(req.status_code)
        self.page = self.get_page(req)
        self.soup = BeautifulSoup(self.page, 'html.parser')
        self.meta_tags = self.get_meta_tags()

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
            if wb_api_resp != {}:
                wb_url = wb_api_resp["archived_snapshots"]["closest"]["url"]
                wb_page_req = requests.get(wb_url)
                if wb_page_req.status_code == 200:
                    self.status_code = 200
                    self.page_url = wb_url
                    return wb_page_req.text
        
        self.status_code = 500
        #raise Exception("Failed to load html for {0}".format(self.page_url))
        return req.text

    def get_wayback_api_url(self, scenario_url):
        return "http://archive.org/wayback/available?url={}".format(scenario_url)


    def get_pdf(self):
        #form pdf
        form_data = {}
        f = self.soup.select("form")
        #print(self.page)
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
                    print(meta_tags[name])
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

    def get_authors(self, fallback_author=''):
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


    # convenience method to parse 
    def get_authors_from_body(self, fallback_author=''):
        #known patterns
        #John Doe/Jane Doe/Jenny Doe
        #John Doe & Jane Doe
        #John Doe and Jane Doe
        #John Doe und Jane Doe
        #John Doe; Jane Doe; Jenny Doe
        #John Doe, Jane Doe, Jenny Doe
        #John Doe, Jane Doe & Jenny Doe
        #John Doe, Jane Doe and Jenny Doe
        authors = []
        #author =   todo soup selector for any element with class docauthor
        #print("~~~~~~~~~{}".format(author))
        if author in bad_names:
            parts = author.split(",")
            author = "{} {}".format(parts[1], parts[0]).strip()

        parts = []
        if "/" in author:
            parts = author.split("/")
        elif ";" in author:
            parts = author.split(";")
        elif "," in author:
            parts = author.split(",")
        else:
            parts = [author]

        for part in parts:
            part = part.replace(" and ", "&")
            part = part.replace("&amp;", "&")
            part = part.replace("und", "&")
            part_parts = part.split("&")
            authors = authors + part_parts

        authors = list(map(str.strip, authors)) 
        authors = list(filter(None, authors))
        if len(authors) == 0:
            if fallback != '':
                authors.append(fallback_author)
        return authors

    def get_abstract(self):
        el = self.soup.select('div.abstract > p')
        if len(el) > 0:
            abstract = el[0].get_text()
            abstract = " ".join(abstract.split()).strip()
        else:
            abstract = ""
        return abstract

    def get_language(self):
        lang = url.split("/")[-1]
        if lang in ['en', 'de']:
            return lang
        else:
            return 'en'

    def get_citations(self):
        content_box = self.soup.select("div.content")[0]
        citations = []
        heading = content_box.find_all(['a', 'div', 'p'], string="Bibliography")
        if len(heading) > 0:
            #print(heading)
            first_entry = heading[0].find_next("p")
            #print(first_entry)
            citations.append(first_entry.get_text())
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

    #keywords
    #type

    def get_encoded_pdf(self):
        return base64.b64encode(self.get_pdf()).decode('utf-8')

    def get_encoded_html(self):
        return base64.b64encode(self.get_html().encode('ascii')).decode('utf-8')

    def get_html(self):
        doi = self.soup.select('span[class="doi"] > a')
        if len(doi) > 0:
            doi = doi[0].get_text()
        vol = self.soup.select('span[class="volume"]')[0].get_text()
        issue = self.soup.select('span[class="issue"]')[0].get_text()
        year = self.soup.select('span[class="date"]')[0].get_text().replace("Year", "").strip()
        citation_str = "{0}, {1}, {2}".format(vol, issue, year)
        if len(doi) > 0:
            citation_str = "{0}, doi:{1}".format(citation_str, doi)
        citation = self.soup.new_tag("div")
        citation.string = citation_str
        metadata = self.soup.select('div[class="metadata"]')[0]
        metadata.append(citation)
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
            if "scenario-back.png" in img["src"]:
                img.replace_with("[Back]")
                continue    
            
            if img["src"].startswith("http"):
                img_url = img["src"]
            elif img["src"].startswith("/web/"):
                img_url ="{0}/{1}".format("https://web.archive.org", img["src"]) 
            else:
                img_url ="{0}/{1}".format(self.page_url.rsplit("/", 1)[0], img["src"])
            print("########################## {0}".format(img_url))
            # horrible hack for broken image
            if img_url == "http://research.ucc.ie/journals/scenario/2019/02/PrivasBreaute/10/en/media/image6.png":
                continue
            image_req = requests.get(img_url)
            if image_req.status_code != 200:
                raise Exception("Unable to download image {0} for page {1}".format(img_url, self.page_url))
            image_data = image_req.content

            mimetype = mimetypes.guess_type(img_url)[0]
            img['src'] = "data:%s;base64,%s" % (mimetype, base64.b64encode(image_data).decode('utf-8'))
        #print(content_box)
        return content_box
