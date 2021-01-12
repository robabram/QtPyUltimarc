#
# This file is subject to the terms and conditions defined in the
# file 'LICENSE', which is part of this source code package.
#
# Base class for all USB device classes.
#

import ctypes as ct
import json
import logging
import os
from json import JSONDecodeError

from jsonschema import validate, ValidationError
import libusb as usb

from ultimarc import translate_gettext as _

REPORT_TYPE_OUT = 200

_logger = logging.getLogger('ultimarc')

ULTIMARC_MACRO_SIZE = 85


class UltimarcConfigurationStruct(ct.Structure):
    """ Defines the bit values for the configuration byte """
    _fields_ = [
        ('high_current_output', ct.c_int, 1),
        ('accelerometer', ct.c_int, 1),
        ('paclink', ct.c_int, 1),
        ('debounce', ct.c_int, 2),
        ('expand_interface', ct.c_int, 1),
        ('blanks', ct.c_int, 2)
    ]


class UltimarcByteStruct(ct.Structure):
    """ 49 bytes structure """
    _fields_ = [
        ('byte_1', ct.c_ubyte),
        ('byte_2', ct.c_ubyte),
        ('byte_3', ct.c_ubyte),
        ('byte_4', ct.c_ubyte),
        ('byte_5', ct.c_ubyte),
        ('byte_6', ct.c_ubyte),
        ('byte_7', ct.c_ubyte),
        ('byte_8', ct.c_ubyte),
        ('byte_9', ct.c_ubyte),
        ('byte_10', ct.c_ubyte),
        ('byte_11', ct.c_ubyte),
        ('byte_12', ct.c_ubyte),
        ('byte_13', ct.c_ubyte),
        ('byte_14', ct.c_ubyte),
        ('byte_15', ct.c_ubyte),
        ('byte_16', ct.c_ubyte),
        ('byte_17', ct.c_ubyte),
        ('byte_18', ct.c_ubyte),
        ('byte_19', ct.c_ubyte),
        ('byte_20', ct.c_ubyte),
        ('byte_21', ct.c_ubyte),
        ('byte_22', ct.c_ubyte),
        ('byte_23', ct.c_ubyte),
        ('byte_24', ct.c_ubyte),
        ('byte_25', ct.c_ubyte),
        ('byte_26', ct.c_ubyte),
        ('byte_27', ct.c_ubyte),
        ('byte_28', ct.c_ubyte),
        ('byte_29', ct.c_ubyte),
        ('byte_30', ct.c_ubyte),
        ('byte_31', ct.c_ubyte),
        ('byte_32', ct.c_ubyte),
        ('byte_33', ct.c_ubyte),
        ('byte_34', ct.c_ubyte),
        ('byte_35', ct.c_ubyte),
        ('byte_36', ct.c_ubyte),
        ('byte_37', ct.c_ubyte),
        ('byte_38', ct.c_ubyte),
        ('byte_39', ct.c_ubyte),
        ('byte_40', ct.c_ubyte),
        ('byte_41', ct.c_ubyte),
        ('byte_42', ct.c_ubyte),
        ('byte_43', ct.c_ubyte),
        ('byte_44', ct.c_ubyte),
        ('byte_45', ct.c_ubyte),
        ('byte_46', ct.c_ubyte),
        ('byte_47', ct.c_ubyte),
        ('byte_48', ct.c_ubyte),
        ('byte_49', ct.c_ubyte)
    ]


class UltimarcStruct(ct.Structure):
    """ Defines the structure used be most Ultimarc boards """
    _fields_ = [
        ('header', ct.c_ubyte),
        ('led_packet', ct.c_ubyte),
        ('quadrature', ct.c_ubyte),
        ('configuration', UltimarcConfigurationStruct),
        ('codes', UltimarcByteStruct),  # 5 - 54 (49 bytes)
        ('shifted_codes', UltimarcByteStruct),  # 55 - 104  (49 bytes)
        ('analog_axis_calibration', UltimarcByteStruct),  # 105 - 154 (49 bytes)
        ('axis_offset_1', ct.c_ubyte),  # byte 155
        ('axis_offset_2', ct.c_ubyte),  # byte 156
        ('axis_offset_3', ct.c_ubyte),  # byte 157
        ('axis_offset_4', ct.c_ubyte),  # byte 158
        ('axis_offset_5', ct.c_ubyte),  # byte 159
        ('axis_offset_6', ct.c_ubyte),  # byte 160
        ('axis_offset_7', ct.c_ubyte),  # byte 161
        ('axis_offset_8', ct.c_ubyte),  # byte 162
        ('axis_scale_1', ct.c_ubyte),  # byte 163
        ('axis_scale_2', ct.c_ubyte),  # byte 164
        ('axis_scale_3', ct.c_ubyte),  # byte 165
        ('axis_scale_4', ct.c_ubyte),  # byte 166
        ('axis_scale_5', ct.c_ubyte),  # byte 167
        ('axis_scale_6', ct.c_ubyte),  # byte 168
        ('axis_scale_7', ct.c_ubyte),  # byte 169
        ('axis_scale_8', ct.c_ubyte),  # byte 170
        ('macros', ct.c_ubyte * ULTIMARC_MACRO_SIZE)  # bytes 171 - 256
    ]


