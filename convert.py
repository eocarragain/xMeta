from xmler import dict2xml
import xmet 
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert to Crossref and Dspace metadata')
    parser.add_argument('input_filename', nargs=1, help='the filename to process')
    args = vars(parser.parse_args())
    print(args)
    input_file = args['input_filename'][0]
    crossref_job = xmet.CrossRefJob(input_file)
    crossref_job.generate()
    
    dspace_job = xmet.DspaceJob(input_file)
    dspace_job.generate()
