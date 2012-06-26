"""
zdf2pdf: Create PDFs from Zendesk forums and entries
"""
from __future__ import unicode_literals
import os, shutil, re, textwrap
try:
    import simplejson as json
except:
    import json

def zdf2pdf(entries, opts):
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

    # Add PDF header if given
    if opts['header']:
        data += opts['header'] + '\n'

    if opts['footer']:
        data += opts['footer'] + '\n'

    # Build anything provided that should go on the title page
    if opts['title'] or opts['author'] or opts['date'] or opts['copyright']:
        if opts['title_class']:
            title_class = ' class="{}"'.format(opts['title_class'])
        else:
            title_class = ''

        data += '<div{}>\n'.format(title_class)

        if opts['title']:
            data += '<h1>{}</h1>\n'.format(opts['title'])

        if opts['author']:
            data += '<div>{}</div>\n'.format(opts['author'])

        if opts['date']:
            data += '<div>{}</div>\n'.format(opts['date'])

        if opts['copyright']:
            data += '<div>{}</div>\n'.format(opts['copyright'])

        data += '</div>\n'

    if opts['toc']:
        if opts['toc_class']:
            toc_class = ' class="{}"'.format(opts['toc_class'])
        else:
            toc_class = ''

        data += '<div{}>\n<h2>{}</h2>\n<ol>\n'.format(toc_class, opts['toc_title'])

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
        data += '</ol>\n</div>\n'

    # Put all of the body after the table of contents
    data += entry_body

    # Change to working directory to begin file output
    os.chdir(opts['work_dir'])

    # Save entries
    with open('entries.json', "w") as outfile:
        outfile.write(json.dumps(entries))

    # Make the data a traversable beautifulsoup
    soup = BeautifulSoup(data)

    if opts['pre_width']:
        # Monkey patch TextWrapper for splitting on any whitespace and add
        # splitting on commas. Save the old one for when we're done.
        old_wordsep_simple_re = textwrap.TextWrapper.wordsep_simple_re
        new_wordsep_simple_re = re.compile(r'(\s+|\,)')
        textwrap.TextWrapper.wordsep_simple_re = new_wordsep_simple_re

        w = textwrap.TextWrapper(width=opts['pre_width'],
                replace_whitespace=False, drop_whitespace=False,
                break_on_hyphens=False, break_long_words=True)
        for pre in soup.find_all('pre'):
            pre_str = ''
            try:
                for line in pre.string.splitlines():
                    pre_str += '\n'.join(w.wrap(line)) + '\n'
                pre.string = pre_str
            except AttributeError:
                # pre tag has no content
                pass

        # Put the original wordsep_simple_re back
        textwrap.TextWrapper.wordsep_simple_re = old_wordsep_simple_re

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

    if opts['strip_empty']:
        soup = strip_empty_tags(soup)

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

