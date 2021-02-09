from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
import re
from unidecode import unidecode
import datetime

class fetchUtils():
    def __init__(self, contrib_db):
        self.contrib_db = contrib_db # "contribs_boolean.xlsx"
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

    def get_name_parts(self, contrib):
        return contrib.split(" ", 1)

    def get_contibs(self, contribs, affiliation = ""):
        contrib_keys = []

        if len(contribs) == 0:
            return ""

        for contrib in contribs:
            if contrib in ["Foreword", "Vorwort"]:
                contrib = "Manfred Schewe"
            contrib = " ".join(contrib.split()).strip()
            name_parts = self.get_name_parts(contrib)
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