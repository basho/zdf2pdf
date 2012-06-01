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
4. Run `zdf2pdf` for the documentation set(s) you wish to archive.
5. Create a new entry in the Archived Documentation section of
Zendesk Documentation at https://help.basho.com.
6. Add your generated archive PDF to the entry with any additional notes, etc.

The details for each step above will be presented in the following sections.

## Zendesk API Token Setup

To use zdf2pdf as shown in the **zdf2pdf Utility** section, you
must first generate a Zendesk API token for your account. This token helps
you to avoid disclosing your Zendesk user account password, and it can be
regenerated or disabled altogether at any time.

To create a Zendesk API token for use with zdversion, follow these steps:

1. Log into your Zendesk user account at this URL: https://help.basho.com/
2. Navigate to this URL: https://help.basho.com/settings/api/
3. Click the **Enabled** checkbox inside the **Token Access** section.
4. Make note of the 40 character string after *Your API token is:*
5. Click Save.

**NOTE**: If you have problems with step #3 above, you might need to ask
someone  with appropriate Zendesk-fu to provide you with the
necessary permissions.

Once your Zendesk API token is configured, and you've made note of it,
proceed to configuring a Python virtual environment on the system with which
you plan to archive documentation.

## Virtual Environment Setup

The most effective way to set up for using zdf2pdf is to install
virtualenv, and follow these steps:

Clone the zdf2pdf repo:

    git clone git@github.com:basho/zdf2pdf.git

Create a new virtualenv in the clone directory:

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

Install beautifulsoup4, httplib2, pycurl, simplejson, and xhtml2pdf:

    pip install beautifulsoup4 httplib2 pycurl simplejson xhtml2pdf

Clone the Python zendesk module:

    cd src
    git clone git@github.com:basho/zendesk.git
    cd zendesk
    python setup.py install
    cd $VIRTUAL_ENV

Finally, install zdf2pdf itself:

    cd $VIRTUAL_ENV
    python setup.py install

More detailed information for installation and configuring virtualenv for
specific environments is available from the
[virtualenv project page](http://pypi.python.org/pypi/virtualenv).

## zdf2pdf Utility

zdf2pdf is the Python script for creating documentation snapshots. Once you have configured it for use with your Zendesk account, you can use it to archive documentation.

### Configuration

Before using zdf2pdf, you must configure some basics, such as the target Zendesk URL, your account name, and your API token. These values are stored in the file `~/.zdf2pdf.cfg`, and the expected format of the file
is shown in this example:

    [zdf2pdf]
    email = you@example.com
    token = dneib393fwEF3ifbsEXAMPLEdhb93dw343
    url = https://example.zendesk.com

Once you have created a `~/.zdf2pdf.cfg` file with values specific to
your installation, you can proceed to using zdf2pdf.

### Usage

The script can be invoked with the following synopsis:

    zdf2pdf [-h] [-c CONFIG_FILE] [-f ENTRIES_FILE | -i FORUM_ID | -l]
                      [-k KEEP_FILE] [-o PDF_FILE] [-t PDF_TITLE] [-v]


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

#### Generate PDF from Forums URL

To generate a PDF archive document directly from a particular forum URL and save the PDF with a certain title and filename, execute zdf2pdf
with the `-i`, `-t`, and `-o` options:

    zdf2pdf -i 20828562 -t "Great Justice" -o great_justice-v1.pdf

where the `-i` option specifies a Zendesk forum identifier, which is the 8-digit string that makes up part of a Zendesk forum URL. For example, in the
following URL:

    https://help.basho.com/forums/20748808-operations

the forum identifier is **20748808**.

The `-t` option specifies a title for the PDF document, which appears in the document text.

Finally, the `-o` option tells zdf2pdf to save the PDF with the filename `great_justice-v1.pdf`.

#### Generate PDF from Forums JSON File

To generate a PDF archive document from an existing JSON file containing
Zendesk forum entries, and give a custom title to the document,
execute zdf2pdf with the `-f` and `-t` options:

    zdf2pdf -f my_file.json -t "Documentation Archive"

The above command will open the file `my_file.json`, and generate a PDF titled
"Documentation Archive", with the filename `Documentation Archive.pdf`.


## Notes

* zdf2pdf uses Zendesk API version 1 with JSON
* zdf2pdf depends on the following Python modules:
 * beautifulsoup4
 * httplib2
 * pycurl
 * simplejson
 * xhtml2pdf
 * zendesk

### Issues and Caveats

There are potential issues and caveats with this process:

* zdf2pdf does not currently handle additional forum metadata such
as file attachments, but this is a planned capability that is in progress.

### Resources

* zdf2pdf: https://github.com/basho/zdf2pdf
* Python Zendesk module: https://github.com/basho/zendesk
* Zendesk API: http://developer.zendesk.com/documentation/rest_api/introduction.html