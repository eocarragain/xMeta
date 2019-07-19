import datetime
from xmler import dict2xml
import pandas as pd 
import re
import csv

class genericJob():
    def __init__(self, path):
        self.schema_version = "4.4.2"
        self.depositor_name = "University College Cork"
        self.depositor_email_address = "cora@ucc.ie"
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        self.path = path
        xl = pd.ExcelFile(self.path)
        self.article_df = xl.parse('Articles')
        self.contributors_df = xl.parse('Contributors')
        self.citations_df = xl.parse('Citations')
        journal_series = xl.parse('Journal').loc[0]
        self.journal_title = journal_series['journal_title']
        self.journal_short_title = journal_series['short_title']
        self.journal_issn = journal_series['journal_issn']
        self.journal_doi = self.get_valid_doi(journal_series['doi'])
        self.journal_url = journal_series['journal_url']
        self.journal_publisher = journal_series['publisher']
        self.reference_distribution_opts = journal_series['reference_distribution_opts']
        self.license_url = journal_series['license_url']
        try:
            issue_series = xl.parse('Issue').loc[0]
            self.issue_doi = self.get_valid_doi(issue_series['doi'])
            self.issue_number = str(issue_series['issue_number'])
            self.issue_url = issue_series['issue_url']        
            self.issue_title = issue_series['journal_title']
            self.issue_editors_keys = issue_series['editors']
            self.publication_date = issue_series['publication_date']
            self.batch_id = self.issue_doi
            self.rights_statement = issue_series['rights_statement']
            self.cora_collection = issue_series['collection'] 
            self.has_issue = True
        except:
            print("WARNING: No issue metadata found, publication date will be set to today")
            now = datetime.datetime.now()
            self.publication_date = pd.Timestamp(now)
            self.batch_id = "{}-{}".format(self.journal_doi, now.strftime("%Y-%m-%d"))
            self.rights_statement = "© the Author(s)"
            self.cora_collection = "" 
            self.has_issue = False
        try:
            volume_series = xl.parse('Volume').loc[0]
            self.volume_doi = self.get_valid_doi(volume_series['doi'])
            self.volume_number = str(volume_series['volume_number'])
            self.volume_url = volume_series['volume_url']
            if self.volume_number:        
                self.has_volume = True
            else:
                self.has_volume = False 
        except:
            print("WARNING: No volume metadata found")
            self.has_volume = False          

    def valid_doi(self, doi):
        doi = self.format_doi(doi)
        pattern = re.compile("^10.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
        if pattern.match(doi):
            return True
        else:
            return False
    
    def valid_ucc_doi(self, doi):
        doi = self.format_doi(doi)
        pattern = re.compile("^10.33178/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
        if pattern.match(doi):
            return True
        else:
            return False

    def get_doi_uri(self, doi):
        doi = self.get_valid_doi(doi)
        return "https://doi.org/{}".format(doi)

    def format_doi(self, doi):
        doi = doi.strip()
        doi = re.sub(r'^https?:\/\/(dx.)?doi.org\/', '', doi)
        return doi

    def get_valid_doi(self, doi, ucc=False):
        doi = self.format_doi(doi)
        
        if ucc == True:
            if self.valid_ucc_doi(doi):
                return doi
            else:
                raise Exception("Invalid UCC DOI: {}".format(doi))
        else:
            if self.valid_doi(doi):
                return doi
            else:
                raise Exception("Invalid DOI: {}".format(doi))

    def get_doi_parts(self, doi):
        doi = self.get_valid_doi(doi)
        doi_parts = doi.split("/")
        return doi_parts

    def get_doi_suffix(self, doi):
        return self.get_doi_parts(doi)[1]

    def get_doi_prefix(self, doi):
        return self.get_doi_parts(doi)[0]

    def get_valid_orcid(self, orcid):
        orcid = orcid.strip()
        pattern = re.compile("^https?://orcid.org/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[X0-9]{1}$", re.IGNORECASE)
        if pattern.match(orcid):
            return orcid
        elif pattern.match("https://orcid.org/{}".format(orcid)):
            return "https://orcid.org/{}".format(orcid)
        else:
            raise Exception("Invalid ORCID: {}".format(orcid))

    def get_pud_date_string(self, timestamp):
        pydate = timestamp.to_pydatetime()
        date_str = pydate.strftime("%Y-%m-%d")
        return date_str

    def get_pub_date_parts(self, date):
        date_str = self.get_pud_date_string(date)
        date_parts_array = date_str.split("-")
        date_parts = {
            "year": date_parts_array[0],
            "month": date_parts_array[1],
            "day": date_parts_array[2]
        }
        return date_parts

class CrossRefJob(genericJob):
    def get_root(self):
        root = {
            "doi_batch": {
                "@attrs": {
                    "version": self.schema_version,
                    "xmlns": "http://www.crossref.org/schema/{}".format(self.schema_version),
                    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                    "xsi:schemaLocation": "http://www.crossref.org/schema/{} http://www.crossref.org/schema/deposit/crossref{}.xsd".format(self.schema_version, self.schema_version)
                }
            }
        }
        return root

    def get_head(self):
        head = {
            "doi_batch_id": self.batch_id,
            "timestamp": self.timestamp,
            "depositor": {
                "depositor_name": self.depositor_name,
                "email_address": self.depositor_email_address
            },
            "registrant": self.depositor_name
        }
        return head

    def get_journal_metadata(self):
        journal = {
            "@attrs": {
                "reference_distribution_opts": self.reference_distribution_opts,
            },
            "full_title": self.journal_title,
            "abbrev_title": self.journal_short_title,
            "issn": self.journal_issn,
            "doi_data": {
                "doi": self.journal_doi,
                "resource": self.journal_url
            }
        }
        return journal

    def get_journal_issue(self):
        journal_issue = {
            "contributors": self.get_contributors(self.issue_editors_keys, "editor"),
            "titles": {
                "title": self.issue_title
            },
            "publication_date": self.get_pub_date(self.publication_date),
            "issue": self.issue_number,
            "doi_data": {
                "doi": self.issue_doi,
                "resource": self.issue_url
            }
        }
        return journal_issue
      
    def get_contributors(self, lookup, role):
        contributors = {}
        keys = lookup.replace(" ", "").split("||")
        if len(keys) == 0:
            return contributors

        for idx, val in enumerate(keys):
            print(val)
            try:
                contributor_df = self.contributors_df.loc[self.contributors_df['id'] == val]
                contributor_df = contributor_df.reset_index().fillna('')
                contributor_series = contributor_df.loc[0]
            except:
                #todo proper error handling
                raise Exception("########### CONTRIB NOT FOUND #######################")


            if role == "author" and idx == 0:
                sequence = "first"
            else:
                sequence = "additional"


            person_name = {
                    "@attrs": {
                        "sequence": sequence,
                        "contributor_role": role
                    },
                    "@name" : "person_name",
                    "given_name": contributor_series['given_name'],
                    "surname": contributor_series['surname']
                }

            
            if contributor_series['primary_affiliation']:
                person_name.update({"primary_affiliation": {"@value": contributor_series['primary_affiliation'], "@name": "affiliation" }})

            if contributor_series['secondary_affiliation']:
                 person_name.update({"secondary_affiliation": {"@value": contributor_series['secondary_affiliation'], "@name": "affiliation" }})
            
            if contributor_series['orcid']:
                orcid = self.get_valid_orcid(contributor_series['orcid'])
                person_name.update({"ORCID": orcid})  
                    

            contributors.update({"person_name-{}-{}-{}".format(idx, val, role): person_name})
        return contributors

    def get_pub_date(self, date, media_type="online"):
        date_parts = self.get_pub_date_parts(date)
        pub_date = {
            "@attrs": {
                "media_type": media_type
            },
            "month": date_parts["month"],
            "day": date_parts["day"],
            "year": date_parts["year"]
        }
        return pub_date

    def get_license(self, start_date):
        versions = ['vor', 'am', 'tdm']
        licenses = {
                "@attrs": {
                    "name": "AccessIndicators",
                    "xmlns": "http://www.crossref.org/AccessIndicators.xsd"
                }
            }
        for version in versions:
            license_dict = {
                "license_ref-{}".format(version): {
                    "@attrs":{
                        "applies_to": version,
                        "start_date": start_date
                    },
                    "@name": "license_ref",
                    "@value": self.license_url
                }
            }
            licenses.update(license_dict)
        return licenses

    def get_citation(self, raw_row, art_doi, idx):
        row = raw_row.fillna('')
        doi_suffix = self.get_doi_suffix(art_doi)
        citation_key = "{}-{}".format(doi_suffix, idx)

        if row["DOI for reference"] and self.valid_doi(row["DOI for reference"]):
            cite_block = {"doi": self.get_valid_doi(row["DOI for reference"])}
        elif row["Complete reference"]:
            cite_block = {"unstructured_citation": row["Complete reference"]}
        else:
            raise Exception("no valid citation")

        cite = {
            "@attrs":{
                "key": citation_key
            },
            "@name": "citation",
        }
        cite.update(cite_block)

        citation = {
            "citation-{}".format(citation_key): cite
        }
        return citation


    def get_citations(self, art_doi):
        #print(self.citations_df.columns)
        citations = {}
        art_citations_df = self.citations_df.loc[self.citations_df['Article DOI '] == art_doi]
        if len(art_citations_df.index) == 0:
            art_citations_df = self.citations_df.loc[self.citations_df['Article DOI '] == self.get_doi_uri(art_doi)]

        if len(art_citations_df.index) == 0:
            #todo proper logging
            print("### WARNING: no citations found for {}".format(art_doi))
            return citations

        art_citations_df = art_citations_df.reset_index().fillna('')    

        for idx, row in art_citations_df.iterrows():
            citation = self.get_citation(row, art_doi, idx + 1) 
            citations.update(citation)
        
        return citations

    def get_abstract(self, abstract, language):       
        el = {
            "@attrs": {
                "xmlns": "http://www.ncbi.nlm.nih.gov/JATS1",
                "xml:lang": language
            },
            "@name": "abstract",
            "p": abstract
        }

        return el

    def get_article(self, raw_row):
        row = raw_row.fillna('')
        titles = {
            "title": row["title"]
        }
        if row["subtitle"]:
            titles["subtitle"] = row["subtitle"]
       
        if row["authors"]: 
            contributors = self.get_contributors(row["authors"], "author")
        
        if row["editors"]:
            editors = self.get_contributors(row["editors"], "editor")
            contributors.update(editors)

        publication_date = self.get_pub_date(self.publication_date)
        pub_date_str = self.get_pud_date_string(self.publication_date)
        doi = self.get_valid_doi(row["doi"])
        print("Processing: {}".format(doi))
        url = row["url"]

        try: 
            language = row["language"]
        except:
            language = "en"

        article_id = "journal_article-{}".format(doi)
        article =  {article_id: {
                "@attrs": {
                    "publication_type": "full_text",
                    "language": language,
                    "reference_distribution_opts": self.reference_distribution_opts,
                },
                "@name": "journal_article",
                "titles" : titles,
                "contributors": contributors,
                "abstract": self.get_abstract(row["abstract"], language),
                "abstract_en": self.get_abstract(row["abstract_translated_to_en"], 'en'),
                "publication_date": publication_date,
                "pages": {
                    "first_page": str(row["first_page"]),
                    "last_page": str(row["last_page"]),
                },
                "program": self.get_license(pub_date_str),
                "doi_data": {
                    "doi": doi,
                    "resource": url 
                },
                "citation_list": self.get_citations(doi)
            } 
        }
        
        if article[article_id]["abstract"]["p"] == "":
            del article[article_id]["abstract"]

        if article[article_id]["abstract_en"]["p"] == "":
            del article[article_id]["abstract_en"]

        #print(article)
        return article

    def get_articles(self):
        articles = {}
        for idx, row in self.article_df.iterrows():
            article = self.get_article(row) 
            articles.update(article)
        return articles

    def get_body(self):
        journal = {}

        journal["journal_metadata"] = self.get_journal_metadata()
        if self.has_issue:
            journal["journal_issue"] = self.get_journal_issue()
        journal.update(self.get_articles())
        body = {"journal" : journal}
        return body

    def generate(self):
        myDict = self.get_root()
        
        myDict["doi_batch"]["head"] = self.get_head()
        myDict["doi_batch"]["body"] = self.get_body()

        #print(myDict)
        #print("~~~~~~~~~~~~#################~~~~~~~~~~~~~~~~~~~~~")
        #print(dict2xml(myDict))
        output_path = self.path.replace(".xlsx", ".xml")
        f = open(output_path, "w", encoding='utf-8')
        f.write(dict2xml(myDict))
        f.close()


class DspaceJob(genericJob):

    def get_article_citation(self, authors, year, title, start_page, end_page, doi):
        #self.journal_title
        #self.volume_number
        #self.issue_number
        no_of_auths = len(authors)
        authors_str = ""
        for idx, author in enumerate(authors):
            initial = "{}.".format(author["given_name"][0])
            name = "{}, {}".format(author["surname"], initial)
            if idx == 0:
                authors_str = name
            elif idx == (no_of_auths - 1):
                authors_str = "{} and {}".format(authors_str, name)
            else:
                authors_str = "{}, {}".format(authors_str, name)

        if self.has_volume:
            vol_issue = "{}({})".format(self.volume_number, self.issue_number)
        else:
            vol_issue = self.issue_number

        pages = "pp. {}-{}.".format(start_page, end_page)
        article_citation_list = [
            authors_str,
            "({})".format(year),
            "'{}',".format(title),
            "{},".format(self.journal_title),
            "{},".format(vol_issue),
            pages,
            "doi: {}".format(doi)
        ]

        article_citation = " ".join(article_citation_list)
        return article_citation

    def get_contributors_as_dicts(self, lookup):
        contributors = []
        keys = lookup.replace(" ", "").split("||")
        if len(keys) == 0:
            return contributors

        for val in keys:
            print(val)
            try:
                contributor_df = self.contributors_df.loc[self.contributors_df['id'] == val]
                contributor_df = contributor_df.reset_index().fillna('')
                contributor_series = contributor_df.loc[0]
            except:
                #todo proper error handling
                raise Exception("########### CONTRIB NOT FOUND #######################")

            primary_affiliation = ""
            if contributor_series['primary_affiliation']:
                primary_affiliation = contributor_series['primary_affiliation']


            contributor = {
                "given_name": contributor_series['given_name'].strip(),
                "surname": contributor_series['surname'].strip(),
                "primary_affiliation": primary_affiliation.strip()
            }

            if contributor_series['email_for_ucc_authors']:
                email = contributor_series['email_for_ucc_authors']
                if '@ucc.ie' in email:
                   contributor['email_for_ucc_authors'] = email
            
            contributors.append(contributor)
        return contributors 
 
    def get_contributors(self, lookup):
        print(lookup)
        contributors_array = self.get_contributors_as_dicts(lookup)
        print("here")
        contributors = ""
        print(contributors_array)
        for idx, contributor in enumerate(contributors_array):
            author_str = "{}, {}".format(contributor["surname"], contributor["given_name"])
            if idx == 0:
                contributors = author_str
            else:
                contributors = "{}||{}".format(contributors, author_str)

        return contributors

    def format_affilation(self, given_name, surname, affiliation):
        author = "{} {}".format(given_name, surname)
        if affiliation:
            author = "{}, {}".format(author, affiliation)
        return author


    def get_pub_date(self, date):
        date_parts = self.get_pub_date_parts(date)
        return date_parts["year"]

    def get_article(self, raw_row):
        row = raw_row.fillna('')
        title = row["title"]

        if row["subtitle"]:
            title = "{}: {}".format(title, row["subtitle"])      

        doi = self.get_valid_doi(row["doi"])
    
        authors = ""
        first_author_str = ""
        internal_email = ""
        if row["authors"]: 
            authors = self.get_contributors(row["authors"])
            first_author = self.get_contributors_as_dicts(row["authors"])[0]
            first_author_str = self.format_affilation(first_author["given_name"], first_author["surname"], first_author["primary_affiliation"])
            if 'email_for_ucc_authors' in first_author:
                internal_email = first_author['email_for_ucc_authors']

        editors = ""
        if row["editors"]:
            editors = self.get_contributors(row["editors"])

        subjects = ""
        if row["keywords"]:
            subjects = row["keywords"].replace("|| ", "||").replace(" ||", "||")

        item_type = row["type"]
        peer_reviewed = row["peer_reviewed"]
        if item_type.lower().strip() == "article":
            if peer_reviewed.lower().strip() == "peer reviewed":
                item_type = "Article (peer-reviewed)"
            else:
                item_type = "Article (non peer-reviewed)"
        
        pub_year = self.get_pub_date(self.publication_date)

        start_page = str(row["first_page"])
        end_page = str(row["last_page"])

        article_citation = self.get_article_citation(
            self.get_contributors_as_dicts(row["authors"]),
            pub_year,
            title,
            start_page,
            end_page,
            doi
        )

        row_dict = {
                'id': '+',
                'dc.identifier.doi': doi,
                'collection': self.cora_collection,
                'dc.contributor.author[]': authors,
                'dc.contributor.editor[en]': editors,
                'dc.title[en]': title,
                'dc.identifier.citation[en]': article_citation,
                'dc.relation.uri[]': row["url"],
                'dc.identifier.endpage[]': end_page,
                'dc.subject[en]': subjects,
                'dc.internal.authorcontactother[en]': first_author_str,
                'dc.internal.IRISemailaddress[en]': internal_email,
                'dc.type[en]': item_type,
                'dc.description.abstract[en]': row["abstract"],
                'dc.identifier.journaltitle[en]': self.journal_title,
                'dc.publisher[en]': self.journal_publisher,
                'dc.identifier.issn[]': self.journal_issn,
                'dc.date.issued[]': pub_year,
                'dc.identifier.issued[]': self.issue_number,
                'dc.identifier.startpage[]': start_page,
                'dc.description.status[en]': peer_reviewed,
                'dc.description.version[en]': "Published Version",
                'dc.format.mimetype[en]': "application/pdf",
                'dc.language.iso[en]': row["language"],
                'dc.internal.availability[en]': "Full text available",
                'dc.rights[en]': self.rights_statement,
                'dc.rights.uri': self.license_url,
                'dc.description.provenance[en]': "Batch upload from published version"
        }

        return row_dict

    def generate(self):
        output_path = self.path.replace(".xlsx", ".csv")
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            # get the fieldnames from the first article dict, to ensure consistency
            test_article = self.get_article(self.article_df.iloc[0])

            fieldnames = list(test_article.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for idx, row in self.article_df.iterrows():
                article = self.get_article(row) 
                writer.writerow(article)



