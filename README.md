# Archiving Zendesk Based Documentation

This guide describes the process and tools for creating archived, version
specific, Zendesk based product documentation snapshots in the form of PDF
documents which are stored in the **Archived Documentation** section of our
documentation at http://help.basho.com/.

## Process

The process for creating a documentation archive is fairly straightforward,
but involves some one-time preparation of the Zendesk account for users
making documentation archives. Additional time is required to establish a working environment for the documentation archiving utility, zdf2pdf.

Here are the essential steps for a basic documentation archiving run:

1. One time set up of Zendesk user API token.
2. Get zdf2pdf: https://github.com/basho/zdf2pdf
3. One time set up of Python virtualenv work environment and dependencies.
4. Run `zdf2pdf` for the documentation set(s) to archive.
5. Create a new entry in the Archived Documentation section of
Zendesk Documentation at https://help.basho.com.
6. Add generated archive PDF to the entry with any additional notes, etc.

The details for each step above will be presented in the following sections.

## Zendesk API Token Setup

Prior to using zdf2pdf, a Zendesk API token must be generated for the
account that will be used for archiving documentation. This token helps
avoid disclosing the Zendesk user account password, and it can be
regenerated or disabled altogether at any time.

To create a Zendesk API token for use with zdversion, follow these steps:

1. Log into the Basho Zendesk at this URL: https://help.basho.com/
2. Navigate to this URL: https://help.basho.com/settings/api/
3. Click the **Enabled** checkbox inside the **Token Access** section.
4. Make note of the 40 character string after *Your API token is:*
5. Click Save.

**NOTE**: If problems occur with step #3 above, the account used to access
Zendesk could lack the necessary permissions to work with an API token. In
this case, appropriate permissions should be requested from a Basho Zendesk
administrator.

Once the Zendesk API token is configured, and noted, proceed to configuring
a Python virtual environment.

## Virtual Environment Setup

The most effective way to set up for using zdf2pdf is to install
virtualenv, and follow these steps:

Create a new virtualenv:

    virtualenv zdf2pdf

Activate the virtualenv:

    cd zdf2pdf && source bin/activate

Build Freetype2:

Download Freetype (version 2.4.9 used for this guide) from this URL:
http://sourceforge.net/projects/freetype/files/freetype2/2.4.9/

    mkdir src && cd src
    tar zxf freetype-2.4.9.tar.gz
    cd freetype-2.4.9
    ./configure --prefix=$VIRTUAL_ENV
    make
    make install
    cd $VIRTUAL_ENV

Install beautifulsoup4, httplib2, simplejson, and xhtml2pdf:

    pip install beautifulsoup4 httplib2 simplejson xhtml2pdf

Clone the Python zendesk module:

    cd src
    git clone git@github.com:basho/zendesk.git
    cd zendesk
    python setup.py install
    cd $VIRTUAL_ENV

Finally, install zdf2pdf itself:

    cd src
    git clone git@github.com:basho/zdf2pdf.git
    cd $VIRTUAL_ENV/lib/python2.7/site-packages
    ln -s <path_to_code>/zdf2pdf/zdf2pdf
    cd $VIRTUAL_ENV/bin
    ln -s <path_to_code>/zdf2pdf/bin/zdf2pdf
    cd $VIRTUAL_ENV

Change `<path_to_code>` in the above example to the path where the zdf2pdf
source code is located.

