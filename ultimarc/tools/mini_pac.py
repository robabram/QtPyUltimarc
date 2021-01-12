#
# This file is subject to the terms and conditions defined in the
# file 'LICENSE', which is part of this source code package.
#
# Template for Ultimarc CLI tools.
#
import logging
import sys

from ultimarc import translate_gettext as _
from ultimarc.devices import DeviceClassID
from ultimarc.tools import ToolContextManager, ToolEnvironmentObject

_logger = logging.getLogger('ultimarc')

# Tool_cmd and tool_desc name are required.
# Remember to add/update bash completion in 'tools.bash'
tool_cmd = _('mini-pac')
tool_desc = _('manage mini-pac devices')


class MiniPACClass(object):
    """ Tool class for managing Mini-PAC devices """

    def __init__(self, args, tool_env: ToolEnvironmentObject):
        """
        :param args: command line arguments.
        :param tool_env: tool environment information, see: gcp_initialize().
        """
        self.args = args
        self.tool_env = tool_env

    def run(self):
        """
        Main program process
        :return: Exit code value
        """
        # TODO: write program main process here after setting 'tool_cmd' and 'tool_desc'...

        # Get devices we want to work with based on filters.
        devices = [dev for dev in
                   self.tool_env.devices.filter(class_id=DeviceClassID.MiniPac, bus=self.args.bus,
                                                address=self.args.address)]

        if not devices:
            _logger.error(_('No Mini-PAC devices found, aborting'))
            return -1

        for dev in devices:
            with dev as dev_h:
                dev_h.get_device_configuration()

        print('hi')
        return 0


def run():
    # Set global debug value and setup application logging.
    ToolContextManager.initialize_logging(tool_cmd)
    parser = ToolContextManager.get_argparser(tool_cmd, tool_desc)

    # TODO:  Setup additional program arguments here.
    args = parser.parse_args()

    with ToolContextManager(tool_cmd, args) as tool_env:
        process = MiniPACClass(args, tool_env)
        exit_code = process.run()
        return exit_code


# --- Main Program Call ---
if __name__ == "__main__":
    sys.exit(run())
