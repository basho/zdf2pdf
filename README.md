# Creating PDFs from Zendesk forums and entries

Zdf2pdf is a utility for downloading entries or entire forums from
[Zendesk](http://www.zendesk.com) and creating PDFs from them.

## Installing

Tested with Python 2.7. Simplejson, httplib2, and beautifulsoup4 are required.
Zdf2pdf requires xhtml2pdf for the generation of PDF files. Also, to
communicate with Zendesk forums, the [patched
zendesk](http://github.com/eventbrite/zendesk) Python module is required. Therefore,
the installation process is usually something like:

1. Install Freetype if not installed. (libfreetype.a needed for reportlab build)
2. Install prereqs using `pip install simplejson beautifulsoup4 httplib2 xhtml2pdf`
4. Install zendesk using `pip install https://github.com/eventbrite/zendesk/archive/master.zip`
5. Install zdf2pdf using `pip install https://github.com/basho/zdf2pdf/archive/master.zip`

Alternatively, instead of using pip to directly install from the public git
repos, one can clone them locally and run `python setup.py install`.

## Freetype2 and Reportlab on OS X

Mac OS X, as of 10.7, does not ship with libfreetype.a, which is useful when
building reportlab. The simplest way to deal with this issue is to install
zdf2pdf and its required packages into a
[virtualenv](http://pypi.python.org/pypi/virtualenv). One can then install
libfreetype.a into the lib directory of the virtualenv for reportlab to use
when building.

To do this, install virtualenv, create a new virtualenv, and then download
Freetype (version 2.4.9 used for this guide) from this URL:
http://sourceforge.net/projects/freetype/files/freetype2/2.4.9/

    cd /path/to/your/virtualenv/
    source bin/activate
    cd /path/to/downloaded/freetype/
    tar zxf freetype-2.4.9.tar.gz
    cd freetype-2.4.9
    ./configure --prefix=$VIRTUAL_ENV
    make
    make install

Once this is done, install reportlab into the virtualenv.

    # if not already activated
    cd /path/to/your/virtualenv
    source bin/activate
    # xhtml2pdf will automatically pull in reportlab
    pip install xhtml2pdf

## Zendesk API Token Setup

Prior to using zdf2pdf, a Zendesk API token must be generated for the
account that will be used for archiving documentation. This token helps
avoid disclosing the Zendesk user account password, and it can be
regenerated or disabled altogether at any time.

To create a Zendesk API token for use with zdversion, follow these steps:

1. Log into the your Zendesk website: https://example.zendesk.com
2. Navigate to the API settings: https://example.zendesk.com/settings/api/
3. Click the **Enabled** checkbox inside the **Token Access** section.
4. Make note of the 40 character string after *Your API token is:*
5. Click Save.

**NOTE**: If problems occur with step #3 above, the account used to access
Zendesk could lack the necessary permissions to work with an API token. In this
case, appropriate permissions should be requested from your administrator.

Once the Zendesk API token is configured, and noted, proceed to configuring
a Python virtual environment.

### Configuration

Options when running zdf2pdf can be configured through configuration files. The
`[zdf2pdf]` section of the file `~/.zdf2pdf.cfg` is always read. Once the
options from this section are applied, the command line options are applied
(see next section). If the `-c CONFIG_FILE` option is specified, then the
`[zdf2pdf]` section from the specified config file is then applied. Also, if
the `-r RUN_SECTION` option is specified, the `[RUN_SECTION]` from
`~/.zdf2pdf.cfg` is read and applied. Finally, if both `-c` and `-r` options
are given, the `[RUN_SECTION]` from `CONFIG_FILE` is applied.

The purpose of offering so many configuration options is to allow individuals
to set their desired options such as `mail`, `url`, and `password` in their own
~/.zdf2pdf.cfg, and then groups can share config files that have options set
such as `forums`, `entries`, `title`, etc. All options are valid in all config
files and sections. An example of using two config files is given below.

    # ~/.zdf2pdf.cfg
    [zdf2pdf]
    mail = you@example.com
    password = dneib393fwEF3ifbsEXAMPLEdhb93dw343
    url = https://example.zendesk.com
    is_token = 1

    [MyBook]
    forums = 20747046, 20877608, 20748808
  


    # Example config file with all options. This is a comment.
    [tps_report]
    # version is not actually a config option. used for interpolation below
    version = 1.1.2
    # verbose = 1
    # json_file = entries.json
    forums = 30617246, 10887508, 23728902
    # topics = 30162764, 20878085, 32279820
    style_file = mystyle.css
    output_file = tps_report-%(version)s.pdf
    title = TPS REPORT %(version)s
    author = Peter Gibbons<br/>Bill Lumbergh, Supervisor
    date = Feb 19 1999
    copyright = Copyright © 2012 Initech, Inc.
    title_class = titlePage
    toc = 1
    toc_title = Table of Contents
    toc_class = tableOfContents
    pre_width = 80
    strip_empty = 1
    # header = <div id="header">Some header HTML</div>
    footer = <div id="footer">
      <pdf:pagenumber/>
      </div>
      <pdf:nexttemplate name="regular"/>
    # category_sections = 0
    forum_sections = 1
    # topics_heading = 'Section heading above 30162764, 20878085, and 32279820'
    work_dir = my_tps_reports
    # delete = 1
    url = https://example.zendesk.com
    mail = pgibbons@example.com
    password = dneib393fwEF3ifbsEXAMPLEdhb93dw343
    is_token = true


### Usage

The script can be invoked with the following synopsis:

    usage: zdf2pdf [-h] [-v] [-j JSON_FILE] [-f FORUMS] [-e ENTRIES]
                   [-r RUN_SECTION] [-l [FORUM_TO_LIST]] [-c CONFIG_FILE]
                   [-s STYLE_FILE] [-o OUTPUT_FILE] [-t TITLE] [-a AUTHOR]
                   [--date DATE] [--copyright COPYRIGHT]
                   [--title-class TITLE_CLASS] [--toc] [--pre-width PRE_WIDTH]
                   [--strip-empty] [-w WORK_DIR] [-d] [-u URL] [-m MAIL]
                   [-p [PASSWORD]] [-i]

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Verbose output
      -j JSON_FILE          Zendesk entries JSON file to convert to PDF
      -f FORUMS             Comma separated Forum IDs to download and convert to
                            PDF
      -e ENTRIES            Comma separated Entry IDs to download and convert to
                            PDF
      -r RUN_SECTION        Run pre-configured section in configuration file
      -l [FORUM_TO_LIST]    List a forum's entries by ID and title. If no forum ID
                            is supplied, list forums by ID and title
      -c CONFIG_FILE        Configuration file (overrides ~/.zdf2pdf.cfg)
      -s STYLE_FILE         Style file (CSS) to <link>
      -o OUTPUT_FILE        Output filename (default: PCLOADLETTER.pdf)
      -t TITLE              Title to be added to the beginning of the PDF
      -a AUTHOR             Author line to be added to the beginning of the PDF
      --date DATE           Date line to be added to the beginning of the PDF
      --copyright COPYRIGHT
                            Copyright line to be added to the beginning of the PDF
      --title-class TITLE_CLASS
                            CSS class to be added to title page elements
      --toc                 Generate a Table of Contents (default: false)
      --pre-width PRE_WIDTH
                            Width to wrap contents of <pre></pre> tags.
      --strip-empty         Strip empty tags. (default: false)
      -w WORK_DIR           Working directory in which to store JSON output and
                            images (default: temp dir)
      -d, --delete          Delete working directory at program exit (default: do
                            not delete)
      -u URL                URL of Zendesk (e.g. https://example.zendesk.com)
      -m MAIL               E-Mail address for Zendesk login
      -p [PASSWORD]         Password for Zendesk login
      -i, --is-token        Is token? Specify if password supplied a Zendesk token

Here are some basic zdf2pdf usage examples to get started:

#### Help

    zdf2pdf -h

#### Listing forums

    zdf2pdf -l

The output consists of a listing of forum identifiers and their titles:

    20828562 Foo
    20840027 Bar

Entries in a forum can also be listed:

    zdf2pdf -l 20828562

The output consists of a listing of entry identifiers and their titles:

    21460866 Baz
    21442012 Qux

#### Generate PDF from Forums URL by Forum ID

To generate a PDF archive document directly from a particular forum URL and
save the PDF with a certain title and filename, execute zdf2pdf
with the `-f`, `-t`, and `-o` options:

    zdf2pdf -f 20828562 -t "Great Justice" -o great_justice-v1.pdf

where the `-f` option specifies a Zendesk forum identifier, which is the
8-digit string that makes up part of a Zendesk forum URL. For example, in the
following URL:

    https://example.zendesk.com/forums/20828562-foo

the forum identifier is **20828562**.

The `-t` option specifies a title for the PDF document, which appears in
the document text on a title page.

Finally, the `-o` option tells zdf2pdf to save the PDF with the filename
`great_justice-v1.pdf`.

#### Generate PDF from a Forums JSON File

To generate a PDF archive document from an existing JSON file containing
Zendesk forum entries, and give a custom title to the document,
execute zdf2pdf with the `-j` and `-t` options:

    zdf2pdf -j my_file.json -t "Documentation Archive"

The above command will open the file `my_file.json`, and generate a PDF titled
"Documentation Archive", with the default filename PCLOADLETTER.pdf.

#### Generate PDF from Forums URL with Custom Style

To generate a PDF archive document directly from a particular forum URL, save
the PDF with a certain title and filename, and apply a custom CSS stylesheet
to the output, execute zdf2pdf with the `-f`, `-t`, `-o`, and `-s` options:

    zdf2pdf -f 20828562 -t "Styled" -o styled.pdf -s ./style.css

where the `-f` option specifies a Zendesk forum identifier, which is the
8-digit string that makes up part of a Zendesk forum URL. For example, in the
following URL:

    https://example.zendesk.com/forums/20828562-foo

the forum identifier is **20828562**.

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
 * zendesk (patched for forum support)

### Headers and Footers

The header and footer options are provided for the purpose of doing things like
page numbers. They provide the capability to inject HTML at the beginning of
the document which can be styled to suit various purposes. For example, page
numbers can be achieved by using an option like this in a config file:

    footer = <div id="footer">
      <pdf:pagenumber/>
      </div>
      <pdf:nexttemplate name="regular"/>

And then using CSS such as:

    @page {
        -pdf-page-orientation: portrait;
        -pdf-page-size: letter;
        margin: 2cm;
    }

    @page regular {
        -pdf-page-orientation: portrait;
        -pdf-page-size: letter;
        margin: 2cm 2cm 3cm 2cm;
        @frame footer {
            -pdf-frame-content: footer;
            bottom: 1.5cm;
            left: 2cm;
            right: 2cm;
            height: .6cm;
        }
    }

The above will result in a first page which does not contain a footer, and
following pages that do contain a footer. The footer will contain the PDF page
number.

### Resources

* zdf2pdf: https://github.com/basho/zdf2pdf
* Python Zendesk module: https://github.com/eventbrite/zendesk
* Zendesk Developer Site (For API information): http://developer.zendesk.com
