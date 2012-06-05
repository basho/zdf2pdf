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

def zdf2pdf(entries, filename, title=None, style=None):
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

    if title:
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
    argp.add_argument('-v', action='store_true',
        help='Verbose output')

    g1 = argp.add_mutually_exclusive_group(required=True)
    g1.add_argument('-j', action='store', dest='json_file',
        help='Zendesk entries JSON file to convert to PDF')
    g1.add_argument('-f', action='store', dest='forums',
        help='Comma separated Forum IDs to download and convert to PDF')
    g1.add_argument('-e', action='store', dest='entries',
        help='Comma separated Entry IDs to download and convert to PDF')
    g1.add_argument('-r', action='store', dest='run_section',
        help='Run pre-configured section in configuration file')
    g1.add_argument('-l', action='store', dest='list_zdf',
        help="""List a forum's entries by ID and title.  If no forum ID is
        supplied, list forums by ID and title""",
        nargs='?', const='forums', metavar='FORUM_TO_LIST')

    argp.add_argument('-c', action='store', dest='config_file',
        default=os.path.expanduser('~') + '/.zdf2pdf.cfg',
        help='Configuration file (default: ~/.zdf2pdf.cfg)')
    argp.add_argument('-s', action='store', dest='style_file',
        help='Style file (CSS) to <link>')
    argp.add_argument('-o', action='store', dest='output_file',
        help='Output filename (default: PCLOADLETTER.PDF)',
        default='PCLOADLETTER.PDF')
    argp.add_argument('-t', action='store', dest='title',
        help='Title to be added to the beginning of the PDF', default=None)

    argp.add_argument('-w', action='store', dest='work_dir',
        help='Working directory in which to stores JSON and images (default: temp dir)')
    argp.add_argument('-d', action='store_true', dest='del_dir',
        help='Delete working directory at program exit')

    argp.add_argument('-u', action='store', dest='url',
        help='URL of Zendesk (e.g. https://example.zendesk.com)')
    argp.add_argument('-m', action='store', dest='mail',
        help='E-Mail address for Zendesk login')
    argp.add_argument('-p', action='store', dest='password',
        help='Password for Zendesk login')
    argp.add_argument('-i', action='store_true', dest='is_token',
        help='Is token? Specify if password supplied a Zendesk token')

    if argv is None:
        argv = sys.argv
    args = argp.parse_args()

    if args.entries or args.forums or args.list_zdf:
        zd = config_zendesk(args.config_file)
        if not zd:
            return 1

    # Use an entries file on disk
    if args.json_file:
        # Get the entries off disk
        with open(args.json_file, 'r') as infile:
            entries = json.loads(infile.read())

    # Get individual entries from zendesk
    elif args.entries:
        entries = []
        try:
            entry_ids = [int(i) for i in args.entries.split(',')]
            for entry_id in entry_ids:
                entries.append(zd.show_entry(entry_id=entry_id))
        except ValueError:
            print('Error: Could not convert to integers: {}'.format(args.entries))
            return 1

    # Get the entries from one or more zendesk forums
    elif args.forums:
        entries = []
        try:
            forum_ids = [int(i) for i in args.forums.split(',')]
            for forum_id in forum_ids:
                entries += zd.list_entries(forum_id=forum_id)
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

    zdf2pdf(entries=entries, filename=args.pdf_file, title=args.pdf_title,
            style=args.style_file)
    return 0