def strip_empty_tags(soup):
    """
    Strip out tags that do not have any contents. Intended to clean up HTML
    produced by editors. Does not remove self closing tags, empty anchor link
    tags, or xhtml2pdf specific tags.
    """
    emptymatches = re.compile('^(&nbsp;|\s|\n|\r|\t)*$')
    emptytags = soup.findAll(lambda tag: tag.find(True) is None and (tag.string is None or tag.string.strip()=="" or tag.string.strip()==emptymatches) and not tag.isSelfClosing and not (tag.name=='a' and tag.name) and tag.name[0:3] != 'pdf')
    if emptytags and (len(emptytags) != 0):
        for t in emptytags: t.extract()
        #recursive in case removing empty tag creates new empty tag
        strip_empty_tags(soup)
    return soup

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
            config_dict[k] = config.getboolean(section, k)
        except ConfigParser.NoOptionError:
            # This config file did not contain this option. Skip it.
            pass

    # Convert any new strings to full unicode
    for k in [k for k, v in config_dict.iteritems() if isinstance(v, str)]:
        config_dict[k] = config_dict[k].decode('utf-8')

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
        'toc': False,
        'toc_class': None,
        'toc_title': 'Table of Contents',
        'pre_width': None,
        'strip_empty': False,
        'header': None,
        'footer': None,
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
        help='CSS class to be added to title page div')
    argp.add_argument('--toc', action='store_true', dest='toc',
        help="Generate a Table of Contents (default: false)")
    argp.add_argument('--toc-title', action=UnicodeStore, dest='toc_title',
        help="ToC title (default: Table of Contents)")
    argp.add_argument('--toc-class', action=UnicodeStore, dest='toc_class',
        help='CSS class to be added to ToC div')
    argp.add_argument('--pre-width', action=UnicodeStore, dest='pre_width',
        help='Width to wrap contents of <pre></pre> tags.')
    argp.add_argument('--strip-empty', action='store_true', dest='strip_empty',
        help='Strip empty tags. (default: false)')
    argp.add_argument('--header', action=UnicodeStore, dest='header',
        help='HTML header to add to the PDF (see docs)')
    argp.add_argument('--footer', action=UnicodeStore, dest='footer',
        help='HTML footer to add to the PDF (see docs)')

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
        if state['verbose']: print('Reading config file {}'.format(args.config_file))
        try:
            config_state(args.config_file, 'zdf2pdf', state)
        except ConfigParser.NoSectionError:
            # -c CONFIG_FILE did not have a [zdf2pdf] section. Skip it.
            pass

    # -r RUN_SECTION given
    if args.run_section:
        if state['verbose']: print('Searching for {} in ~/.zdf2pdf'.format(args.run_section))
        section_found = False
        try:
            config_state(os.path.expanduser('~') + '/.zdf2pdf.cfg', args.run_section, state)
            section_found = True
            if state['verbose']: print('Found {} in ~/.zdf2pdf'.format(args.run_section))
        except ConfigParser.NoSectionError:
            # ~/.zdf2pdf.cfg did not have this section. Hope it's found later.
            pass

        # -c CONFIG_FILE and -r RUN_SECTION given
        if args.config_file:
            if state['verbose']: print('Searching for {} in {}'.format(args.run_section, args.config_file))
            try:
                config_state(args.config_file, args.run_section, state)
                section_found = True
                if state['verbose']: print('Found {} in {}'.format(args.run_section, args.config_file))
            except ConfigParser.NoSectionError:
                # CONFIG_FILE did not have this section.
                pass

        # If the section wasn't found, print an error and exit
        if not section_found:
            print('Error: Run section {} was not found'.format(args.run_section))
            return 1

    if state['entries'] or state['forums'] or state['list_zdf']:
        from zendesk import Zendesk
        if state['url'] and state['mail'] and state['password']:
            if state['verbose']:
                print('Configuring Zendesk with:\n'
                      'url: {}\n'
                      'mail: {}\n'
                      'password: (hidden)\n'
                      'is_token: {}\n'.format( state['url'], state['mail'],
                                             repr(state['is_token']) ))
            zd = Zendesk(state['url'],
                        zendesk_username = state['mail'],
                        zendesk_password = state['password'],
                        use_api_token = state['is_token'])
        else:
            msg = textwrap.dedent("""\
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

    # All config options are in, state is set.
    # Handle any last minute type checking or setting
    if state['pre_width']:
        try:
            state['pre_width'] = int(state['pre_width'])
        except TypeError:
            print('Could not convert pre_width {} to integer'.format( repr(state['pre_width']) ))
            return 1

    # Log the state
    if state['verbose']:
        print('Running with program state:')
        for k, v in state.iteritems():
            print('{} {}'.format(k, repr(v)))

    if state['list_zdf'] == 'forums':
        # List available zendesk forums with their IDs and titles and exit
        if state['verbose']: print('Listing all forums')
        forums = zd.list_forums()
        for forum in forums:
            print('{} {}'.format(forum['id'], forum['name']))
        return 0

    elif state['list_zdf']:
        if state['verbose']: print('Listing all entries in forum {}'.format(state['list_zdf']))
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
        if state['verbose']: print('Reading entries from {}'.format(state['json_file']))
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
                if state['verbose']: 
                    print('Obtaining entries from forum {}'.format(forum_id))
                entries += zd.list_entries(forum_id=forum_id)
        except ValueError:
            print('Error: Could not convert to integers: {}'.format(state['forums']))
            return 1

    # Get individual entries from zendesk
    if state['entries']:
        try:
            entry_ids = [int(i) for i in state['entries'].split(',')]
            for entry_id in entry_ids:
                if state['verbose']: 
                    print('Obtaining entry {}'.format(entry_id))
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

