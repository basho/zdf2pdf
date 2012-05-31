"""
zdf2pdf: Create version specific documentation archives from Zendesk
product documentation at https://help.basho.com

See the following URL for documentation on usage & process:

https://help.basho.com/entries/21469982-archiving-zendesk-based-documentation

Example <forum_id> for reading from help.basho.com: 20767107
"""
try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et

class zdf2pdf:
    def __init__(self, creds=None, url=None):
        # creds ex: you@example.com/token:dneib393fwEF3ifbsEXAMPLEdhb93dw343
        self.fapi_path = '/api/v1/forums/'
        self.creds = creds
        if url:
            self.url = url
        else:
            self.url = None

    def _zdf_request(self, url):
        if not self.creds:
            # raise some kind of exception if no creds
            return

        import pycurl
        try:
            import cStringIO as SIO
        except ImportError:
            import StringIO as SIO

        sio = SIO.StringIO()
        curl = pycurl.Curl()
        curl.setopt(curl.HTTPHEADER, ['Accept: application/xml'])
        curl.setopt(curl.URL, url)
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

    def read_config(self, config_file):
        # Read zendesk info from config file
        import ConfigParser as configparser
        config = configparser.RawConfigParser()
        config.read(config_file)
        email = config.get('zdf2pdf', 'email')
        token = config.get('zdf2pdf', 'token')
        url   = config.get('zdf2pdf', 'url')

        self.creds = email + '/token:' + token
        self.url   = url


    def get_all_forums(self):
        return self._zdf_request(self.url + '/forums.xml')

    def get_forum_entries(self, fid):
        """Wrapper function around PyCurl with XML/Zendesk specific bits"""
        return self._zdf_request(self.url + self.fapi_path + fid + '/entries.xml')

    def get_forum(self, fid):
        return self._zdf_request(self.url + '/forums/' + fid + '.xml')

    def xml2pdf(self, tree, filename, title=''):
        import xhtml2pdf.pisa as pisa
        import HTMLParser
        try:
            import cStringIO as SIO
        except ImportError:
            import StringIO as SIO

        htmlparser = HTMLParser.HTMLParser()

        data = '<h1>' + title + '</h1>'
        for entry in tree.iter('entry'):
            #t = htmlparser.unescape(entry.find('body').text)
            #print(t)
            t = entry.find('body').text
            entry_tree = et.XML(t)
            for img in entry_tree.iter('img'):
                print(img.attrib['src'])
            data += t
            data += '<br/><br/>'

        pdf = pisa.CreatePDF(
            SIO.StringIO(data),
            file(filename, "wb")
        )

        #if pdf.err:
        #    dumpErrors(pdf)

def _config_errmsg():
    from textwrap import dedent
    msg = dedent("""\
        Error: Could not read settings from {config}

        Expected config file to be of the format:
        [zdf2pdf]
        email = you@example.com
        token = dneib393fwEF3ifbsEXAMPLEdhb93dw343
        url = https://example.zendesk.com
        """)
    print(msg.format(config=args.config_file))

def main(argv=None):
    import os, sys, argparse

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

    # Set up the zdf2pdf object and obtain the xml tree
    zdf = zdf2pdf()

    # use an xml file on disk
    if args.entries_file:
        # Refrain from guessing about the PDF title when using an entries file
        if not args.pdf_title:
            print('Error: Entries file specified but no title given.')
            print('       Use -t PDF_TITLE to specify a title.')
            return 1

        # Get the entries off disk and make the etree
        tree = et.ElementTree(file=args.entries_file)

    # Get the xml from zendesk
    elif args.forum_id:
        try:
            zdf.read_config(args.config_file)
        except configparser.NoSectionError:
            _config_errmsg()
            return 1

        # If no title given, use the forum title from Zendesk
        if not args.pdf_title:
            forum_tree = et.XML(zdf.get_forum(args.forum_id))
            args.pdf_title = forum_tree.find('name').text

        # Get the entries and make the etree
        entries = zdf.get_forum_entries(args.forum_id)
        tree = et.XML(entries)

        # If requested, save the downloaded XML file
        if args.keep_file:
            with open(args.keep_file, "w") as outfile:
                outfile.write(entries)
    elif args.list_forums:
        # list available zendesk forums with their IDs and exit
        try:
            zdf.read_config(args.config_file)
        except configparser.NoSectionError:
            _config_errmsg()
            return 1

        tree = et.XML(zdf.get_all_forums())
        for forum in tree.iter('forum'):
            print(forum.find('id').text + ' ' + forum.find('name').text)
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

    zdf.xml2pdf(tree=tree, filename=args.pdf_file, title=args.pdf_title)
    return 0

