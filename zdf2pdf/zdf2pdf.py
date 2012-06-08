"""
zdf2pdf: Create version specific documentation archives from Zendesk
product documentation at https://help.basho.com

See the following URL for documentation on usage & process:

https://help.basho.com/entries/21469982-archiving-zendesk-based-documentation

Example <forum_id> for reading from help.basho.com: 20767107
"""
from __future__ import unicode_literals
import os, shutil
try:
    import simplejson as json
except:
    import json

def zdf2pdf(entries, opts):
    import re
    from bs4 import BeautifulSoup
    import urllib, urlparse
    import xhtml2pdf.pisa as pisa
    try:
        import cStringIO as SIO
    except ImportError:
        import StringIO as SIO

    # Save the current directory so we can go back once done
    startdir = os.getcwd()

    # Start the xhtml to be converted
    data = '<head>\n'

    # Normalize all of the given paths to absolute paths
    opts['output_file'] = os.path.abspath(opts['output_file'])
    opts['work_dir'] = os.path.abspath(opts['work_dir'])
    attach_dir = os.path.join(opts['work_dir'], 'attach')

    # Check for and create working directory
    if not os.path.isdir(opts['work_dir']):
        os.makedirs(opts['work_dir'])

    # Check for and create a directory for attachments and images
    if not os.path.isdir(attach_dir):
        os.makedirs(attach_dir)

    if opts['style_file']:
        shutil.copy(opts['style_file'], opts['work_dir'])
        data += """<link rel="stylesheet" type="text/css"
                   href="{}" />\n""".format(os.path.basename(opts['style_file']))

    data += '</head>\n<body>\n'

    if opts['title_class']:
        title_class = ' class="{}"'.format(opts['title_class'])
    else:
        title_class = ''

    if opts['title']:
        data += '<h1{}>{}</h1>\n'.format(title_class, opts['title'])

    if opts['author']:
        data += '<div{}>{}</div>\n'.format(title_class, opts['author'])

    if opts['date']:
        data += '<div{}>{}</div>\n'.format(title_class, opts['date'])

    if opts['copyright']:
        data += '<div{}>{}</div>\n'.format(title_class, opts['copyright'])

    if opts['title'] or opts['author'] or opts['date'] or opts['copyright']:
        data += '<div>\n<pdf:nextpage />\n</div>\n'

    if opts['toc']:
        data += '<h2>Table of Contents</h2>\n<ol>\n'

    entry_body = ''
    entry_ids = []
    for entry in entries:
        # Keep a list of entry IDs that are included in this doc so relative
        # links can be fixed.
        entry_ids.append(entry['id'])

        # Build the table of contents
        if opts['toc']:
            data += '<li><a href="#{}">{}</a></li>\n'.format(entry['id'], entry['title'])
        
        # Get the body of the entry
        entry_body += '<a name="{}"></a><h1>{}</h1>\n'.format(entry['id'], entry['title'])
        #entry_body += '<a name="' + entry['id'] + '<h1>' + entry['title'] + '</h1>\n'
        entry_body += entry['body'] + '\n'

    if opts['toc']:
        data += '</ol>\n<div>\n<pdf:nextpage />\n</div>\n'

    # Put all of the body after the table of contents
    data += entry_body

    # Change to working directory to begin file output
    os.chdir(opts['work_dir'])

    # Save entries
    with open('entries.json', "w") as outfile:
        outfile.write(json.dumps(entries))

    # Make the data a traversable beautifulsoup
    soup = BeautifulSoup(data)

    # Get images and display them inline
    for img in soup.find_all('img'):
        # Handle relative and absolute img src
        src = urlparse.urljoin(opts['url'], img['src'])

        # Normalize the local filename
        srcfile = os.path.join(attach_dir, src.replace('/', '_'))

        # Get this image if not already present
        if not os.path.isfile(srcfile):
            urllib.urlretrieve(src, srcfile)

        # Update the tag for the relative filepath
        img['src'] = srcfile

    # Make relative links to entries and absolute links to entries point to PDF
    # anchors. e.g.
    # http://example.zendes.com/entries/21473796-title
    # /entries/21473796-title
    # TODO /entries/21473796-title#anchor
    r = re.compile('(?:' + opts['url'] + ')?/entries/([0-9]*)-.*')
    for a in soup.find_all('a'):
        try:
            m = r.match(a['href'])
            # modify the link if we have a match and the entry is in the PDF
            if m and int(m.group(1)) in entry_ids:
                a['href'] = '#{}'.format(m.group(1))
        except KeyError:
            # this a tag doesn't have an href. named anchor only?
            pass

    html = soup.encode('utf-8')

    # Save generated html
    with open('entries.html', "w") as outfile:
        outfile.write(html)

    pdf = pisa.CreatePDF(
        SIO.StringIO(html),
        file(opts['output_file'], "wb"),
        encoding = 'utf-8'
    )

    if pdf.err and pdf.log:
        for mode, line, msg, code in pdf.log:
            print "%s in line %d: %s" % (mode, line, msg)

    if pdf.warn:
        print "*** %d WARNINGS OCCURED" % pdf.warn

    os.chdir(startdir)

