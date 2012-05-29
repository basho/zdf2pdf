"""
zdfversion: Helper script for Zendesk forum entry (knowledge base)
            documentation set version creation and maintenance.
            See: <TODO> Internal wiki link with documentation on usage, etc.

            Example <forum_id>: 20767107
"""

class ZDF:
    def __init__(self, creds, url):
        # creds looks like you@example.com/token:dneib393fwEF3ifbsEXAMPLEdhb93dw343
        self.creds = creds
        self.url = url + '/api/v1/forums/'

    def curl(self, forum_id):
        """Wrapper function around PyCurl with XML/Zd specific bits"""
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
        """Strips elements which need to be regenerated automatically by the API at POST time"""
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
        description='Make a PDF from a Zendesk forum.')
    argp.add_argument('-c', action='store', dest='config_file',
        default=os.path.expanduser('~') + '/.zdfversion.cfg',
        help='Zendesk configuration file (default: ~/.zdfversion.cfg)')

    group = argp.add_mutually_exclusive_group()
    group.add_argument('-f', action='store', dest='entries_file',
        help='Zendesk entries XML file to convert to PDF')
    group.add_argument('-i', action='store', dest='forum_id',
        help='Zendesk forum ID to download and convert to PDF')

    argp.add_argument('-o', action='store', dest='pdf_file',
        help='PDF output filename')
    argp.add_argument('-t', action='store', dest='pdf_title',
        help='PDF title')
    argp.add_argument('-v', '--verbose', action='store_true',
        help='Verbose output')

    if argv is None:
        argv = sys.argv
    args = argp.parse_args()

    config = configparser.RawConfigParser()
    try:
        config.read(args.config_file)
        email = config.get('zdfversion', 'email')
        token = config.get('zdfversion', 'token')
        url   = config.get('zdfversion', 'url')
    except configparser.NoSectionError:
        print('Could not read settings from ' + args.config_file)
        return 1

    creds = email + '/token:' + token
    zdf = ZDF(creds=creds, url=url)

    if args.entries_file:
        tree = et.ElementTree(file=args.entries_file)
    elif args.forum_id:
        entries = zdf.curl(args.forum_id)
        xml_filename = args.forum_id + '.xml'
        with open(xml_filename, "w") as outfile:
            outfile.write(entries)
        tree = et.XML(entries)
    else:
        print('Error: Need either Zendesk entries XML file or remote forum ID.\n')
        return 1

    if not args.pdf_file:
        args.pdf_file = 'bob.pdf'

    if not args.pdf_title:
        args.pdf_title = 'Bob'

    zdf.xml2pdf(tree=tree, filename=args.pdf_file, title=args.pdf_title)
    return 0

