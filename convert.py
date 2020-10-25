from xmler import dict2xml
import xmet 
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert to Crossref and Dspace metadata')
    parser.add_argument('input_filename', help='the filename to process')
    parser.add_argument('--journal', help='the journal title being processed, e.g. scenario, boolean, alphaville', default='none')
    args = vars(parser.parse_args())
    print(args)
    input_file = args['input_filename']
    journal = args['journal']
    crossref_job = xmet.CrossRefJob(input_file)
    crossref_job.generate()
    
    dspace_job = xmet.DspaceJob(input_file)
    dspace_job.generate()

    if journal == "scenario":
        ojs_job = xmet.OjsScenarioJob(input_file)
        ojs_job.generate()
    elif journal == "boolean":
        ojs_job = xmet.OjsBooleanJob(input_file)
        ojs_job.generate()
