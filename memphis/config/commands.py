""" paste commands """
import argparse, textwrap
import StringIO, ConfigParser
from collections import OrderedDict

from memphis import config
from memphis.config import api, directives


grpTitleWrap = textwrap.TextWrapper(
    initial_indent='* ',
    subsequent_indent='  ')

grpDescriptionWrap = textwrap.TextWrapper(
    initial_indent='    ',
    subsequent_indent='    ')

nameWrap = textwrap.TextWrapper(
    initial_indent='  - ',
    subsequent_indent='    ')

nameTitleWrap = textwrap.TextWrapper(
    initial_indent='       ',
    subsequent_indent='       ')

nameDescriptionWrap = textwrap.TextWrapper(
    initial_indent=' * ',
    subsequent_indent='')


def settingsCommand():
    args = SettingsCommand.parser.parse_args()
    cmd = SettingsCommand(args)
    cmd.run()


class SettingsCommand(object):
    """ 'settings' paste command"""

    parser = argparse.ArgumentParser(description="Memphis settings management")
    parser.add_argument('-a', '--all', action="store_true",
                        dest='all',
                        help = 'List all registered settings')
    parser.add_argument('-l', '--list',
                        dest='section', default='',
                        help = 'List registered settings')
    parser.add_argument('-p', '--print', action="store_true",
                        dest='printcfg',
                        help = 'Print default settings in ConfigParser format')

    def __init__(self, args):
        self.options = args

    def run(self):
        # load all memphis packages
        config.initialize()

        # print defaults
        if self.options.printcfg:
            data = config.Settings.export(True)

            parser = ConfigParser.ConfigParser(dict_type=OrderedDict)
            items = data.items()
            items.sort()
            for key, val in items:
                parser.set(ConfigParser.DEFAULTSECT, key, val)

            fp = StringIO.StringIO()
            try:
                parser.write(fp)
            finally:
                pass

            print fp.getvalue()
            return

        if self.options.all:
            section = ''
        else:
            section = self.options.section

        # print description
        groups = config.Settings.items()
        groups.sort()

        for name, group in groups:
            if section and name != section:
                continue

            print ''
            title = group.title or name

            print grpTitleWrap.fill(title)
            if group.description:
                print grpDescriptionWrap.fill(group.description)

            print
            for node in group.schema:
                default = '<required>' if node.required else node.default
                print nameWrap.fill(
                    '%s.%s: %s (%s: %s)'%(
                        name, node.name, node.title,
                        node.typ.__class__.__name__, default))

                print nameTitleWrap.fill(node.description)
                print
