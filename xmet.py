import datetime
from xmler import dict2xml
import pandas as pd 
import re
import csv
import roman
import scenario

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
        journal_series = xl.parse('Journal').loc[0].fillna('')
        self.journal_title = journal_series['journal_title']
        self.journal_short_title = journal_series['short_title']
        self.journal_issn = journal_series['journal_issn']
        self.journal_doi = self.get_valid_doi(journal_series['doi'])
        self.journal_url = journal_series['journal_url']
        self.journal_publisher = journal_series['publisher']
        self.reference_distribution_opts = journal_series['reference_distribution_opts']
        self.license_url = journal_series['license_url']
        try:
            issue_series = xl.parse('Issue').loc[0].fillna('')
            self.issue_doi = self.get_valid_doi(issue_series['doi'])
            self.issue_number = str(issue_series['issue_number'])
            self.issue_url = issue_series['issue_url']
            if issue_series['issue_title']: 
                self.issue_title = issue_series['issue_title']
            else:
                self.issue_title = ""
            self.issue_editors_keys = issue_series['editors']
            self.publication_date = issue_series['publication_date']
            self.batch_id = self.issue_doi
            self.rights_statement = issue_series['rights_statement']
            self.cora_collection = issue_series['collection']
            self.issue_languages = issue_series['languages']
            self.has_issue = True
        except:
            print("WARNING: No issue metadata found, publication date will be set to today")
            now = datetime.datetime.now()
            self.publication_date = pd.Timestamp(now)
            self.batch_id = "{}-{}".format(self.journal_doi, now.strftime("%Y-%m-%d"))
            self.rights_statement = "© the Author(s)"
            self.cora_collection = ""
            self.issue_languages = "en" 
            self.has_issue = False
        try:
            volume_series = xl.parse('Volume').loc[0].fillna('')
            if volume_series['doi']:
                self.volume_doi = self.get_valid_doi(volume_series['doi'])
            else:
                self.volume_doi = ""
            self.volume_number = volume_series['volume_number']
            self.volume_url = volume_series['volume_url']
            if self.volume_number:        
                self.has_volume = True
            else:
                self.has_volume = False 
        except:
            print("WARNING: No volume metadata found")
            self.has_volume = False
        self.publication_type = self.get_publication_type()

    def get_publication_type(self):
        return "journal"          

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
        #print(doi)
        
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

    def get_pub_date_string(self, timestamp):
        pydate = timestamp.to_pydatetime()
        date_str = pydate.strftime("%Y-%m-%d")
        return date_str

    def get_pub_date_parts(self, date):
        date_str = self.get_pub_date_string(date)
        date_parts_array = date_str.split("-")
        date_parts = {
            "year": date_parts_array[0],
            "month": date_parts_array[1],
            "day": date_parts_array[2]
        }
        return date_parts

    def get_journal_volume(self):
        volume_metadata = {}
        if self.has_volume == False:
            return volume_metadata
        
        if self.volume_number.strip() != "":
            volume_metadata["volume"] = self.volume_number

        if self.volume_doi and self.volume_url:
            volume_metadata["doi_data"] = {
                "doi": self.volume_doi,
                "resource": self.volume_url
            }
        return volume_metadata

    def get_citations(self, art_doi):
        citations = {}
        article_doi_series = self.citations_df['Article DOI '].str.strip()
        art_citations_df = self.citations_df.loc[article_doi_series == art_doi]
        if len(art_citations_df.index) == 0:
            art_citations_df = self.citations_df.loc[article_doi_series == self.get_doi_uri(art_doi)]

        if len(art_citations_df.index) == 0:
            #todo proper logging
            print("### WARNING: no citations found for {}".format(art_doi))
            return citations

        art_citations_df = art_citations_df.reset_index().fillna('')    

        for idx, row in art_citations_df.iterrows():
            citation = self.get_citation(row, art_doi, idx + 1) 
            citations.update(citation)
        
        return citations

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

    def get_contributors(self, lookup, role):
        contributors = {}
        if lookup == "":
            return contributors
        keys = lookup.replace(" ", "").split("||")
        if len(keys) == 0:
            return contributors

        for idx, val in enumerate(keys):
            try:
                contributor_df = self.contributors_df.loc[self.contributors_df['id'] == val]
                contributor_df = contributor_df.reset_index().fillna('')
                contributor_series = contributor_df.loc[0]
            except:
                #todo proper error handling
                raise Exception("########### CONTRIB NOT FOUND: {0} #######################".format(val))


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
        if self.publication_type == "conference_proceedings":
            element_name = "conference_paper" 
        else:
            element_name = "journal_article" 

        contributors = {}
        row = raw_row.fillna('')
        titles = {
            "title": row["title"].strip()
        }
        if row["subtitle"]:
            titles["subtitle"] = row["subtitle"]
       
        if row["authors"]: 
            contributors = self.get_contributors(row["authors"], "author")
        
        if row["editors"]:
            editors = self.get_contributors(row["editors"], "editor")
            contributors.update(editors)

        publication_date = self.get_pub_date(self.publication_date)
        pub_date_str = self.get_pub_date_string(self.publication_date)
        doi = self.get_valid_doi(row["doi"])
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
                "@name": element_name,
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

        return article

    def get_articles(self):
        articles = {}
        for idx, row in self.article_df.iterrows():
            if 'mint_doi' in row:
                if row['mint_doi'] == False:
                    continue

            article = self.get_article(row) 
            articles.update(article)
        return articles

    def generate(self):
        myDict = self.get_root()
        
        myDict["doi_batch"]["head"] = self.get_head()
        myDict["doi_batch"]["body"] = self.get_body()

        

        output_path = self.path.replace(".xlsx", ".xml")
        f = open(output_path, "w", encoding='utf-8')
        f.write(dict2xml(myDict))
        #f.write(str(myDict))
        f.close()



