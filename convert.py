from xmler import dict2xml
import xmet 
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert to Crossref and Dspace metadata')
    parser.add_argument('input_filename', help='the filename to process')
    parser.add_argument('--journal', help='the journal title being processed, e.g. scenario, boolean, alphaville', default='none')
    parser.add_argument('--type', help='the type of item being processed, either journal or conference', default='journal')
    parser.add_argument('--ojs', help='whether to attemp to scrape legacy content and generate OJS import XML, true if yes', default='false')
    args = vars(parser.parse_args())
    print(args)
    input_file = args['input_filename']
    journal = args['journal']
    type = args['type']
    ojs = args['ojs']
    
    if type == "journal":
        dspace_job = xmet.DspaceJob(input_file)
        dspace_job.generate()

        crossref_job = xmet.CrossRefJournalJob(input_file)
        crossref_job.generate()

        if journal == "scenario" and ojs == "true":
            ojs_job = xmet.OjsScenarioJob(input_file)
            ojs_job.generate()
        elif journal == "boolean" and ojs == "true":
            ojs_job = xmet.OjsBooleanJob(input_file)
            ojs_job.generate()
        elif journal == "chimera" and ojs == "true":
            ojs_job = xmet.OjsChimeraJob(input_file)
            ojs_job.generate()
        elif journal == "ijpp" and ojs == "true":
            ojs_job = xmet.OjsIjppJob(input_file)
            ojs_job.generate()
    elif type == "conference":
        crossref_job = xmet.CrossRefConferenceJob(input_file)
        crossref_job.generate()

        dspace_job = xmet.DspaceConferenceJob(input_file)
        dspace_job.generate()