def config_state(config_file, section, state):
    """
    Update a state (a dictionary) with options from a file parsed by
    ConfigParser for a config [section]. May throw ConfigParser.NoSectionError.

    Handles Boolean values specially by looking at the current state for
    booleans and updating those values specially with ConfigParser.getboolean
    """
    import ConfigParser

    # A list of program state items which are booleans.
    # Kept for convience as they are treated specially when parsing configs.
    state_bools = [k for k, v in state.iteritems() if isinstance(v, bool)]

    # read the config file
    config = ConfigParser.SafeConfigParser()
    config.read(config_file)

    # look for the section, make it a dictionary
    config_dict = dict(config.items(section))

    # Treat bool values specially using getboolean (allows for 1, yes, true)
    for k in state_bools:
        try:
            config_dict[k] = config.getboolean('zdf2pdf', k)
        except ConfigParser.NoOptionError:
            # This config file did not contain this option. Skip it.
            pass

    # update the state with the section dict
    state.update(config_dict)

def main(argv=None):
    import sys, tempfile, argparse
    import ConfigParser

    # Log to stdout
    import logging
    logging.basicConfig()

    # Declare a class for an argparse custom action.
    # Handles converting ascii input from argparse that may contain unicode
    # to a real unicode string.
    class UnicodeStore(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values.decode('utf-8'))

    # Options precedence:
    # program state defaults, which are overridden by
    # ~/.zdf2pdf.cfg [zdf2pdf] section options, which are overridden by
    # command line options, which are overridden by
    # -c CONFIG_FILE [zdf2pdf] section options, which are overridden by
    # ~/.zdf2pdf.cfg [RUN_SECTION] section options, which are overridden by
    # -c CONFIG_FILE [RUN_SECTION] section options
    #
    # Program state, with defaults
    #
    state = {
        'verbose': False,
        'json_file': None,
        'forums': None,
        'entries': None,
        'run_section': None,
        'list_zdf': 'forums',
        'style_file': None,
        'output_file': 'PCLOADLETTER.pdf',
        'title': None,
        'title_class': None,
        'author': None,
        'date': None,
        'copyright': None,
        'toc': True,
        'work_dir': tempfile.gettempdir(),
        'delete': False,
        'url': None,
        'mail': None,
        'password': 'prompt',
        'is_token': False,
    }

    argp = argparse.ArgumentParser(
        description='Make a PDF from Zendesk forums or entries.')
    argp.add_argument('-v', '--verbose', action='store_true',
        help='Verbose output')

    argp.add_argument('-j', action=UnicodeStore, dest='json_file',
        help='Zendesk entries JSON file to convert to PDF')
    argp.add_argument('-f', action=UnicodeStore, dest='forums',
        help='Comma separated Forum IDs to download and convert to PDF')
    argp.add_argument('-e', action=UnicodeStore, dest='entries',
        help='Comma separated Entry IDs to download and convert to PDF')
    argp.add_argument('-r', action=UnicodeStore, dest='run_section',
        help='Run pre-configured section in configuration file')
    argp.add_argument('-l', action=UnicodeStore, dest='list_zdf',
        help="""List a forum's entries by ID and title.  If no forum ID is
        supplied, list forums by ID and title""",
        nargs='?', const=state['list_zdf'], metavar='FORUM_TO_LIST')

    argp.add_argument('-c', action=UnicodeStore, dest='config_file',
        help='Configuration file (overrides ~/.zdf2pdf.cfg)')
    argp.add_argument('-s', action=UnicodeStore, dest='style_file',
        help='Style file (CSS) to <link>')
    argp.add_argument('-o', action=UnicodeStore, dest='output_file',
        help='Output filename (default: PCLOADLETTER.pdf)',
        default=state['output_file'])
    argp.add_argument('-t', action=UnicodeStore, dest='title',
        help='Title to be added to the beginning of the PDF')
    argp.add_argument('-a', action=UnicodeStore, dest='author',
        help='Author line to be added to the beginning of the PDF')
    argp.add_argument('--date', action=UnicodeStore, dest='date',
        help='Date line to be added to the beginning of the PDF')
    argp.add_argument('--copyright', action=UnicodeStore, dest='copyright',
        help='Copyright line to be added to the beginning of the PDF')
    argp.add_argument('--title-class', action=UnicodeStore, dest='title_class',
        help='CSS class to be added to title page elements')
    argp.add_argument('--toc', action='store_true', dest='toc',
        help="Generate a Table of Contents (default: true)")

    argp.add_argument('-w', action=UnicodeStore, dest='work_dir',
        help="""Working directory in which to store JSON output and images
        (default: temp dir)""")
    argp.add_argument('-d', '--delete', action='store_true', dest='delete',
        help="""Delete working directory at program exit
        (default: do not delete)""")

    argp.add_argument('-u', action=UnicodeStore, dest='url',
        help='URL of Zendesk (e.g. https://example.zendesk.com)')
    argp.add_argument('-m', action=UnicodeStore, dest='mail',
        help='E-Mail address for Zendesk login')
    argp.add_argument('-p', action=UnicodeStore, dest='password',
        help='Password for Zendesk login',
        nargs='?', const=state['password'])
    argp.add_argument('-i', '--is-token', action='store_true', dest='is_token',
        help='Is token? Specify if password supplied a Zendesk token')

    # Set argparse defaults with program defaults.
    # Skip password and list_zdf as they are argparse const, not argparse default
    argp.set_defaults(**dict((k, v) for k, v in state.iteritems() if k != 'password' and k != 'list_zdf'))

    # Read ~/.zdf2pdf.cfg [zdf2pdf] section and update argparse defaults
    try:
        config_state(os.path.expanduser('~') + '/.zdf2pdf.cfg', 'zdf2pdf', state)
        # Skip list_zdf because it is not a config file value, not an argparse
        # const value, and we don't want to lose it by overwriting it with None.
        # Password is OK now, because we either have one from the config file or
        # it is still None.
        argp.set_defaults(**dict((k, v) for k, v in state.iteritems() if k != 'list_zdf'))
    except ConfigParser.NoSectionError:
        # -c CONFIG_FILE did not have a [zdf2pdf] section. Skip it.
        pass

    # Parse the command line options
    if argv is None:
        argv = sys.argv
    args = argp.parse_args()

    # Update the program state with command line options
    for k in state.keys():
        state[k] = getattr(args, k)

    # -c CONFIG_FILE given on command line read args.config_file [zdf2pdf], update state
    if args.config_file:
        try:
            config_state(args.config_file, 'zdf2pdf', state)
        except ConfigParser.NoSectionError:
            # -c CONFIG_FILE did not have a [zdf2pdf] section. Skip it.
            pass

    # -r RUN_SECTION given
    if args.run_section:
        section_found = False
        try:
            config_state(os.path.expanduser('~') + '/.zdf2pdf.cfg', args.run_section, state)
            section_found = True
        except ConfigParser.NoSectionError:
            # ~/.zdf2pdf.cfg did not have this section. Hope it's found later.
            pass

        # -c CONFIG_FILE and -r RUN_SECTION given
        if args.config_file:
            try:
                config_state(args.config_file, args.run_section, state)
                section_found = True
            except configparser.NoSectionError:
                # CONFIG_FILE did not have this section.
                pass

        # If the section wasn't found, print an error and exit
        if not section_found:
            print('Error: Run section {} was not found'.format(args.run_section))
            return 1

    if state['entries'] or state['forums'] or state['list_zdf']:
        from zendesk import Zendesk
        if state['url'] and state['mail'] and state['password']:
            zd = Zendesk(state['url'],
                        zendesk_username = state['mail'],
                        zendesk_password = state['password'],
                        use_api_token = state['is_token'])
        else:
            from textwrap import dedent
            msg = dedent("""\
                Error: Need Zendesk config for requested operation. Use -u, -m,
                       -p options or a config file to provide the information.

                Config file (e.g. ~/.zdf2pdf.cfg) should be something like:
                [zdf2pdf]
                url = https://example.zendesk.com
                mail = you@example.com
                password = dneib393fwEF3ifbsEXAMPLEdhb93dw343
                is_token = 1
                """)
            print(msg)
            return 1

    if state['list_zdf'] == 'forums':
        # List available zendesk forums with their IDs and titles and exit
        forums = zd.list_forums()
        for forum in forums:
            print('{} {}'.format(forum['id'], forum['name']))
        return 0

    elif state['list_zdf']:
        # List a zendesk forum's entries with their IDs and titles and exit
        try:
            forum_id = int(state['list_zdf'])
        except ValueError:
            print('Error: Could not convert to integer: {}'.format(state['list_zdf']))
            return 1

        entries = zd.list_entries(forum_id=state['list_zdf'])
        for entry in entries:
            print('{} {}'.format(entry['id'], entry['title']))
        return 0

    # Use an entries file on disk
    if state['json_file']:
        # Get the entries off disk
        with open(state['json_file'], 'r') as infile:
            entries = json.loads(infile.read())
    else:
        entries = []

    # Get the entries from one or more zendesk forums
    if state['forums']:
        try:
            forum_ids = [int(i) for i in state['forums'].split(',')]
            for forum_id in forum_ids:
                entries += zd.list_entries(forum_id=forum_id)
        except ValueError:
            print('Error: Could not convert to integers: {}'.format(state['forums']))
            return 1

    # Get individual entries from zendesk
    if state['entries']:
        try:
            entry_ids = [int(i) for i in state['entries'].split(',')]
            for entry_id in entry_ids:
                entries.append(zd.show_entry(entry_id=entry_id))
        except ValueError:
            print('Error: Could not convert to integers: {}'.format(state['entries']))
            return 1

    if len(entries) == 0:
        # Didn't get entries from any inputs.
        print("Error: Did not receive any entries.")
        return 1

    zdf2pdf(entries, state)

    if state['delete']:
        shutil.rmtree(state['work_dir'])

    return 0

