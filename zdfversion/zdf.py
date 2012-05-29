#!/usr/bin/env python

"""
zdfversion: Helper script for Zendesk forum entry (knowledge base)
            documentation set version creation and maintenance.
            See: <TODO> Internal wiki link with documentation on usage, etc.

            Example <forum_id>: 20767107
"""

import argparse
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

creds = "you@example.com/token:dneib393fwEF3ifbsEXAMPLEdhb93dw343"
zdf_entries = "entries.xml"
zdf_forums = "forums.xml"
zdf_get_base = "https://help.basho.com/api/v1/forums/"
zdf_post_base = "https://help.basho.com/api/v1/"

parser = argparse.ArgumentParser(description="Gets current versions and posts new versions of Zendesk forum entries")
parser.add_argument('-f', action='store', dest='entries_filename',
                    help='Specify XML file containing Zendesk forum entries for uploading')

parser.add_argument('-i', action='store', dest='forum_id',
                    help='Specify an 8 digit Zendesk forum identifier from which to get entries')
parser.add_argument('-n', action='store', dest='new_forum', help='Specify the quoted name of the new forum target for documentation snapshot')
parser.add_argument('-o', action='store', dest='output_file',
                    help='Specify optional output filename for forum entries file (default: entries_clean.xml)')
# <TODO>
# parser.add_argument("-v","--verbose", help="Verbose output")
# args = parser.parse_args(['-h'])
args = parser.parse_args()

def zdf_curl(fid, verb, data):
    """Wrapper function around PyCurl with XML/Zd specific bits"""
    b = cStringIO.StringIO()
    c = pycurl.Curl()
    if verb == "GET":
        c.setopt(c.HTTPHEADER, ['Accept: application/xml'])
        zdf_url = zdf_get_base + args.forum_id + '/' + zdf_entries
    else:
        c.setopt(c.HTTPHEADER, ['Content-type: application/xml'])
        zdf_url = zdf_post_base + zdf_entries
    c.setopt(c.URL, zdf_url)
    c.setopt(c.WRITEFUNCTION, b.write)
    c.setopt(c.CONNECTTIMEOUT, 5)
    c.setopt(c.TIMEOUT, 7)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.MAXREDIRS, 5)
    c.setopt(c.USERPWD, creds)
    c.setopt(c.CUSTOMREQUEST, verb)
    if not data == "null":
        c.setopt(c.POSTFIELDS, data)
    c.perform()
    result = b.getvalue()
    b.close()
    return result;


# <TODO> clean this up a bit
def zdf_strip():
    """Strips elements which need to be regenerated automatically by the API at POST time"""
    for elem in tree.iterfind('entry/created-at'):
        elem.clear()
    for elem in tree.iterfind('entry/id'):
        elem.clear()
    for elem in tree.iterfind('entry/submitter-id'):
        elem.clear()
    for elem in tree.iterfind('entry/updated-at'):
        elem.clear()


def zdf_new_forum(nfname):
    root = ET.Element('forum')
    forum_name = ET.SubElement(root, 'name')
    forum_name.text = nfname
    restrict = ET.SubElement(root, 'visibility-restriction-id')
    restrict.text = "3"
    tree = ET.ElementTree(root)
    #<TODO> API call and catch result for new forum id

def zdf_post_new(nfid, data):
    # testing
    nfid = "20846071"
    new_entries = zdf_curl(zdf_get_base + args.forum_id + '/' + zdf_entries, "GET", "null")
    tree = ET.ElementTree(new_entries)
    zdfstrip()

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
