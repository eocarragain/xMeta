
# xMeta

A set of python scripts for converting metadata in a specific spreadsheet format into XML for submission to CrossRef and CSV for loading into DSpace. It also includes code used to scrape legacy journal sites to facilitate migration to OJS using its native XML import format.

## Installation (Windows 10 specific)
### Install Python

 - Open a command prompt
 - Type ```python -V ``` to make sure python isn't already installed. If it is and is a version other than 3.7 or 3.8 you may need to uninstall or use a virtual environment tool which is capable of managing multiple versions of python (note: installations will currently fail with versions of python higher than 3.8 as they are not supported by numpy which is a dependency)
 - Assuming python isn't installed, download the latest 3.8.x installer from https://www.python.org/downloads/release/python-3810/. Download the 32 bit installer. Note: Windows may try to install from Windows Store, but avoid this.
 - Double click the installer & be sure to tick the "Add Python 3.8 to PATH box before clicking "Install Now"
 - Open a new command prompt and type ```python -V ``` to verify you are using version 3.8.x

### Download script

 - Download & extract the latest version as a zip file from github (or use git to clone it): https://github.com/eocarragain/xMeta/
 - In the command prompt, navigate into the project folder that you extracted. Type the following commands:
 -  ``` python -m venv env```
 -  ``` env\Scripts\activate.bat```
 -  ``` pip install -r requirements.txt ```
 - This should install additionally libraries. Note: if the last command fails with an error about needing Visual Studio Build tools, this can be installed from
https://visualstudio.microsoft.com/visual-cpp-build-tools/. Then try the last command again

You should now be ready to use xMeta.


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