class CrossRefJournalJob(CrossRefJob):

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
            "titles": {},
            "publication_date": self.get_pub_date(self.publication_date),
            "journal_volume": {},
            "issue": self.issue_number,
            "doi_data": {
                "doi": self.issue_doi,
                "resource": self.issue_url
            }
        }

        if len(self.issue_title.strip()) > 0:
            journal_issue["titles"] = {
                "title": self.issue_title
            }
        else:
            del journal_issue["titles"]
        
        volume_metadata = self.get_journal_volume()
        if len(volume_metadata.keys()) > 0:
            journal_issue["journal_volume"] = self.get_journal_volume()
        else:
            del journal_issue["journal_volume"]

        return journal_issue
      

    def get_body(self):
        journal = {}

        journal["journal_metadata"] = self.get_journal_metadata()
        if self.has_issue:
            journal["journal_issue"] = self.get_journal_issue()
        journal.update(self.get_articles())
        body = {"journal" : journal}
        return body

class CrossRefConferenceJob(CrossRefJob):
    def get_publication_type(self):
        return "conference_proceedings"     

    def get_proceedings_metadata(self):
        publication_date = self.get_pub_date(self.publication_date)
        proceedings_metadata = {
            "@attrs": {
                "reference_distribution_opts": self.reference_distribution_opts,
            },
            "proceedings_title": self.issue_title,
        }
        
        publishers = self.journal_publisher.strip().split("||")
        i = 0
        for publisher in publishers:
            proceedings_metadata["pubisher{}".format(i)] = {
                "@name": "publisher",
                "publisher_name": publisher.strip(),
            }
            i += 1

        proceedings_metadata["publication_date"] = publication_date
        proceedings_metadata["doi_data"] = {
                "doi": self.issue_doi,
                "resource": self.issue_url
            }
        return proceedings_metadata

    def get_event_metadata(self):
        event_metadata = {
            "conference_name": self.issue_title
        }

        sponsors = self.journal_publisher.strip().split("||")
        i = 0
        for sponsor in sponsors:
            event_metadata["conference_sponsor{}".format(i)] = {
                "@name": "conference_sponsor",
                "@value": sponsor.strip()
            }
            i += 1
        
        event_year = self.issue_number
        if len(event_year) == 4 and event_year.isnumeric():
            event_metadata["conference_date"] = { "@attrs": {
                    "start_year": event_year,
                    "end_year": event_year
                }
            }
        print(event_metadata)        
        return event_metadata
      

    def get_body(self):
        conference = {}

        #add editors as contributors
        conference["contributors"] = self.get_contributors(self.issue_editors_keys, "editor")
        conference["event_metadata"] = self.get_event_metadata()
        
        conference["proceedings_metadata"] = self.get_proceedings_metadata()

        conference.update(self.get_articles())
        body = {"conference" : conference}
        return body


