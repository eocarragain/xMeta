from xmler import dict2xml
import crossref 

#job = crossref.CrossRefJob("Kopie von Metadata_Scenario_13_1_28_06 - Editable.xlsx")
input_file = "Metadata_Alphaville_Issue17.xlsx"
crossref_job = crossref.CrossRefJob(input_file)
crossref_job.generate()

dspace_job = crossref.DspaceJob(input_file)
dspace_job.generate()

myDict = {
    "doi_batch": {
        "@attrs": {
            "version": "4.4.2",
            "xmlns": "http://www.crossref.org/schema/4.4.2",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": "http://www.crossref.org/schema/4.4.2 http://www.crossref.org/schema/deposit/crossref4.4.2.xsd"
        },
        "head": {
            "doi_batch_id": "acde",
            "timestamp": "201907032310",
            "depositor": {
                "depositor_name": "University College Cork",
                "email_address": "cora@ucc.ie"
            },
            "registrant": "University College Cork"
        },
        "body": {
            "journal": {
                "journal_metadata": {
                    "@attrs": {
                        "reference_distribution_opts": "any",
                    },
                    "full_title": "Alphaville: Journal of Film and Screen Media",
                    "abbrev_title": "Alphaville",
                    "issn": "2009-4078",
                    "doi_data": {
                        "doi": "10.33178/alpha",
                        "resource": "http://www.alphavillejournal.com/"
                    }
                }
            }
        }

    }
}

#print(dict2xml(myDict))