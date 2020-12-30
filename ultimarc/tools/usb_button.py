#
# This file is subject to the terms and conditions defined in the
# file 'LICENSE', which is part of this source code package.
#
# Tool for managing Ultimarc USB Button devices.
#
import json
import logging
import os
import random
import re
import sys

from ultimarc import translate_gettext as _
from ultimarc.tools import ToolContextManager, ToolEnvironmentObject

_logger = logging.getLogger('ultimarc')

# Tool_cmd and tool_desc name are required.
# Remember to add/update bash completion in 'tools.bash'
tool_cmd = _('usb-button')
tool_desc = _('manage usb-button devices.')

_RGB_STRING_REGEX = "^([0-9]{1,3}),([0-9]{1,3}),([0-9]{1,3})+$"


class USBButtonClass(object):
    """ Tool class for managing USB buttons. """

    def __init__(self, args, env: ToolEnvironmentObject):
        """
        :param args: command line arguments.
        :param env: tool environment information, see: gcp_initialize().
        """
        self.args = args
        self.env = env

    def run(self):
        """
        Main program process
        :return: Exit code value
        """
        # Get devices we want to work with based on filters.
        devices = [dev for dev in
                   self.env.devices.filter(class_id='usb-button', bus=self.args.bus, address=self.args.address)]

        if not devices:
            _logger.error(_('No USB button devices found, aborting'))
            return -1

        # See if we are setting a color from the command line args.
        if self.args.set_color:
            match = re.match(_RGB_STRING_REGEX, self.args.set_color)
            for dev in devices:
                with dev as dev_h:
                    dev_h.set_color(match.groups()[0], match.groups()[1], match.groups()[2])

        # Return the current color RGB values.
        elif self.args.get_color:
            for dev in devices:
                with dev as dev_h:
                    red, green, blue = dev_h.get_color()
                    if red:
                        _logger.info(f'{dev.dev_key} ({dev.bus},{dev.address}): ' +
                                     _('Color') + f': RGB({red},{green},{blue}).')

        # Set a random RGB color.
        elif self.args.set_random_color:
            for dev in devices:
                red = random.randrange(255)
                green = random.randrange(255)
                blue = random.randrange(255)
                with dev as dev_h:
                    dev_h.set_color(red, green, blue)
                _logger.info(f'{dev.dev_key} ({dev.bus},{dev.address}): ' +
                             _('randomly set button color to') + f' RGB({red},{green},{blue}).')

        # Apply a usb button config.
        elif self.args.set_config:
            for dev in devices:
                with dev as dev_h:
                    dev_h.set_config(self.args.set_config)
                    _logger.info(f'{dev.dev_key} ({dev.bus},{dev.address}): ' +
                                 _('configuration successfully applied to device.'))

        return 0


def run():
    # Set global debug value and setup application logging.
    ToolContextManager.initialize_logging(tool_cmd)
    parser = ToolContextManager.get_argparser(tool_cmd, tool_desc)

    # --set-color --get-color --load-config --export-config
    parser.add_argument('--set-color', help=_('set usb button color with RGB value'), type=str, default=None)
    parser.add_argument('--set-random-color', help=_('randomly set usb button color'), default=False,
                        action='store_true')
    parser.add_argument('--get-color', help=_('output current usb button color RGB value'), default=False,
                        action='store_true')
    parser.add_argument('--set-config', help=_('Set button config from config file.'), type=str, default=None)

    args = parser.parse_args()

    num_args = sum([bool(args.set_color), args.set_random_color, args.get_color, bool(args.set_config)])
    if num_args == 0:
        _logger.warning(_('Nothing to do.'))
        return 0
    if num_args > 1:
        # Enhance this check and provide better feedback on which arguments are mutually exclusive.
        _logger.error(_('More than one mutually exclusive argument specified.'))
        return -1

    if args.set_color:
        if not re.match(_RGB_STRING_REGEX, args.set_color):
            _logger.error(_('Invalid RGB value found for --set-color argument.'))
            return -1

    if args.set_config:
        # Always force absolute path for config files.
        args.set_config = os.path.abspath(args.set_config)
        if not os.path.exists(args.set_config):
            _logger.error(_('Unable to find configuration file specified in argument.'))
            return -1

    with ToolContextManager(tool_cmd, args) as tool_env:
        process = USBButtonClass(args, tool_env)
        exit_code = process.run()
        return exit_code


# --- Main Program Call ---
if __name__ == "__main__":
    sys.exit(run())