# -*- coding: utf-8 -*-

"""
zdf2pdf: Create version specific documentation archives from Zendesk
product documentation at https://help.basho.com

See the following URL for documentation on usage & process:

https://help.basho.com/entries/21469982-archiving-zendesk-based-documentation

Example <forum_id> for reading from help.basho.com: 20767107
"""
try:
    import simplejson as json
except:
    import json

try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et

def zdf2pdf(entries, filename, title=''):
    from bs4 import BeautifulSoup
    import xhtml2pdf.pisa as pisa
    try:
        import cStringIO as SIO
    except ImportError:
        import StringIO as SIO

    data = '<style>h1,h2,h3,h4,h5,h5{font-family:Helvetica,arial,freesans,clean,sans-serif;}h1{font-size:33px;color:#3d3d3d;font-weight:700;}h2{font-size:24px;color:#141414;}h2{font-size:18px;color:#3d3d3d;}body,p{font-family:Helvetica,arial,freesans,clean,sans-serif;font-size:14px;}a{color:#4183C4;}</style>'
    data += '<h1>' + title + '</h1>'
    for entry in entries:
        data += '<h1>' + entry['title'] + '</h1>'
        data += entry['body']
        data += '<br /><br />'

    #soup = BeautifulSoup(data)
    #print(soup.prettify())
    #for img in soup.find_all('img'):
    #    src = img.attrs['src']
    #    srcfile = src.replace('/', '_')
    #    # see if we already have this image
    #    #os.path.isfile(
    #    if src[0:4] != 'http':
    #        pass
    #        # append base url to relative srcs

    pdf = pisa.CreatePDF(
        SIO.StringIO(data.encode('utf-8')),
        file(filename, "wb"),
        encoding = 'utf-8'
    )

    if pdf.err and pdf.log:
        for mode, line, msg, code in pdf.log:
            print "%s in line %d: %s" % (mode, line, msg)

    if pdf.warn:
        print "*** %d WARNINGS OCCURED" % pdf.warn


def config_zendesk(config_file):
    """Read Zendesk info from config file"""
    from zendesk import Zendesk
    import ConfigParser as configparser

    config = configparser.RawConfigParser()
    config.read(config_file)
    try:
        email = config.get('zdf2pdf', 'email')
        token = config.get('zdf2pdf', 'token')
        url   = config.get('zdf2pdf', 'url')

        # Set up the zendesk object
        zd = Zendesk(url,
                    zendesk_username = email,
                    zendesk_password = token,
                    use_api_token = True)
        return zd

    except configparser.NoSectionError:
        from textwrap import dedent
        msg = dedent("""\
            Error: Could not read settings from {config}

            Expected config file to be of the format:
            [zdf2pdf]
            email = you@example.com
            token = dneib393fwEF3ifbsEXAMPLEdhb93dw343
            url = https://example.zendesk.com
            """)
        print(msg.format(config=config_file))
        return None

def main(argv=None):
    import os, sys, argparse
    import logging

    logging.basicConfig()

    argp = argparse.ArgumentParser(
        description='Make a PDF from Zendesk forums.')
    argp.add_argument('-c', action='store', dest='config_file',
        default=os.path.expanduser('~') + '/.zdf2pdf.cfg',
        help='Zendesk configuration file (default: ~/.zdf2pdf.cfg)')

    g1 = argp.add_mutually_exclusive_group()
    g1.add_argument('-f', action='store', dest='entries_file',
        help='Zendesk entries XML file to convert to PDF')
    g1.add_argument('-i', action='store', dest='forum_id',
        help='Zendesk forum ID to download and convert to PDF')
    g1.add_argument('-l', action='store_true', dest='list_forums',
        help='List Zendesk forums and IDs')

    # this should technically only be available if using -i, but argparse
    # doesn't support groups under mutually exclusive group ala
    # [ -i FORUM_ID [-k KEEP_FILE] ] | [ -f ENTRIES_FILE ] ]
    # See: http://bugs.python.org/issue11588
    argp.add_argument('-k', action='store', dest='keep_file',
        help='Keep the fetched entries xml file at the given file path')

    argp.add_argument('-o', action='store', dest='pdf_file',
        help='PDF output filename')
    argp.add_argument('-t', action='store', dest='pdf_title',
        help='PDF title')
    argp.add_argument('-v', '--verbose', action='store_true',
        help='Verbose output')

    if argv is None:
        argv = sys.argv
    args = argp.parse_args()

    # Use an entries file on disk
    if args.entries_file:
        # Refrain from guessing about the PDF title when using an entries file
        if not args.pdf_title:
            print('Error: Entries file specified but no title given.')
            print('       Use -t PDF_TITLE to specify a title.')
            return 1

        # Get the entries off disk
        with open(args.entries_file, 'r') as infile:
            entries = json.loads(infile.read())

    # Get the entries from zendesk
    elif args.forum_id:
        zd = config_zendesk(args.config_file)
        if not zd:
            return 1

        # If no title given, use the forum title from Zendesk
        if not args.pdf_title:
            forum = zd.show_forum(forum_id=args.forum_id)
            args.pdf_title = forum['name']

        # Get the entries
        entries = zd.list_entries(forum_id=args.forum_id)

        # If requested, save the downloaded entries file
        if args.keep_file:
            with open(args.keep_file, "w") as outfile:
                outfile.write(json.dumps(entries))

    elif args.list_forums:
        # List available zendesk forums with their IDs and exit
        zd = config_zendesk(args.config_file)
        if not zd:
            return 1

        forums = zd.list_forums()
        for forum in forums:
            print(str(forum['id']) + ' ' + forum['name'])
        return 0

    else:
        from textwrap import dedent
        msg = dedent("""\
            Error: One of the following is required:
              -l option to list forums
              -i FORUM_ID to retrieve
              -f ENTRIES_FILE to convert
            """)
        print(msg)
        return 1

    # If no PDF filename given, name it after the title
    if not args.pdf_file:
        args.pdf_file = args.pdf_title + '.pdf'

    zdf2pdf(entries=entries, filename=args.pdf_file, title=args.pdf_title)
    return 0

