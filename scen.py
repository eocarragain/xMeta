import xmet 
#year_range = range(2009, 2010)
year_range = range(2015, 2021)
filenames = []
for year in year_range:
    filenames.append("scenario_{0}_01.xlsx".format(year))
    filenames.append("scenario_{0}_02.xlsx".format(year))

next_issue = "scenario_2020_02.xlsx"
if next_issue in filenames:
    filenames.remove(next_issue)

for input_file in filenames:
    print(input_file)
    crossref_job = xmet.CrossRefJob(input_file)
    crossref_job.generate()
    
    dspace_job = xmet.DspaceJob(input_file)
    dspace_job.generate()

    ojs_job = xmet.OjsJob(input_file)
    ojs_job.generate()

    
