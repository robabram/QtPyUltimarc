#
# This file is subject to the terms and conditions defined in the
# file 'LICENSE', which is part of this source code package.
#
import ctypes as ct
import json
import logging
import os

from jsonschema import validate, ValidationError

from ultimarc import translate_gettext as _
from ultimarc.devices._device import USBDeviceHandle as _USBDevice


_logger = logging.getLogger('ultimarc')


# TODO: What do these value mean?
USBB_GET_COLOR = ct.c_uint8(0x01)
USBB_SET_COLOR = ct.c_uint8(0x09)
USBButtonWValue = ct.c_uint16(0x0200)
USBButtonWIndex = ct.c_uint16(0x0)


class USBButtonColorStruct(ct.Structure):
    """ Defines RGB color values for USB button device """
    _fields_ = [
        ('target', ct.c_uint8),  # Must always be 0x01.
        ('red', ct.c_uint8),
        ('green', ct.c_uint8),
        ('blue', ct.c_uint8)
    ]


class USBButtonDevice(_USBDevice):
    """
    Manage a USB Button device
    """
    class_id = 'usb-button'  # Used to match/filter devices.
    class_descr = _('USB Button')

    def set_color(self, red, green, blue):
        """
        Set USB button color.
        :param red: integer between 0 and 255
        :param green: integer between 0 and 255
        :param blue: integer between 0 and 255
        :return: True if successful otherwise False.
        """
        for color in [red, green, blue]:
            if not isinstance(color, int) or not 0 <= color <= 255:
                raise ValueError(_('Color argument value is invalid'))

        data = USBButtonColorStruct(0x01, red, green, blue)
        return self.write(USBB_SET_COLOR, USBButtonWValue, USBButtonWIndex, data, ct.sizeof(data))

    def get_color(self):
        """
        Return the current USB button RGB color values.
        :return: (Integer, Integer, Integer) or None
        """
        data = USBButtonColorStruct()
        for x in range(20):
            ret = self.read(USBB_GET_COLOR, USBButtonWValue, USBButtonWIndex, data, ct.sizeof(data))
            if ret:
                return data.red, data.green, data.blue
            _logger.error(_('Failed to read color data from usb button.'))
        return None, None, None

    def set_config(self, config_file):
        """
        Write the configuration file to the device.
        :param config_file: Absolute path to configuration json file.
        :return: True if successful otherwise False.
        """
        # List of possible 'resourceType' values in the config file for a USB button.
        resource_types = ['usb-button-color']

        # Validate against the base schema.
        config = self.validate_config_base(config_file, resource_types)
        if not config:
            return False

        if config['deviceClass'] != 'usb-button':
            _logger.error(_('Configuration device class is not "usb-button".'))
            return False

        # Determine which config resource type we have.
        if config['resourceType'] == 'usb-button-color':
            if not self.validate_config(config, '../schemas/usb-button-color.schema'):
                return False
            c = config['colorRGB']
            data = USBButtonColorStruct(0x01, c['red'], c['green'], c['blue'])
            return self.write(USBB_SET_COLOR, USBButtonWValue, USBButtonWIndex, data, ct.sizeof(data))

        return False