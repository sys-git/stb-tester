'''
Created on 31 Oct 2012

@author: YouView
'''

from ConfigParser import SafeConfigParser
import os

def loadDefaultArgs(tool):
    confFile = SafeConfigParser()
    confFile.add_section('global')
    confFile.add_section(tool)
    """"
    When run from the installed location (as `stbt run`), will read config
    from $SYSCONFDIR/stbt/stbt.conf (see `stbt.in`); when run from the source
    directory (as `stbt-run`) will read config from the source directory.
    """
    system_config = os.environ.get('STBT_SYSTEM_CONFIG', os.path.join(os.getcwd(), 'stbt.conf'))
    files_read = confFile.read([
        system_config,
        # User config: ~/.config/stbt/stbt.conf, as per freedesktop's base directory specification:
        '%s/stbt/stbt.conf' % os.environ.get('XDG_CONFIG_HOME', '%s/.config'%os.environ['HOME']),
        # Config files specific to the test suite / test run:
        os.environ.get('STBT_CONFIG_FILE', ''),
        ])
    assert(system_config in files_read)
    items = confFile.items('global')
    #    Change hyphen to underscore:
    for index, (item, value) in enumerate(items):
        item = item.replace("-", "_")
        items[index] = (item, value)
    return dict(items, **dict(confFile.items(tool)))
