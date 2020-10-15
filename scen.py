import xmet 
#year_range = range(2009, 2010)
year_range = range(2007, 2019)
filenames = []
for year in year_range:
    filenames.append("scenario_{0}_01.xlsx".format(year))
    filenames.append("scenario_{0}_02.xlsx".format(year))

for input_file in filenames:
    print(input_file)
    crossref_job = xmet.CrossRefJob(input_file)
    crossref_job.generate()
    
    dspace_job = xmet.DspaceJob(input_file)
    dspace_job.generate()

    ojs_job = xmet.OjsJob(input_file)
    ojs_job.generate()

    
def get_parsed_name(contrib):
    Graham W. Lea
    Amir Hossein Esmkhani
    Annie Ó Breacháin
    Antu Romero Nunes
    Catherine Van Halsema
    Sophie Charlotte Rummel
    Isobel Ní Riain
    Kathleen Rose McGovern
    Konstantinos Prokopios Trimmis
    Leticia García Brea
    María Isabel Fernández García
    Maria Giovanna Biscu


            elif len(name_parts) > 2:
            parsed_name = self.get_parsed_name(contrib)
            if len(parsed_name) > 0:
            else:
                name_parts = contrib.split(" ", 1)
                given_name = name_parts[0]
                family_name = name_parts[1]