class DspaceJob(genericJob):

    def get_initials(self, all_given_names):
        given_names_array = all_given_names.split(" ")
        initials = ""
        for idx, given_name in enumerate(given_names_array):
            #print(given_name)
            if idx == 0:
                initials = "{}.".format(given_name[0])
            else:
                initials = "{} {}.".format(initials, given_name[0])
        return initials

    def get_article_citation(self, authors, year, title, start_page, end_page, doi):
        #self.journal_title
        #self.volume_number
        #self.issue_number
        no_of_auths = len(authors)
        authors_str = ""
        for idx, author in enumerate(authors):
            initials = self.get_initials(author["given_name"])
            name = "{}, {}".format(author["surname"], initials)
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
        if len(end_page) > 0:
            pages = "pp. {}-{}.".format(start_page, end_page)
        else:
            pages = "pp. {}.".format (start_page)
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
        if lookup == '':
            return contributors
        keys = lookup.replace(" ", "").split("||")
        if len(keys) == 0:
            return contributors

        for val in keys:
            try:
                contributor_df = self.contributors_df.loc[self.contributors_df['id'] == val]
                contributor_df = contributor_df.reset_index().fillna('')
                contributor_series = contributor_df.loc[0]
            except:
                #todo proper error handling
                raise Exception("########### CONTRIB NOT FOUND: {0} #######################".format(val))

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
        contributors_array = self.get_contributors_as_dicts(lookup)
        contributors = ""
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
        title = row["title"].strip()

        if row["subtitle"]:
            title = "{}: {}".format(title, row["subtitle"]) 

        title = title.replace("&", "and")     

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
        type_norm = item_type.lower().strip()
        pr_norm = peer_reviewed.lower().strip()
        if type_norm in ["article", "foreward", "interview"]:
            if pr_norm == "peer reviewed":
                item_type = "Article (peer-reviewed)"
            else:
                item_type = "Article (non peer-reviewed)"
        elif type_norm  in ["review", "film review", "book review"]:
                item_type = "Review"    
        elif type_norm  in ["conference presentation", "conference report"]:
            item_type = "Conference item"
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

        #add trailing fullstops to abstracts
        abstract = row["abstract"].strip()
        if len(abstract) > 0:
            if abstract[-1:].isalpha():
                abstract = "{}.".format(abstract)

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
                'dc.description.abstract[en]': abstract,
                'dc.identifier.journaltitle[en]': self.journal_title,
                'dc.identifier.journalabbrev[en]': self.journal_short_title,
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

        languages = self.issue_languages.split("||")
        for language in languages:
            language = language.strip()
            if language != "en":
                column_heading = "keywords_{}".format(language)
                if column_heading in row:
                    keywords_lang = row[column_heading].replace("|| ", "||").replace(" ||", "||")
                    row_dict["dc.subject[{}]".format(language)] = keywords_lang
        
        row_dict = self.clean_row_dict(row_dict)

        return row_dict

    def clean_row_dict(self, row_dict):
        # this method is a place for sub-classes to make final modifications 
        return row_dict

    def generate(self):
        output_path = self.path.replace(".xlsx", ".csv")
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            # get the fieldnames from the first article dict, to ensure consistency
            test_article = self.get_article(self.article_df.iloc[0])

            fieldnames = list(test_article.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for idx, row in self.article_df[::-1].iterrows():
                if 'mint_doi' in row:
                    if row['mint_doi'] == False:
                        continue
                article = self.get_article(row) 
                writer.writerow(article)

class DspaceConferenceJob(DspaceJob):
    def get_article_citation(self, authors, year, title, start_page, end_page, doi):
        no_of_auths = len(authors)
        authors_str = ""
        for idx, author in enumerate(authors):
            initials = self.get_initials(author["given_name"])
            name = "{}, {}".format(author["surname"], initials)
            if idx == 0:
                authors_str = name
            elif idx == (no_of_auths - 1):
                authors_str = "{} and {}".format(authors_str, name)
            else:
                authors_str = "{}, {}".format(authors_str, name)

        if len(end_page) > 0:
            pages = "pp. {}-{}.".format(start_page, end_page)
        else:
            pages = "pp. {}.".format (start_page)
        article_citation_list = [
            authors_str,
            "({})".format(self.issue_number),
            "'{}',".format(title),
            "{},".format(self.issue_title),
            pages,
            "doi: {}".format(doi)
        ]

        article_citation = " ".join(article_citation_list)
        return article_citation

    def clean_row_dict(self, row_dict):
        row_dict = row_dict
        del row_dict['dc.identifier.issued[]']
        del row_dict['dc.identifier.journalabbrev[en]']
        del row_dict['dc.identifier.journaltitle[en]']
        
        
        row_dict['dc.date.issued[]'] = self.issue_number
        # this method is a place for sub-classes to make final modifications 
        return row_dict



class OjsJob(genericJob):
    def get_contributors(self, lookup, role):
        if lookup == '':
            return {}
        contributors = {
            "@attrs": {
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://pkp.sfu.ca native.xsd"
            },
        }
        keys = lookup.replace(" ", "").split("||")
        if len(keys) == 0:
            return contributors

        for idx, val in enumerate(keys):
            try:
                contributor_df = self.contributors_df.loc[self.contributors_df['id'] == val]
                contributor_df = contributor_df.reset_index().fillna('')
                contributor_series = contributor_df.loc[0]
            except:
                #todo proper error handling
                raise Exception("########### CONTRIB NOT FOUND: {0} #######################".format(val))


            if role == "author" and idx == 0:
                sequence = "first"
            else:
                sequence = "additional"


            person_name = {
                    "@attrs": {
                        "include_in_browse": "true",
                        "user_group_ref": "Author",
                        "seq": "1",
                        "id": "1"
                    },
                    "@name" : "author",
                    "givenname": contributor_series['given_name'],
                    "familyname": contributor_series['surname'],
                    "affiliation": "",
                    "email": "",
                    "orcid": "",
                    "biography": ""
                }

            if contributor_series['primary_affiliation']:
                person_name["affiliation"] = contributor_series['primary_affiliation']

            if contributor_series['email_for_ucc_authors']:
                person_name["email"] = contributor_series['email_for_ucc_authors']
                        
            if contributor_series['orcid']:
                orcid = self.get_valid_orcid(contributor_series['orcid'])
                person_name["orcid"] = orcid  
                    

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


    def get_citation(self, raw_row, art_doi, idx):
        row = raw_row.fillna('')
        
        doi_suffix = self.get_doi_suffix(art_doi)
        citation_key = "{}-{}".format(doi_suffix, idx)

        cite = {
            "@value": row["Complete reference"],
            "@name": "citation",
        }

        citation = {
            "citation-{}".format(citation_key): cite
        }
        #print(citation)
        return citation


    def get_submission_file(self, type, id, enc_data, filename_base, lang="en"):
        filename = "{0}_{1}_{2}.{3}".format(filename_base, type, lang, type)
        if type == "html":
            filetype = "text/html"
        elif type == "docx":
            filetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif type == "xml":
            filetype = "application/xml"
        else:
            filetype = "application/pdf"

        sub = {
            "@attrs": {
                    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                    "stage": "production_ready",
                    "id": id,
                    "xsi:schemaLocation": "http://pkp.sfu.ca native.xsd"
            },
            "@name": "submission_file",
            "revision": {
                "@attrs": {
                    "number": "1",
                    "genre":"Article Text",
                    "filename": filename,
                    "filetype": filetype,
                    "viewable": "true",
                    "date_uploaded": datetime.datetime.now().strftime("%Y-%m-%d"), 
                    "date_modified": datetime.datetime.now().strftime("%Y-%m-%d"), 
                    "uploader": "admin"
                },
                "name": "admin, {0}".format(filename),
                "embed": {
                    "@attrs": {
                        "encoding": "base64",
                    },    
                    "@value": enc_data #"YW0NZW5kb2JqDXN0YXJ0eHJlZg0KMTE2DQolJUVPRg0K"#
                }
            }
        }
        return sub

    def get_locale(self, lang):
        if lang == "de":
            locale = "de_DE"
        else:
            locale = "en_US"
        return locale

    def get_galley(self, type, id, lang="en"):
        if type == "html":
            name = "HTML"
            if lang == "en":
                seq = "1"
                url_path = "html-en"
            else:
                seq = "3"
                url_path = "html-de"
        else:
            name = "PDF"
            if lang == "en":
                seq = "0"
                url_path = "pdf-en"
            else:
                seq = "2"
                url_path = "pdf-de"
        locale = self.get_locale(lang)

        galley = {
            "@attrs": {
                    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                    "url_path": url_path,
                    "approved":"true",
                    "xsi:schemaLocation": "http://pkp.sfu.ca native.xsd"
                    
            },
            "@name": "article_galley",
            "name": {
                "@attrs": {
                    "locale": locale
                },
                "@value":name
            },
            "seq": seq,
            "submission_file_ref": {
                "@attrs": {
                    "id": id,
                    "revision":"1"
                },
            } 
        }
        return galley


    def get_keywords(self, raw_row, column_heading, language):
        row = raw_row.fillna('')
        kwords = row[column_heading].replace("|| ", "||").replace(" ||", "||").split("||")
        locale = self.get_locale(language)
        keywords = {
                    "@attrs": {
                        "locale": locale
                    }
                }
        kword_count = 0
        for kword in kwords:
            keywords["kword{0}".format(kword_count)] = {"@name": "keyword", "@value":kword.strip()}
        return keywords
            
    def get_articles(self):
        articles = {
            "@attrs": {
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://pkp.sfu.ca native.xsd"
            }
        }
        for idx, row in self.article_df.iterrows():
            article = self.get_article(row) 
            articles.update(article)
        return articles
 
    def get_pub_year(self, date):
        date_parts = self.get_pub_date_parts(date)
        return date_parts["year"]

    def is_int(self, val):
        try: 
            int(val)
            return True
        except ValueError:
            return False   

    def get_valid_vol_number(self, vol):
        if self.is_int(vol):
            return vol
        elif self.is_int(roman.fromRoman(vol)):
            return str(roman.fromRoman(vol))
        else:
            return "0"


    def get_issue_title_dict(self, title, locale):
        block = {
                    "@attrs": {
                        "locale" : locale
                    },
                    "@name":"title",
                    "@value": title
                }

        return block

    def get_issue_identification(self):
        num = self.issue_number
        year = self.get_pub_year(self.publication_date)
        issue_identification = {
                "volume": "",
                "number": num,
                "year": year,
                "title_en": "",
                "title_de": "" 
            }

        volume_metadata = self.get_journal_volume()
        print(volume_metadata)
        vol_roman = False
        if len(volume_metadata.keys()) > 0:
            vol = self.get_valid_vol_number(self.get_journal_volume()["volume"])
            if vol != "0":
                issue_identification["volume"] = vol
                vol_roman = str(roman.toRoman(int(vol)))
            else:
                del issue_identification["volume"]
        else:
            del issue_identification["volume"]

        if len(self.issue_title.strip()) > 0:
            issue_identification["title"] = self.issue_title
            del issue_identification["title_en"]
            del issue_identification["title_de"]
        else:
            if vol_roman:
                title_en = "Volume {}, Issue {} ({})".format(vol_roman, num, year)
                title_de = "Jahrgang {}, Ausgabe {} ({})".format(vol_roman, num, year)
            else:
                title_en = "Issue {} ({})".format(num, year)
                title_de = "Ausgabe {} ({})".format(num, year) 

            issue_identification["title_en"] = self.get_issue_title_dict(title_en, 'en_US')
            issue_identification["title_de"] = self.get_issue_title_dict(title_de, 'de_DE')
        return issue_identification

    def get_path_from_doi(self, doi):
        return doi.split("/")[1].replace(".", "-")


    #def get_sections(self, sections_data):
    #    sections = {}
    #    return sections

    def get_root(self):
        root = {
            "issues": {
                "@attrs": {
                    "xmlns": "http://pkp.sfu.ca",
                    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                    "xsi:schemaLocation": "http://pkp.sfu.ca native.xsd"
                }
            }
        }
        return root

    def tree_traverse(self, tree):
        for k, v  in tree.items():
            if str(type(v)) == "<class 'int'>":
                print("{} -- {}".format(k, v))
            elif isinstance(v, dict):
                found = self.tree_traverse(v) 
                if found is not None:  # check if recursive call found it
                    #print(found)
                    return found

    def generate(self):
        myDict = self.get_journal_issue()

        output_path = self.path.replace(".xlsx", "_ojs.xml")
        f = open(output_path, "w", encoding='utf-8')
        #print(myDict["issue"]["date_published"])
        found = self.tree_traverse(myDict)
        f.write(dict2xml(myDict))
        f.close()

    def write_art(self, article):
        output_path = self.path.replace(".xlsx", "_ojs_art.xml")
        f = open(output_path, "w", encoding='utf-8')
        f.write(dict2xml(article))
        f.close()

    def get_journal_issue(self):
        issue_obj = self.get_issue()
        doi_path = self.get_path_from_doi(self.issue_doi) 

        journal_issue = {
            "issue": {
                "@attrs": {
                    "xmlns": "http://pkp.sfu.ca",
                    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                    "published":"1",
                    "current": "0",
                    "access_status": "1",
                    "url_path": doi_path,
                    "xsi:schemaLocation": "http://pkp.sfu.ca native.xsd"
                },
                "@name": "issue",
                "id":{
                    "@attrs": {"type":"internal", "advice":"ignore"},
                    "@value": "1"
                },
                "doi":{
                    "@attrs": {"type":"doi", "advice":"update"},
                    "@name": "id",
                    "@value": self.issue_doi
                },
                "description": "",
                "issue_identification": self.get_issue_identification(),
                "date_published": self.get_pub_date_string(self.publication_date), 
                "last_modified": datetime.datetime.now().strftime("%Y-%m-%d"),
                "sections": self.get_sections(issue_obj.get_sections_as_dict()),
                "covers": {},
                "issue_galleys": {},
                "articles": self.get_articles()    
            }
        }

        issue_galleys = {}
        if issue_obj.get_issue_galley_path() != "":
            issue_galleys = {
                    "@attrs": {
                        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                        "xsi:schemaLocation": "http://pkp.sfu.ca native.xsd"
                    },
                    "issue_galley":{
                        "label": "Whole Issue",
                        "issue_file":{
                            "file_name": "issue_galley.pdf",
                            "file_type": "application/pdf",
                            "file_size": '5000',
                            "content_type": "1",
                            "original_file_name": "issue_galley.pdf",
                            "date_uploaded": "2020-10-04",
                            "date_modified": "2020-10-04",
                            "embed": {
                                "@attrs" : {
                                    "encoding": "base64"
                                },
                                "@value" : issue_obj.get_encoded_issue_galley()
                            }       
                        }
                    }
                }
            journal_issue["issue"]["issue_galleys"] = issue_galleys
        else:
            del journal_issue["issue"]["issue_galleys"]

        issue_cover = {}
        if issue_obj.issue_cover_path != "":
            issue_cover = {
                "cover": {
                    "cover_image": issue_obj.get_issue_cover_filename(),
                    "cover_image_alt_text": "Issue Cover",
                    "embed": {
                        "@attrs" : {
                            "encoding": "base64"
                        },
                        "@value" : issue_obj.get_encoded_issue_cover()
                    }
                }
            }
            journal_issue["issue"]["covers"] = issue_cover
        else:
            del journal_issue["issue"]["covers"]

        return journal_issue

    def get_article(self, raw_row):
        row = raw_row.fillna('')
        contributors = {}
        titles = {
            "title": row["title"].strip()
        }
        if row["subtitle"]:
            titles["subtitle"] = row["subtitle"]
       
        if row["authors"]: 
            contributors = self.get_contributors(row["authors"], "author")
        
        if row["editors"]:
            editors = self.get_contributors(row["editors"], "editor")
            contributors.update(editors)

        publication_date = self.get_pub_date(self.publication_date)
        pub_date_str = self.get_pub_date_string(self.publication_date)
        doi = self.get_valid_doi(row["doi"])
        url_path = self.get_path_from_doi(doi) 
        url = row["url"].strip()

        #issue_url = url.rsplit("/", 3)[0]
        issue = self.get_issue() # scenario.parseScenarioIssue(issue_url)

        toc = issue.get_articles_from_toc()
        if url.lower() in toc:
            toc_row = toc[url.lower()]
        else:
            toc_row = {}
        toc_row_de = {}

        # article url patter consistent for 
        # both scenario and boolean
        url_parts = url.split("/")
        art_no = url_parts[-2]
        issue_no = url_parts[-4]
        issue_year = url_parts[-5]

        filename_base = "{}-{}-{}".format(issue_year, issue_no, art_no)

        title = row["title"].strip()
        abstract = row["abstract"]
        title_de = ""
        abstract_de = ""

        # only applies to scenario but does no harm for boolean     
        secondary_language = False
        secondary_language_url = ""
        if url.endswith("en"):
            language = "en"
            de_url = url[:-2] + "de"
            de_url_lower = de_url.lower()
            if "/foreword/" in url.lower():
                de_url_lower = de_url_lower.replace("/foreword/", "/vorwort/")
            if de_url_lower in toc.keys():
                de_article_from_toc = toc[de_url_lower]
                de_url = de_article_from_toc["url"]
                toc_row_de = toc[de_url_lower]
                title_de = toc_row_de["title"]
                secondary_language_url = de_url
                scen_de = scenario.parseScenario(secondary_language_url)
                abstract_de = scen_de.get_abstract()
                
                secondary_language = True
        else:
            language = "de"
            title_de = title
            abstract_de = abstract
    
        if 'section' in toc_row:
            toc_section = toc_row['section']
        else:
            toc_section = "article"
        section_ref = issue.get_section_ref(toc_section, title)
        
        article_id = "journal_article-{}".format(doi)
        article_no = self.get_article_no(doi) #re.sub(r"\D", "", doi.split("/")[1])
        article_seq = str(int(art_no)) # doi.split("/")[1].split(".")[-1]

        pages = str(row["first_page"])
        if len(str(row["last_page"]).strip()) > 0:
            pages = "{0}-{1}".format(row["first_page"], row["last_page"])

        article =  {
            article_id: {
                "@attrs": {
                    #"xmlns": "http://pkp.sfu.ca",
                    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                    "date_submitted": pub_date_str, 
                    "status": "3",
                    "submission_progress":"0",
                    "current_publication_id": article_no,
                    "stage":"production",
                    "xsi:schemaLocation": "http://pkp.sfu.ca native.xsd"
                },
                "@name": "article",
                "id":{
                    "@attrs": {"type":"internal", "advice":"ignore"},
                    "@value": article_no
                },
                "pdf_file_en": {},
                "html_file_en": {},
                "docx_file_en": {},
                "pdf_file_de": {},
                "html_file_de": {},
                "docx_file_de": {},
                "publication": {
                    "@attrs": {
                        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                        "locale":"en_US",
                        "version": "1",
                        "status": "3",
                        #"primary_contact_id"
                        "url_path":url_path,
                        "seq":article_seq,
                        "date_published": pub_date_str,
                        "section_ref": section_ref,
                        #"access_status"
                        "xsi:schemaLocation": "http://pkp.sfu.ca native.xsd"
                    },
                    "id":{
                        "@attrs": {"type":"internal", "advice":"ignore"},
                        "@value": article_no
                    },
                    "doi":{
                        "@attrs": {"type":"doi", "advice":"update"},
                        "@name": "id",
                        "@value": doi
                    },
                    "title" : {
                        "@attrs": {
                            "locale": 'en_US'
                        },
                        "@value": title
                    },
                    "title_de" : {
                        "@attrs": {
                            "locale": 'de_DE'
                        },
                        "@name": "title",
                        "@value":title_de.strip()
                    },
                    #prefix
                    "subtitle":"",
                    "abstract": {
                        "@attrs": {
                            "locale": 'en_US'
                        },
                        "@value":abstract
                    },
                    "abstract_de" : {
                        "@attrs": {
                            "locale": 'de_DE'
                        },
                        "@name": "abstract",
                        "@value":abstract_de
                    },
                    #rights
                    "licenseUrl": "http://creativecommons.org/licenses/by-nc-nd/4.0",
                    "copyrightHolder": "the author(s)",
                    "copyrightYear": self.get_pub_year(self.publication_date),
                    "keywords": {},
                    "authors": self.get_contributors(row["authors"], "author"),
                    "pdf_galley_en": {},
                    "html_galley_en": {},
                    "pdf_galley_de": {},
                    "html_galley_de": {},
                    #"issue_identification": self.get_issue_identification(),
                    "pages": pages,   
                    #covers
                    "citations": self.get_citations(row['doi'])
                }
            } 
        }

        if row["subtitle"]:
            article[article_id]["publication"]["subtitle"] = row["subtitle"]

        keywords = {}
        if len(row["keywords"]) > 0:
            keywords = self.get_keywords(row, "keywords", 'en')
        elif len(row["keywords_de"]) > 0:
            keywords = self.get_keywords(row, "keywords_de", 'de')
            languages = self.issue_languages.split("||")

                            
        if len(keywords) > 0 :
            article[article_id]["publication"]["keywords"] = keywords
        else:
            del article[article_id]["publication"]["keywords"]

        # check class
        #scen = scenario.parseScenario(row["url"])
        art_obj = self.get_article_obj(row["url"])

        mint_doi = art_obj.has_doi()
        if mint_doi == False:
            del article[article_id]["publication"]["doi"]

        pdf_b64 = art_obj.get_encoded_pdf()
        pdf_id = str(int(article_no) + 100) # todo
        article[article_id]["pdf_file_{0}".format(language)] = self.get_submission_file("pdf", pdf_id, pdf_b64, filename_base, language)
        article[article_id]["publication"]["pdf_galley_{0}".format(language)] = self.get_galley("pdf", pdf_id, language)
        
        html_b64 = art_obj.get_encoded_html()
        html_id = str(int(article_no) + 200) # todo
        article[article_id]["html_file_{0}".format(language)] = self.get_submission_file("html", html_id, html_b64, filename_base, language)
        article[article_id]["publication"]["html_galley_{0}".format(language)] = self.get_galley("html", html_id, language)

        # submission file only for docx
        docx_b64 = art_obj.get_encoded_docx()
        docx_ext = art_obj.docx_ext
        docx_id = str(int(article_no) + 300) # todo 
        article[article_id]["docx_file_{0}".format(language)] = self.get_submission_file(docx_ext, docx_id, docx_b64, filename_base, language)


        if secondary_language == True:
            #scen = scenario.parseScenario(secondary_language_url)
            art_obj_de = self.get_article_obj(secondary_language_url)
            pdf_b64 = art_obj_de.get_encoded_pdf()
            pdf_id = str(int(article_no) + 1000) # todo
            other_language = "de"
            article[article_id]["pdf_file_{0}".format(other_language)] = self.get_submission_file("pdf", pdf_id, pdf_b64, filename_base, other_language)
            article[article_id]["publication"]["pdf_galley_{0}".format(other_language)] = self.get_galley("pdf", pdf_id, other_language)
            
            html_b64 = art_obj_de.get_encoded_html()
            html_id = str(int(article_no) + 2000) # todo
            article[article_id]["html_file_{0}".format(other_language)] = self.get_submission_file("html", html_id, html_b64, filename_base, other_language)
            article[article_id]["publication"]["html_galley_{0}".format(other_language)] = self.get_galley("html", html_id, other_language)

            # submission file only for docx
            docx_b64 = art_obj_de.get_encoded_docx()
            docx_ext = art_obj_de.docx_ext
            docx_id = str(int(article_no) + 3000) # todo
            article[article_id]["docx_file_{0}".format(other_language)] = self.get_submission_file(docx_ext, docx_id, docx_b64, filename_base, other_language)

        if language == "en":
            if secondary_language == False:
                del article[article_id]["pdf_file_de"]
                del article[article_id]["publication"]["pdf_galley_de"]
                del article[article_id]["html_file_de"]
                del article[article_id]["publication"]["html_galley_de"]
                del article[article_id]["docx_file_de"]
        else:
            del article[article_id]["pdf_file_en"]
            del article[article_id]["publication"]["pdf_galley_en"]
            del article[article_id]["html_file_en"]
            del article[article_id]["publication"]["html_galley_en"]
            del article[article_id]["docx_file_en"]            

        if art_obj.status_code != 200:
            del article[article_id]["html_file_en"]
            del article[article_id]["publication"]["html_galley_en"]

        if secondary_language == True:
            if art_obj_de.status_code != 200:
                del article[article_id]["html_file_de"]
                del article[article_id]["publication"]["html_galley_de"]                        

        return article

    def get_sections(self, sections_data):
        sections = {}
        for data in sections_data:
            ref = data["ref"]
            if str(data["policy"]) == 'nan':
                policy = ""
            else:
                policy = data["policy"]
            
            if 'title_de' in data:
                title_de = data['title_de']
                if str(title_de) == 'nan' or len(str(title_de)) == "":
                    title_de = data['title_en']
            else:
                title_de = ""
                       
            section_details = {
                    "@attrs": {
                        "ref": ref,
                        "seq": str(data["seq"]),
                        "editor_restricted": str(data["editor_restricted"]),
                        "meta_indexed": str(data["meta_indexed"]),
                        "meta_reviewed": str(data["meta_reviewed"]),
                        "abstracts_not_required": str(data["abstracts_not_required"]),
                        "hide_title": str(data["hide_title"]),
                        "hide_author": str(data["hide_author"]),
                        "abstract_word_count": "0"#str(data["abstract_word_count"])
                    },
                    "@name": "section",          
                    "id":{
                        "@attrs": {"type":"internal", "advice":"ignore"},
                        "@value": str(data["seq"]),
                    },
                    "abbrev": data["abbrev"],
                    "policy": policy,#str(data["policy"]),
                    "title_en": {
                        "@attrs": {
                            "locale": 'en_US',
                        },
                        "@name": "title",
                        "@value": data["title_en"]
                    },
                    "title_de": {
                        "@attrs": {
                            "locale": 'de_DE',
                        },
                        "@name": "title",
                        "@value": title_de
                    },
                }

            if title_de == "":
                del section_details["title_de"]
            sections["section_{}".format(ref)] = section_details
        return sections

class OjsBooleanJob(OjsJob):

    def get_article_no(self, doi):
        year = doi.split(".")[-2]
        art_id = int(doi.split(".")[-1])
        lookup = {
            "2010": 100,
            "2011": 200,
            "2012": 300,
            "2013": 400,
            "2014": 500,
            "2015": 600,
        }
        art_no = lookup[year] + art_id
        return str(art_no) 

    def get_issue_path(self):
        issue_identification = self.get_issue_identification()
        year = issue_identification["year"]
        issue_path = "http://research.ucc.ie/boolean/{0}/00".format(year)
        return issue_path 

    def get_issue(self):
        issue_path = self.get_issue_path()
        issue = scenario.parseBooleanIssue(issue_path)
        return issue

    def get_article_obj(self, url):
        art_obj = scenario.parseBoolean(url)
        return art_obj

class OjsScenarioJob(OjsJob):

    def get_article_no(self, doi): 
        article_no = re.sub(r"\D", "", doi.split("/")[1])
        return article_no

    def get_issue_path(self):
        issue_identification = self.get_issue_identification()
        num_pad = issue_identification["number"].rjust(2, '0')
        num = str(int(num_pad))
        year = issue_identification["year"]
        issue_path = "http://research.ucc.ie/scenario/{0}/{1}".format(year, num_pad)
        return issue_path 

    def get_issue(self):
        issue_path = self.get_issue_path()
        issue = scenario.parseScenarioIssue(issue_path)
        return issue

    def get_article_obj(self, url):
        art_obj = scenario.parseScenario(url)
        return art_obj


class OjsChimeraJob(OjsJob):

    def get_article_no(self, doi):
        art_id = int(doi.split(".")[-1])
        art_no = 700 + art_id
        return str(art_no) 

    def get_issue_path(self):
        return "http://research.ucc.ie/chimera/2013/00"

    def get_issue(self):
        issue_path = self.get_issue_path()
        issue = scenario.parseIssue(issue_path)
        return issue

    def get_article_obj(self, url):
        art_obj = scenario.parseChimera(url)
        return art_obj

class OjsIjppJob(OjsJob):

    def get_article_no(self, doi):
        art_id = int(doi.split(".")[-1])
        art_no = 800 + art_id
        return str(art_no) 

    def get_issue_path(self):
        issue_identification = self.get_issue_identification()
        num_pad = issue_identification["number"].rjust(2, '0')
        num = str(int(num_pad))
        year = issue_identification["year"]
        issue_path = "http://research.ucc.ie/ijpp/{0}/{1}".format(year, num_pad)
        return issue_path 

    def get_issue(self):
        issue_path = self.get_issue_path()
        issue = scenario.parseIjppIssue(issue_path)
        return issue

    def get_article_obj(self, url):
        art_obj = scenario.parseIjpp(url)
        return art_obj





