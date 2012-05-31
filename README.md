# Archiving Zendesk Based Documentation

This guide describes the process and tools for creating archived, version
specific, Zendesk based product documentation snapshots in the form of PDF
documents which are stored in the **Archived Documentation** section of our
documentation at http://help.basho.com/.

## Process

The process for creating a documentation archive is fairly straightforward,
but involves some one-time preparation of the Zendesk account for users
making documentation archives. Additional time is required to establish a working environment for the documentation archiving utility, zdfversion.

Here are the essential steps for a basic documentation archiving run:

1. One time set up of Zendesk user API token.
2. One time set up of Python virtualenv work environment.
3. Get zdfversion: <TODO> add URL
4. Run `zdfversion` for the documentation set(s) you wish to archive.
5. Create a new entry in the Archived Documentation section of
Zendesk Documentation at https://help.basho.com.
6. Add your generated archive PDF to the entry with any additional notes, etc.

The details for each step above will be presented in the following sections.

## Zendesk API Token Setup

To use zdfversion as shown in the **zdfversion Utility** section, you
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

The most effective way to set up for using zdfversion is to install
virtualenv, and follow these steps:

Create a new virtualenv:

    virtualenv zdfversion

Activate the virtualenv:

    cd zdfversion && source bin/activate

Build Freetype2:

    mkdir src && cd src
    curl -O

Install PyCurl:

    pip install pycurl

Obtain zdfversion from this URL: <FIXME> add URL

Place zdfversion into the virtualenv you created, and execute it per the
instructions in the **zdfversion Utility** section.

More detailed information for installation and configuring virtualenv for
specific environments is available from the
[virtualenv project page](http://pypi.python.org/pypi/virtualenv).

## zdfversion Utility

### zdfversion Configuration

zdfversion is the Python script for creating documentation snapshots.

Before using zdfversion, you must configure some basics, such as the target Zendesk URL, your account name, and your API token. These values are stored in the file `~/.zdfversion.cfg`, and the expected format of the file
is shown in this example:

    [zdfversion]
    email = you@example.com
    token = dneib393fwEF3ifbsEXAMPLEdhb93dw343
    url = https://example.zendesk.com

Once you have created a `~/.zdfversion.cfg` file with values specific to
your installation, you can proceed to using zdfversion.

The script can be invoked with the following synopsis:

    zdfversion [-h] [-c CONFIG_FILE] [-f ENTRIES_FILE | -i FORUM_ID | -l]
                      [-k KEEP_FILE] [-o PDF_FILE] [-t PDF_TITLE] [-v]


### Listing forums

    zdfversion -l

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

### Generate PDF from Forums URL

To generate a PDF archive document from a forum URL, execute zdfversion
with the `-i` option:

    zdfversion -i 20828562

where the `-i` option specifies a Zendesk forum identifier, which is the 8-digit string that makes up part of a Zendesk forum URL. For example, in the
following URL:

    https://help.basho.com/forums/20748808-operations

the forum identifier is **20748808**.

The `-f` option specifies a file of forum entries from which to use for generation of PDF instead of a forum id directly.

### Generate PDF from Forums File

## Notes

### Issues and Caveats

There are potential issues and caveats with this process:

* zdfversion does not currently handle additional forum metadata such
as file attachments, but this is a planned capability that is in progress.

