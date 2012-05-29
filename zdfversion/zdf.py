"""
zdfversion: Helper script for Zendesk forum entry (knowledge base)
            documentation set version creation and maintenance.
            See: <TODO> Internal wiki link with documentation on usage, etc.

            Example <forum_id>: 20767107
"""

import os
import pycurl
import sys
try:
    import cStringIO
except ImportError:
    import StringIO
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET



class ZDF():
    def __init__(creds, url):
        self.creds = creds # e.g. "you@example.com/token:dneib393fwEF3ifbsEXAMPLEdhb93dw343"
        self.url = url + '/api/v1/forums/'
        self.entries = "entries.xml"
        #self.forums = "forums.xml"
        #self.post_base = "https://help.basho.com/api/v1/"

    def curl(forum_id):
        """Wrapper function around PyCurl with XML/Zd specific bits"""
        sio = cStringIO.StringIO()
        curl = pycurl.Curl()
        curl.setopt(curl.HTTPHEADER, ['Accept: application/xml'])
        curl.setopt(curl.URL, self.url + forum_id + '/' + self.entries)
        curl.setopt(curl.WRITEFUNCTION, sio.write)
        curl.setopt(curl.CONNECTTIMEOUT, 5)
        curl.setopt(curl.TIMEOUT, 7)
        curl.setopt(curl.FOLLOWLOCATION, True)
        curl.setopt(curl.MAXREDIRS, 5)
        curl.setopt(curl.USERPWD, self.creds)
        curl.setopt(curl.CUSTOMREQUEST, "GET")
        #if not data == "null":
        #    curl.setopt(curl.POSTFIELDS, data)
        curl.perform()
        result = sio.getvalue()
        sio.close()
        return result;

    def strip():
        """Strips elements which need to be regenerated automatically by the API at POST time"""
        for elem in tree.iterfind('entry/created-at'):
            elem.clear()
        for elem in tree.iterfind('entry/id'):
            elem.clear()
        for elem in tree.iterfind('entry/submitter-id'):
            elem.clear()
        for elem in tree.iterfind('entry/updated-at'):
            elem.clear()

# <FIXME> This might not be the approach now
"""
if args.forum_id:
    entries = zdf_curl(zdf_get_base + args.forum_id + '/' + zdf_entries, "GET", "null")
    tmpfile = "./entries_tmp.xml"
    with open(tmpfile, "w") as outfile:
        outfile.write(entries)
    tree = ET.ElementTree(file=tmpfile)
    zdf_strip()
    if args.output_file:
        clnfile = args.output_file
    else:
        clnfile = "./entries_clean.xml"
    with open(clnfile, "w") as newfile:
        tree.write(newfile)
    os.unlink(tmpfile)
else:
    print "I need a forum identifier to continue."
    sys.exit(1)

if entries.filename:
    if entries.newforum:
        print "Gonna make a new forum, YAY!"
        # <TODO> create forum xml
        # <TODO> post forum xml
        # <TODO> return newly created forum's id

    else:
        print "You must specify a new forum name in quotes"
        sys.exit(1)
"""

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    import argparse

    args = argparse.ArgumentParser(
        description='Make a PDF from a Zendesk forum.')
    args.add_argument('-c', action='store', dest='config_filename',
        default='~/.zdfversion.cfg',
        help='Zendesk configuration filename (default: ~/.zdfversion.cfg)')
    args.add_argument('-f', action='store', dest='entries_filename',
        help='Zendesk entries XML file to convert to PDF')
    args.add_argument('-i', action='store', dest='forum_id',
        help='Zendesk forum ID to download and convert to PDF')
    args.add_argument('-o', action='store', dest='pdf_filename',
        help='PDF output filename')
    args.add_argument('-t', action='store', dest='pdf_title',
        help='PDF title')
    args.add_argument("-v","--verbose",
        help="Verbose output")
    args.add_argument("-h","--help",
        help="Help and Usage")

    if argv is None:
        argv = sys.argv
    try:
        try:
            args = args.parse_args()
            opts, args = getopt.getopt(argv[1:], "h", ["help"])
        except getopt.error, msg:
             raise Usage(msg)
        # more code, unchanged
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

    import ConfigParser as configparser
    config = configparser.RawConfigParser()
    config.read(config_filename)
    email = config.get('zdfversion', 'email')
    token = config.get('zdfversion', 'token')
    url   = config.get('zdfversion', 'url')

    creds = email + '/token:' + token
    ZDF(creds = "you@example.com/token:dneib393fwEF3ifbsEXAMPLEdhb93dw343",
          url = url
       )

if __name__ == "__main__":
    main()

