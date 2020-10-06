from bs4 import BeautifulSoup
import requests
import base64
import mimetypes

class parseScenario():
    def __init__(self, url):
        print(url)
        if "Privas" in url:
            self.page_url = "http://research.ucc.ie/scenario/2020/01/EVEN/01/en"
        else:
            self.page_url = url     
        self.page = requests.get(self.page_url).text
        self.soup = BeautifulSoup(self.page, 'html.parser')

    def get_pdf(self):
        #form pdf
        form_data = {}
        form = self.soup.select("div.print > form")[0]
        for child in form.descendants:
            if "name" in child.attrs:
                name = child["name"]
                value = child["value"]
                form_data[name] = value
        response = requests.post(form["action"],data=form_data)
        return response.content

    def get_encoded_pdf(self):
        return base64.b64encode(self.get_pdf()).decode('utf-8')

    def get_encoded_html(self):
        return base64.b64encode(self.get_html().encode('ascii')).decode('utf-8')

    def get_html(self):
        doi = self.soup.select('span[class="doi"] > a')[0].get_text()
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
            
            if "http" in img["src"]:
                img_url = img["src"]
            else: 
                img_url ="{0}/{1}".format(self.page_url.rsplit("/", 1)[0], img["src"])
            image_data = requests.get(img_url).content
            mimetype = mimetypes.guess_type(img_url)[0]
            img['src'] = "data:%s;base64,%s" % (mimetype, base64.b64encode(image_data).decode('utf-8'))
        #print(content_box)
        return content_box