def usb_error(code, msg, debug=False):
    """
    Return string containing error code in string format.
    :param code: integer.
    :param msg: string, additional error message
    :param debug: boolean, if False show error else show debug statement.
    """
    if debug is False:
        _logger.error(f'{usb.error_name(code).decode("utf-8")} ({code}): ' + msg)
    else:
        _logger.debug(f'{usb.error_name(code).decode("utf-8")} ({code}): ' + msg)


class USBDeviceHandle:
    """
    Represents an opened USB device.  Do not instantiate directly, use object obtained
    from a USBDeviceInfo object using 'with' command.  IE 'with USBDeviceInfo as handle:'
    """
    __libusb_dev__ = None
    __libusb_dev_handle__ = None
    __libusb_dev_desc__ = None

    dev_key = None
    class_id = 'unset'  # Used to match/filter devices. Override in child classes.
    class_descr = 'unset'  # Override in child classes.

    discriptor_fields = None  # List of available device property fields.

    def __init__(self, dev_handle, dev_key):
        self.__libusb_dev__ = usb.get_device(dev_handle)
        self.__libusb_dev_handle__ = dev_handle
        self.dev_key = dev_key
        self.discriptor_fields = self._get_descriptor_fields()

    def _get_descriptor_fields(self):
        """
        Return a list of available descriptor property fields.
        :return: list of strings.
        """
        if not self.__libusb_dev_desc__:
            self.__libusb_dev_desc__ = usb.device_descriptor()
            usb.get_device_descriptor(self.__libusb_dev__, ct.byref(self.__libusb_dev_desc__))
        fields = sorted([fld[0] for fld in self.__libusb_dev_desc__._fields_])

        return fields

    def get_descriptor_value(self, prop_field):
        if prop_field and prop_field in self.discriptor_fields:
            return getattr(self.__libusb_dev_desc__, prop_field)
        raise ValueError(_('Invalid descriptor property field name') + f' ({prop_field})')

    def get_descriptor_string(self, index):
        """
        Return the String value of a device descriptor property.
        :param index: integer
        :return: String or None
        """
        buf = ct.create_string_buffer(1024)
        ret = usb.get_string_descriptor_ascii(self.__libusb_dev_handle__, index, ct.cast(buf, ct.POINTER(ct.c_ubyte)),
                                              ct.sizeof(buf))
        if ret > 0:
            result = buf.value.decode('utf-8')
            return result

        usb_error(ret, _('failed to get descriptor property field string value.'), debug=True)
        return None

    # TODO: Write function(s) to get device capabilities and other information based on this code.
    #      https://github.com/karpierz/libusb/blob/master/examples/testlibusb.py

    def _make_control_transfer(self, request_type, b_request, w_value, w_index, data, size, timeout=2000):
        """
        Read/Write data from USB device.
        :param request_type: Request type value. Combines direction, type and recipient enum values.
        :param b_request: Request field for the setup packet
        :param w_value: Value field for the setup packet.
        :param w_index: Index field for the setup packet
        :param data: ctypes structure class.
        :param size: data_size of data.
        :return: True if successful otherwise False.
        """
        data_ptr = ct.cast(data, ct.POINTER(ct.c_ubyte)),  # ct.POINTER(ct.c_ubyte)
        ret = usb.control_transfer(
            self.__libusb_dev_handle__,  # ct.c_char_p
            request_type,  # ct.c_uint8
            # TODO: Understand these next 3 arguments better.
            b_request,  # ct.c_uint8
            w_value,  # ct.c_uint16
            w_index,  # ct.c_uint16
            data_ptr[0],
            ct.c_uint16(size),  # ct.c_uint16
            timeout)  # ct.c_uint32

        if ret >= 0:
            direction = _('Read') if request_type & usb.LIBUSB_ENDPOINT_IN else _('Write')
            _logger.debug(f'{direction} {size} ' + _('bytes from device').format(size) + f' {self.dev_key}.')
            return True

        usb_error(ret, _('Failed to communicate with device') + f' {self.dev_key}.')
        return False

    def write(self, b_request, report_id, w_index, msg_size=None, data=None, data_size=None, request_type=usb.LIBUSB_REQUEST_TYPE_CLASS,
              recipient=usb.LIBUSB_RECIPIENT_INTERFACE, report_type=REPORT_TYPE_OUT):
        """
        Write data from USB device.
        :param b_request: Request field for the setup packet
        :param report_id: Part of the value field for the setup packet.
        :param w_index: Index field for the setup packet
        :param msg_size: The size each message.
        :param data: ctypes structure class.
        :param data_size: size of data.
        :param request_type: Request type enum value.
        :param recipient: Recipient enum value.
        :param report_type: Part of the value field for the setup packet.
        :return: True if successful otherwise False.
        """

        class Payload(ct.Structure):
            """ Basic payload structure """
            _fields = [
                ('report_id', ct.c_uint8),
                ('b1', ct.c_uint8),
                ('b2', ct.c_uint8),
                ('b3', ct.c_uint8),
                ('b4', ct.c_uint8)
            ]

        # Combine direction, request type and recipient together.
        request_type = usb.LIBUSB_ENDPOINT_OUT | request_type | recipient
        # Combine Report_Type and Report_ID together.
        w_value = report_type | report_id

        # Figure out how big of a message we are sending
        message_offset = 0
        # payload = Payload()
        payload = (ct.c_ubyte*5)(0)
        payload[0] = report_id
        pos = 0

        _logger.debug(_('Writing the following data:'))
        while pos < data_size:
            # for x in range(1, msg_size + 1):
            #     payload[x] = data.value[pos + (x-1)]

            ct.memmove(ct.addressof(payload)+1, ct.byref(data, pos), msg_size if msg_size <= 4 else 4)

            _logger.debug(_(' '.join(hex(x) for x in payload)))

            payload_ptr = ct.byref(payload) if report_id else ct.byref(payload, 1)
            self._make_control_transfer(request_type, b_request, w_value, w_index, payload_ptr, ct.sizeof(payload))
            pos += msg_size

    def read(self, b_request, w_value, w_index, data=None, size=None, request_type=usb.LIBUSB_REQUEST_TYPE_CLASS,
             recipient=usb.LIBUSB_RECIPIENT_INTERFACE):
        """
        Read data from USB device.
        :param b_request: Request field for the setup packet
        :param w_value: Value field for the setup packet.
        :param w_index: Index field for the setup packet
        :param data: ctypes structure class.
        :param size: data_size of data.
        :param request_type: Request type enum value.
        :param recipient: Recipient enum value.
        :return: True if successful otherwise False.
        """
        # Combine direction, request type and recipient together.
        request_type = usb.LIBUSB_ENDPOINT_IN | request_type | recipient
        # we need to add 8 extra bytes to the data buffer for read requests.
        return self._make_control_transfer(request_type, b_request, w_value, w_index, data, size)

    def load_config_schema(self, schema_file):
        """
        Load the requested schema file.
        :param schema_file: Schema file name only, no path included.
        :return: schema dict.
        """
        schema_paths = ['../schemas', './schemas', './ultimarc/schemas']
        schema_path = None

        for path in schema_paths:
            schema_path = os.path.abspath(os.path.join(path, schema_file))
            if os.path.exists(schema_path):
                break

        if not schema_path:
            _logger.error(_('Unable to locate schema directory.'))
            return None

        with open(schema_path) as h:
            return json.loads(h.read())

    def validate_config(self, config, schema_file):
        """
        Validate a configuration dict against a schema file.
        :param config: dict
        :param schema_file: relative or abspath of schema.
        :return: True if valid otherwise False.
        """
        schema = self.load_config_schema(schema_file)
        if not schema:
            return False

        try:
            validate(config, schema)
        except ValidationError as e:
            _logger.error(_('Configuration file did not validate against config schema.'))
            return False

        return True

    def validate_config_base(self, config_file, resource_types):
        """
        Validate the configuration file against the base schema.
        :param config_file: Absolute path to configuration json file.
        :param resource_types: list of strings representing valid 'resourceType' values.
        :return: config dict.
        """
        # Read the base schema, all json configs must validate against this schema.
        base_schema = self.load_config_schema('base.schema')
        if not base_schema:
            return None

        try:
            with open(config_file) as h:
                config = json.loads(h.read())
        except JSONDecodeError:
            _logger.error(_('Configuration file is not valid JSON.'))
            return None

        try:
            validate(config, base_schema)
        except ValidationError as e:
            _logger.error(_('Configuration file did not validate against the base schema.') + f'\n{e}')
            return None

        if config['resourceType'] not in resource_types:
            valid_types = ",".join(resource_types)
            _logger.error(_('Resource type does not match accepted types') + f' ({valid_types}).')
            return None

        return config
