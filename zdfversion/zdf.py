"""
zdfversion: Helper script for Zendesk forum entry (DOCUMENTATION tab) version
specific archive creation and maintenance.

See the following URL for documentation on usage & process:

http://bit.ly/Ks368Y

Example <forum_id> for reading from help.basho.com: 20767107
"""

class ZDF:
    def __init__(self, creds=None, url=None):
        # creds looks like you@example.com/token:dneib393fwEF3ifbsEXAMPLEdhb93dw343
        self.creds = creds
        if url:
            self.url = url + '/api/v1/forums/'
        else:
            self.url = None

    def curl(self, forum_id):
        """Wrapper function around PyCurl with XML/Zendesk specific bits"""
        if not self.creds and not self.url:
            # raise some kind of exception if no creds and no url
            return

        import pycurl
        try:
            import cStringIO
        except ImportError:
            import StringIO

        sio = cStringIO.StringIO()
        curl = pycurl.Curl()
        curl.setopt(curl.HTTPHEADER, ['Accept: application/xml'])
        curl.setopt(curl.URL, self.url + forum_id + '/entries.xml')
        curl.setopt(curl.WRITEFUNCTION, sio.write)
        curl.setopt(curl.CONNECTTIMEOUT, 5)
        curl.setopt(curl.TIMEOUT, 7)
        curl.setopt(curl.FOLLOWLOCATION, True)
        curl.setopt(curl.MAXREDIRS, 5)
        curl.setopt(curl.USERPWD, self.creds)
        curl.setopt(curl.CUSTOMREQUEST, "GET")
        curl.perform()
        result = sio.getvalue()
        sio.close()
        return result;

    def xml2pdf(self, tree, filename, title=''):
        print('xml2pdf not yet implemented')

    def strip(self):
        """Strips elements which need to be regenerated automatically by the
        Zendesk API at POST time"""
        for elem in tree.iterfind('entry/created-at'):
            elem.clear()
        for elem in tree.iterfind('entry/id'):
            elem.clear()
        for elem in tree.iterfind('entry/submitter-id'):
            elem.clear()
        for elem in tree.iterfind('entry/updated-at'):
            elem.clear()

def main(argv=None):
    import os, sys, argparse
    import ConfigParser as configparser
    try:
        import xml.etree.cElementTree as et
    except ImportError:
        import xml.etree.ElementTree as et

    argp = argparse.ArgumentParser(
        description='Make a PDF documentation archive from a series of Zendesk forum entries.')
    argp.add_argument('-c', action='store', dest='config_file',
        default=os.path.expanduser('~') + '/.zdfversion.cfg',
        help='Zendesk configuration file (default: ~/.zdfversion.cfg)')

    g1 = argp.add_mutually_exclusive_group()
    g1.add_argument('-f', action='store', dest='entries_file',
        help='Zendesk entries XML file to convert to PDF')
    g1.add_argument('-i', action='store', dest='forum_id',
        help='Zendesk forum ID to download and convert to PDF')

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

    # Set up the ZDF object and obtain the xml tree
    if args.entries_file:
        # use an xml file on disk
        zdf = ZDF()
        tree = et.ElementTree(file=args.entries_file)
    elif args.forum_id:
        # Get the xml from zendesk
        # Read zendesk info from config file
        config = configparser.RawConfigParser()
        try:
            config.read(args.config_file)
            email = config.get('zdfversion', 'email')
            token = config.get('zdfversion', 'token')
            url   = config.get('zdfversion', 'url')
        except configparser.NoSectionError:
            from textwrap import dedent
            msg = dedent("""\
                Error: Could not read settings from {config}

                Expected config file to be of the format:
                [zdfversion]
                email = you@example.com
                token = dneib393fwEF3ifbsEXAMPLEdhb93dw343
                url = https://example.zendesk.com
                """)
            print(msg.format(config=args.config_file))
            return 1

        creds = email + '/token:' + token
        zdf = ZDF(creds=creds, url=url)
        entries = zdf.curl(args.forum_id)
        tree = et.XML(entries)

        # If requested, save the downloaded XML file
        if args.keep_file:
            with open(args.keep_file, "w") as outfile:
                outfile.write(entries)
    else:
        print('Error: Need either Zendesk entries XML file or remote forum ID.\n')
        return 1

    if not args.pdf_file:
        args.pdf_file = 'bob.pdf'

    if not args.pdf_title:
        args.pdf_title = 'Bob'

    zdf.xml2pdf(tree=tree, filename=args.pdf_file, title=args.pdf_title)
    return 0

