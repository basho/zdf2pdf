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

def zdf2pdf(entries, filename, title='', style=None):
    from bs4 import BeautifulSoup
    import xhtml2pdf.pisa as pisa
    try:
        import cStringIO as SIO
    except ImportError:
        import StringIO as SIO

    data = '<head>'

    if style:
        data += '<link rel="stylesheet" type="text/css" href="{}" />'.format(style)

    data += '</head>'

    data += '<h1>' + title + '</h1>'
    for entry in entries:
        data += '<h1>' + entry['title'] + '</h1>'
        data += entry['body']

    soup = BeautifulSoup(data)
    for img in soup.find_all('img'):
        src = img.attrs['src']
        srcfile = src.replace('/', '_')
        # see if we already have this image
        #os.path.isfile(
        if src[0:4] != 'http':
            pass
            # append base url to relative srcs

    pdf = pisa.CreatePDF(
        SIO.StringIO(soup.prettify().encode('utf-8')),
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
            email: you@example.com
            token: dneib393fwEF3ifbsEXAMPLEdhb93dw343
            url: https://example.zendesk.com
            """)
        print(msg.format(config=config_file))
        return None

def main(argv=None):
    import os, sys, argparse
    import logging

    logging.basicConfig()

    argp = argparse.ArgumentParser(
        description='Make a PDF from Zendesk forums or entries.')
    argp.add_argument('-c', action='store', dest='config_file',
        default=os.path.expanduser('~') + '/.zdf2pdf.cfg',
        help='Zendesk configuration file (default: ~/.zdf2pdf.cfg)')

    g1 = argp.add_mutually_exclusive_group(required=True)
    g1.add_argument('-j', action='store', dest='json_file',
        help='Zendesk entries JSON file to convert to PDF')
    g1.add_argument('-f', action='store', dest='forums',
        help='Comma separated forum IDs to download and convert to PDF')
    g1.add_argument('-e', action='store', dest='entries',
        help='Comma separated forum IDs to download and convert to PDF')
    g1.add_argument('-l', action='store', dest='list_zdf',
        help="""List a forum's entries by ID and title.  If no forum ID is
        supplied, list forums by ID and title""",
        nargs='?', const='forums', metavar='FORUM_TO_LIST')

    argp.add_argument('-s', action='store', dest='style_file',
        help='Style file (CSS) to embed')

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

    if args.entries or args.forums or args.list_zdf:
        zd = config_zendesk(args.config_file)
        if not zd:
            return 1

    # Use an entries file on disk
    if args.json_file:
        # Refrain from guessing about the PDF title when using an entries file
        if not args.pdf_title:
            print('Error: Entries file specified but no title given.')
            print('       Use -t PDF_TITLE to specify a title.')
            return 1

        # Get the entries off disk
        with open(args.json_file, 'r') as infile:
            entries = json.loads(infile.read())

    # Get individual entries from zendesk
    elif args.entries:
        # Refrain from guessing the PDF title when using individual entries
        if not args.pdf_title:
            print('Error: Entry IDs specified but no title given.')
            print('       Use -t PDF_TITLE to specify a title.')
            return 1

        # Get the entries and build the json file
        entries = []
        try:
            entry_ids = [int(i) for i in args.entries.split(',')]
            for entry_id in entry_ids:
                entries += zd.show_entry(entry_id=entry_id)
        except ValueError:
            print('Error: Could not convert to integers: {}'.format(args.entries))
            return 1

    # Get the entries from one or more zendesk forums
    elif args.forums:
        # If no title given, use the forum title from Zendesk
        if not args.pdf_title:
            forum = zd.show_forum(forum_id=args.forums)
            args.pdf_title = forum['name']

        # Get the forum entries
        entries = []
        try:
            forum_ids = [int(i) for i in args.forums.split(',')]
            for forum_id in forum_ids:
                entries += zd.list_entries(forum_id=args.forums)
        except ValueError:
            print('Error: Could not convert to integers: {}'.format(args.forums))
            return 1

        # If requested, save the downloaded entries file
        if args.keep_file:
            with open(args.keep_file, "w") as outfile:
                outfile.write(json.dumps(entries))

    elif args.list_zdf == 'forums':
        # List available zendesk forums with their IDs and titles and exit
        forums = zd.list_forums()
        for forum in forums:
            print(str(forum['id']) + ' ' + forum['name'])
        return 0

    elif args.list_zdf:
        # List a zendesk forum's entries with their IDs and titles and exit
        try:
            forum_id = int(args.list_zdf)
        except ValueError:
            print('Error: Could not convert to integer: {}'.format(args.list_zdf))
            return 1

        entries = zd.list_entries(forum_id=args.list_zdf)
        for entry in entries:
            print(str(entry['id']) + ' ' + entry['title'])
        return 0

    else:
        # Should never get here, since the mutually exclusive argparse
        # group is set to required
        print args.list_zdf
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

    zdf2pdf(entries=entries, filename=args.pdf_file, title=args.pdf_title,
            style=args.style_file)
    return 0

