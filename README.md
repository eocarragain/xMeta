# xMeta

A set of python scripts for converting metadata in a specific spreadsheet format into XML for submission to CrossRef and CSV for loading into DSpace. It also includes code used to scrape legacy journal sites to facilitate migration to OJS using its native XML import format.

## Installation
TODO

## Usage


```
usage: convert.py [-h] [--journal JOURNAL] [--type TYPE] [--ojs OJS]
                  input_filename

Convert to Crossref and Dspace metadata

positional arguments:
  input_filename     the filename to process

optional arguments:
  -h, --help         show this help message and exit
  --journal JOURNAL  the journal title being processed, e.g. scenario,
                     boolean, alphaville
  --type TYPE        the type of item being processed, either journal or
                     conference
  --ojs OJS          whether to attemp to scrape legacy content and generate
                     OJS import XML, true if yes
```

The options above allow for additional functionality to generate conference metadata (needs work) or to scrape legacy journals. In the standard case of generating CrossRef article XML and Dspace CSV, the command is :
```
python convert.py my_excel_metadata_file.xlsx
```

This command will generate two files in the same folder as the original Excel file: my_excel_metadata_file.xml (Crossref XML), my_excel_metadata_file.csv (the DSpace CSV). These can be loaded through the CrossRef and DSpace interfaces respecively. 

## Contributing
This code is not maintained. 

## License
[MIT](https://choosealicense.com/licenses/mit/)