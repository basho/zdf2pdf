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
2. One time set up of Python virtualenv to do documentation archival work in.
3. Get zdfversion: <TODO> add URL https://github.com/basho/zdfversion
4. Run `zdfversion` for the documentation set(s) you wish to archive.
5. Create a new entry in the Archived Documentation section of
Zendesk Documentation at http://help.basho.com.
6. Add your generated archive PDF to the entry with any additional notes.

The details for each step above will be presented in the following sections.

## Zendesk API Token Setup

To use zdfversion as shown in the **zdfversion Utility** section, you
must first generate a Zendesk API token for your account. This token helps
you to avoid disclosing your Zendesk user account password, and can be
regenerated or disabled altogether at any time.

To create a Zendesk API token for use with **zdversion*, follow these steps:

1. Log into your Zendesk user account at this URL: https://help.basho.com/
2. Navigate to this URL: https://help.basho.com/settings/api/
3. Click the **Enabled** checkbox inside the **Token Access** section to enable
your user account API token
4. Make note of the 40 character string after *Your API token is:*
5. Click Save

**NOTE**: If you have problems with step #3 above, you might need to ask
someone  with appropriate Zendesk-fu to provide you with the
necessary permissions.

Once your Zendesk API token is configured, and you've made note of it,
proceed to configuring a Python virtual environment on the machine with which
you plan to archive documentation.

## Virtual Environment Setup

The most effective way to setup for using the zdfversion utility, is to
install virtualenv, and then follow these steps:

Create a new virtualenv:

    virtualenv zdfversion

Activate the virtualenv:

    cd zdfversion && source bin/activate

Install PyCurl:

    pip install pycurl

Obtain zdfversion from this URL: <FIXME> add URL https://github.com/basho/zdfversion

Place **zdversion** into the virtualenv you created, and execute it per the
instructions in the **zdfversion Utility** section.

More detailed information for installation and configuring virtualenv for
specific environments is available from the
[virtualenv project page](http://pypi.python.org/pypi/virtualenv).

## zdfversion Utility

zdfversion is the Python module for creating documentation snapshots.
The module is simple to use, with the following synopsis:

    zdfversion -l -i <forum_id> -f <entries_file>

**Listing forums**:

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

### zdfversion Configuration

Before using zdfversion, you must configure some basics, such as the target Zendesk URL, your account name, and your API token. These values are stored in the file `~/.zdfversion.cfg`, and the expected format of the file
is shown in this example:

    [zdfversion]
    email = you@example.com
    token = dneib393fwEF3ifbsEXAMPLEdhb93dw343
    url = https://example.zendesk.com

Once you have created a `~/.zdfversion.cfg` file with values specific to
your installation, you can proceed to using zdfversion.

### Generate a PDF from forums

    zdfversion -i 20828562

where the `-i` option specifies a Zendesk forum identifier, which is the 8-digit string that makes up part of a Zendesk forum URL. For example, in the
following URL:

    https://help.basho.com/forums/20748808-operations

the forum identifier is **20748808**.

The `-f` option specifies a file of forum entries from which to use for generation of PDF instead of a forum id directly.

## Notes

### Issues and Caveats

There are potential issues and caveats with this process:

* zdfversion does not currently handle additional forum metadata such
as file attachments, but it is a planned capability that is in progress.