More detailed information for installation and configuring virtualenv for
specific environments is available from the
[virtualenv project page](http://pypi.python.org/pypi/virtualenv).

## zdf2pdf Utility

zdf2pdf is the Python script for creating documentation snapshots. Once it
is configured for use with a Zendesk account, it can be used to generate
documentation archives.

### Configuration

Before using zdf2pdf, some basic configuration should be set, such as the
target Zendesk URL, account name to use, and associated API token. These
values are stored in the `~/.zdf2pdf.cfg` file, and the expected format of
the file is shown in this example:

    [zdf2pdf]
    email = you@example.com
    token = dneib393fwEF3ifbsEXAMPLEdhb93dw343
    url = https://example.zendesk.com

Once a `~/.zdf2pdf.cfg` file with values specific to the installation has
been created, proceed to using zdf2pdf.

### Usage

The script can be invoked with the following synopsis:

    zdf2pdf [-h] [-v] [-j JSON_FILE] [-f FORUMS] [-e ENTRIES]
            [-r RUN_SECTION] [-l [FORUM_TO_LIST]] [-c CONFIG_FILE]
            [-s STYLE_FILE] [-o OUTPUT_FILE] [-t TITLE] [-a AUTHOR]
            [--date DATE] [--copyright COPYRIGHT]
            [--title-class TITLE_CLASS] [--toc] [-w WORK_DIR] [-d] [-u URL]
            [-m MAIL] [-p [PASSWORD]] [-i]

The optional arguments taken by zdf2pdf:

    -h, --help            show this help message and exit
    -v, --verbose         Verbose output
    -j JSON_FILE          Zendesk entries JSON file to convert to PDF
    -f FORUMS             Comma separated Forum IDs to download and convert
                          to PDF
    -e ENTRIES            Comma separated Entry IDs to download and convert
                          to PDF
    -r RUN_SECTION        Run pre-configured section in configuration file
    -l [FORUM_TO_LIST]    List a forum's entries by ID and title. If no
                          forum ID is supplied, list forums by ID and title
    -c CONFIG_FILE        Configuration file (overrides ~/.zdf2pdf.cfg)
    -s STYLE_FILE         Style file (CSS) to <link>
    -o OUTPUT_FILE        Output filename (default: PCLOADLETTER.pdf)
    -t TITLE              Title to be added to the beginning of the PDF
    -a AUTHOR             Author line to be added to the beginning of the PDF
    --date DATE           Date line to be added to the beginning of the PDF
    --copyright COPYRIGHT
                          Copyright line to be added to the beginning of PDF
    --title-class TITLE_CLASS
                          CSS class to be added to title page elements
    --toc                 Generate a Table of Contents (default: true)
    -w WORK_DIR           Working directory in which to store JSON output
                          and images (default: temp dir)
    -d, --delete          Delete working directory at program exit
                          (default: do not delete)
    -u URL                URL of Zendesk (e.g. https://example.zendesk.com)
    -m MAIL               E-Mail address for Zendesk login
    -p [PASSWORD]         Password for Zendesk login
    -i, --is-token        Specify supplied password is a Zendesk token

Here are some basic zdf2pdf usage examples to get started:

#### Help

    zdf2pdf -h

#### Listing forums

    zdf2pdf -l

The output consists of a listing of forum identifiers and their names:

    20832476 Announcements
    20832486 Community Help
    20832496 Tips & Tricks
    20832506 Feature Requests
    20832516 Agents Only
    20828562 Foo
    20828672 Wikiport II
    20840027 Bar
    20846071 Baz

#### Generate PDF from Forums URL by Forum ID

To generate a PDF archive document directly from a particular forum URL and
save the PDF with a certain title and filename, execute zdf2pdf
with the `-i`, `-t`, and `-o` options:

    zdf2pdf -i 20828562 -t "Great Justice" -o great_justice-v1.pdf

where the `-i` option specifies a Zendesk forum identifier, which is the
8-digit string that makes up part of a Zendesk forum URL. For example, in the
following URL:

    https://help.basho.com/forums/20748808-operations

the forum identifier is **20748808**.

The `-t` option specifies a title for the PDF document, which appears in
the document text.

Finally, the `-o` option tells zdf2pdf to save the PDF with the filename
`great_justice-v1.pdf`.

#### Generate PDF from a Forums JSON File

To generate a PDF archive document from an existing JSON file containing
Zendesk forum entries, and give a custom title to the document,
execute zdf2pdf with the `-f` and `-t` options:

    zdf2pdf -f my_file.json -t "Documentation Archive"

The above command will open the file `my_file.json`, and generate a PDF titled
"Documentation Archive", with the filename `Documentation Archive.pdf`.


#### Generate PDF from Forums URL with Custom Style

To generate a PDF archive document directly from a particular forum URL, save
the PDF with a certain title and filename, and apply a custom CSS stylesheet
to the output, execute zdf2pdf with the `-i`, `-t`, `-o`, and `-s` options:

    zdf2pdf -i 20828562 -t "Styled" -o styled.pdf -s ./style.css

where the `-i` option specifies a Zendesk forum identifier, which is the
8-digit string that makes up part of a Zendesk forum URL. For example, in the
following URL:

    https://help.basho.com/forums/20748808-operations

the forum identifier is **20748808**.

The `-t` option specifies a title for the PDF document, which appears in the
document text.

The `-o` option tells zdf2pdf to save the PDF with the filename `styled.pdf`.

Finally, the `-s` option tells zdf2pdf to style the output with CSS from the
file `style.css` located in the present working directory.

## Notes

* zdf2pdf uses Zendesk API version 1 with JSON
* zdf2pdf depends on the following Python modules:
 * beautifulsoup4
 * httplib2
 * simplejson
 * xhtml2pdf
 * zendesk

### Issues and Caveats

There are potential issues and caveats with this process:

* zdf2pdf does not currently handle additional forum metadata such
  as file attachments, but this is a planned capability that is in progress.
* Future versions of zdf2pdf will allow for a simpler syntax that can
  automatically generate a given product documentation set with one switch.
  (See also: issue #1)

### Resources

* zdf2pdf: https://github.com/basho/zdf2pdf
* Python Zendesk module: https://github.com/basho/zendesk
* Zendesk Developer Site (For API information): http://developer.zendesk.com
