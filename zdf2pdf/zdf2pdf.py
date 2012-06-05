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

def main(argv=None):
    import os, sys, tempfile, argparse
    import ConfigParser as configparser

    # Log to stdout
    import logging
    logging.basicConfig()

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

    argp.add_argument('-j', action='store', dest='json_file',
        help='Zendesk entries JSON file to convert to PDF')
    argp.add_argument('-f', action='store', dest='forums',
        help='Comma separated Forum IDs to download and convert to PDF')
    argp.add_argument('-e', action='store', dest='entries',
        help='Comma separated Entry IDs to download and convert to PDF')
    argp.add_argument('-r', action='store', dest='run_section',
        help='Run pre-configured section in configuration file')
    argp.add_argument('-l', action='store', dest='list_zdf',
        help="""List a forum's entries by ID and title.  If no forum ID is
        supplied, list forums by ID and title""",
        nargs='?', const=state['list_zdf'], metavar='FORUM_TO_LIST')

    argp.add_argument('-c', action='store', dest='config_file',
        help='Configuration file (overrides ~/.zdf2pdf.cfg)')
    argp.add_argument('-s', action='store', dest='style_file',
        help='Style file (CSS) to <link>')
    argp.add_argument('-o', action='store', dest='output_file',
        help='Output filename (default: PCLOADLETTER.pdf)',
        default=state['output_file'])
    argp.add_argument('-t', action='store', dest='title',
        help='Title to be added to the beginning of the PDF')

    argp.add_argument('-w', action='store', dest='work_dir',
        help="""Working directory in which to store JSON output and images
        (default: temp dir)""")
    argp.add_argument('-d', '--delete', action='store_true', dest='delete',
        help="""Delete working directory at program exit
        (default: do not delete)""")

    argp.add_argument('-u', action='store', dest='url',
        help='URL of Zendesk (e.g. https://example.zendesk.com)')
    argp.add_argument('-m', action='store', dest='mail',
        help='E-Mail address for Zendesk login')
    argp.add_argument('-p', action='store', dest='password',
        help='Password for Zendesk login',
        nargs='?', const=state['password'])
    argp.add_argument('-i', '--is-token', action='store_true', dest='is_token',
        help='Is token? Specify if password supplied a Zendesk token')

    # Set argparse defaults with program defaults.
    # Skip password and list_zdf as they are const, not default
    argp.set_defaults(**dict((k, v) for k, v in state.iteritems() if k is not 'password' and k is not 'list_zdf'))

    # Read ~/.zdf2pdf.cfg [zdf2pdf] section and update argparse defaults
    config = configparser.SafeConfigParser()
    config.read(os.path.expanduser('~') + '/.zdf2pdf.cfg')
    try:
        argp.set_defaults(**dict(config.items('zdf2pdf')))
    except:
        pass

    # Parse the command line and update program state
    if argv is None:
        argv = sys.argv
    args = argp.parse_args()
    for k in state.keys():
        state[k] = getattr(args, k)

    # If -c given on command line read args.config_file [zdf2pdf], update state
    if args.config_file:
        cmd_line_config = configparser.SafeConfigParser()
        cmd_line_config.read(args.config_file)
        cmd_line_config_dict = dict(cmd_line_config.items('zdf2pdf'))
        for k in state.keys():
            try:
                state[k] = cmd_line_config_dict[k]
            except:
                pass
        # Treat bool values specially using getboolean (allows for 1, yes, true)
        for k in [k for k, v in cmd_line_config_dict.iteritems() if isinstance(v, bool)]:
            try:
                state[k] = cmd_line_config.getboolean('zdf2pdf', k)
            except:
                pass

    # If -r given, update state with [RUN_SECTION] from config and 
    # cmd_line_config, if they exist
    if args.run_section:
        config_dict = dict(config.items(args.run_section))
        for k in state.keys():
            try:
                state[k] = config_dict[k]
            except:
                pass
        # Treat bool values specially using getboolean (allows for 1, yes, true)
        for k in [k for k, v in config_dict.iteritems() if isinstance(v, bool)]:
            try:
                state[k] = config.getboolean(args.run_section, k)
            except:
                pass

        if args.config_file:
            cmd_line_config_dict = dict(cmd_line_config.items(args.run_section))
            for k in state.keys():
                try:
                    state[k] = cmd_line_config_dict[k]
                except:
                    pass
            # Treat bool values specially using getboolean (allows for 1, yes, true)
            for k in [k for k, v in cmd_line_config_dict.iteritems() if isinstance(v, bool)]:
                try:
                    state[k] = cmd_line_config.getboolean(args.run_section, k)
                except:
                    pass

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
            print(str(forum['id']) + ' ' + forum['name'])
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
            print(str(entry['id']) + ' ' + entry['title'])
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

    zdf2pdf(entries=entries, filename=state['output_file'],
            title=state['title'], style=state['style_file'])
    return 0

