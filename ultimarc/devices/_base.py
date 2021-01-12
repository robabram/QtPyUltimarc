#
# This file is subject to the terms and conditions defined in the
# file 'LICENSE', which is part of this source code package.
#
# http://libusb.sourceforge.net/api-1.0/libusb_api.html
#
import ctypes as ct
from enum import Enum
import logging
import traceback

import libusb as usb

from ultimarc import translate_gettext as _
from ultimarc.devices._device import usb_error
from ultimarc.devices.usb_button import USBButtonDevice
from ultimarc.devices.aimtrak import AimTrakDevice
from ultimarc.devices.mini_pac import MiniPACDevice

_logger = logging.getLogger('ultimarc')


# Device Class lookups are based on first 3 digits of product id.
_USB_PRODUCT_CLASSES = {
    'd209:120': USBButtonDevice,
    'd209:160': AimTrakDevice,
    'd209:044': MiniPACDevice
}

# USB key values for every USB device.
USB_PRODUCT_DESCRIPTIONS = {
    'd209:1200': 'USB button',
    'd209:1601': 'Aimtrak Lightgun #1',
    'd209:1602': 'Aimtrak Lightgun #2',
    'd209:1603': 'Aimtrak Lightgun #3',
    'd209:1604': 'Aimtrak Lightgun #4',
    'd209:0440': 'Mini-PAC'
}


class DeviceClassID(Enum):
    """ Device class id values, used in schemas and tools for filtering devices by class. """
    USBButton = 'usb-button'
    AimTrak = 'aimtrak'
    MiniPac = 'mini-pac'


#
# USB device custom exception classes.
#
class USBDeviceNotFoundError(Exception):
    """ Device was not found when trying to open it. """
    def __init__(self, dev_key, message=_('Device was not found when trying to open it.')):
        self.dev_key = dev_key
        self.message = message
        super().__init__(f'{dev_key}: {message}')


class USBDeviceClaimInterfaceError(Exception):
    """ Failed to claim USB device interface. """
    def __init__(self, dev_key, message=_('Failed to claim USB device interface.')):
        self.dev_key = dev_key
        self.message = message
        super().__init__(f'{dev_key}: {message}')


class USBDeviceInfo:
    """
    Represents information about a single USB device found on the local system.
    """
    # Properties for Context Manager use only.
    __dev_handle__ = None  # Handle set by usb.open().
    __dev_list__ = None  # Only use this in the __enter__ and __exit__ methods.
    __dev_handle_obj__ = None  # USBDeviceHandle object.
    __dev_class__ = None  # Device class, based on USB_PRODUCT_CATEGORY lookup.

    dev_key = None
    class_id = ''  # Used to match config/schemas to devices.
    class_descr = ''
    
    vendor_id = None
    product_id = None
    bus = None
    address = None
    path = ''
    product_name = ''

    def __init__(self, tmp_dev, device_desc):
        """
        :param tmp_dev: temporary device handle, do not save.
        :param device_desc: USB device descriptor.
        """
        self.__desc__ = device_desc
        self.vendor_id = device_desc.idVendor
        self.product_id = device_desc.idProduct
        self.bus = usb.get_bus_number(tmp_dev)
        self.address = usb.get_device_address(tmp_dev)

        # find device path.
        dev_path = (ct.c_uint8 * 8)()
        ret = usb.get_port_numbers(tmp_dev, dev_path, ct.sizeof(dev_path))
        if ret > 0:
            self.path = '.'.join([f"{p:d}" for p in dev_path][:ret])

        _logger.debug(' * {:04x}:{:04x} - bus: {:d}, device: {:d}, path: {}'.format(
            self.vendor_id, self.product_id, self.bus, self.address, self.path
        ))

        # Calculate usb product key.
        self.dev_key = f'{self.vendor_id:04x}:{self.product_id:04x}'

        # Find USB product group, based on first 3 digits of product id.
        if self.dev_key[:8] in _USB_PRODUCT_CLASSES:
            product_class = _USB_PRODUCT_CLASSES[self.dev_key[:8]]
            self.class_id = product_class.class_id
            self.class_descr = product_class.class_descr
            self.__dev_class__ = product_class

        # Find USB product description.
        if self.dev_key in USB_PRODUCT_DESCRIPTIONS:
            self.product_name = USB_PRODUCT_DESCRIPTIONS[self.dev_key]

    def __enter__(self):
        """ Return object with properties set to config values """
        _logger.debug(_('Opening USB device') + f' {self.dev_key}')

        dev_handle = self._get_device_handle()
        if not dev_handle:
            raise USBDeviceNotFoundError(self.dev_key)

        # We need to claim the USB device interface.
        usb.set_auto_detach_kernel_driver(dev_handle, 1)
        status = usb.claim_interface(dev_handle, 0)
        if status != usb.LIBUSB_SUCCESS:
            usb.close(dev_handle)
            self._close_device_list_handle()
            raise USBDeviceClaimInterfaceError(self.dev_key)

        self.__dev_handle__ = dev_handle
        self.__dev_handle_obj__ = self.__dev_class__(self.__dev_handle__, self.dev_key)
        return self.__dev_handle_obj__

    def _close_device_list_handle(self):
        """ Close the device list handle if set. """
        if self.__dev_list__:
            _logger.debug(_('Freeing USB device list.'))
            usb.free_device_list(self.__dev_list__, 1)
            self.__dev_list__ = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Clean up or close everything we need to """
        if self.__dev_handle__:
            _logger.debug(_('Closing USB device') + f' {self.dev_key}.')
            usb.close(self.__dev_handle__)
            self.__dev_handle__ = None

        self._close_device_list_handle()

        if exc_type is not None:
            print((traceback.format_exc()))
            _logger.error(_('USB device encountered an unexpected error, quitting.'))
            exit(-1)

    def _get_device_handle(self):
        """
        Return the raw LibUSB device handle pointer for our device. Must only be called from __enter__().
        :return: LibUSBDeviceHandle
        """
        # Get device list from libusb.
        self.__dev_list__ = ct.POINTER(ct.POINTER(usb.device))()
        cnt = usb.get_device_list(None, ct.byref(self.__dev_list__))
        if cnt < 0:
            usb_error(cnt, _('Failed to find attached USB devices.'))
            return None

        for dev in self.__dev_list__:
            if not dev:  # We must always look for the Null device and quit the loop.
                break

            dev_desc = usb.device_descriptor()
            ret = usb.get_device_descriptor(dev, ct.byref(dev_desc))
            if ret != usb.LIBUSB_SUCCESS:
                usb_error(ret, _('failed to get USB device descriptor.'))
                continue

            if self.vendor_id == dev_desc.idVendor and self.product_id == dev_desc.idProduct and \
                    self.bus == usb.get_bus_number(dev) and self.address == usb.get_device_address(dev):
                dev_handle = ct.POINTER(usb.device_handle)()
                ret = usb.open(dev, ct.byref(dev_handle))
                if ret == usb.LIBUSB_SUCCESS:
                    return dev_handle
                usb_error(ret, _('Failed to open device') + f' {self.dev_key}.')

        self._close_device_list_handle()
        _logger.debug(_('Device was not found on host when trying to open it.'))
        return None

    def __str__(self):
        return f'{self.dev_key} {self.bus, self.address}: {self.product_name}'

    def __repr__(self):
        return f'{self.dev_key} {self.bus, self.address}: {self.product_name}'


class USBDevices:
    """ Class that represents all USB devices found on local system. """

    _filters = None
    _usb_devices = None  # List of USB devices found.
    device_count = 0
    error = False

    def __init__(self, vendor_filter: list = None):
        """
        :param vendor_filter: list of vendor/manufacturer IDs to capture.
        """
        if vendor_filter:
            if not isinstance(vendor_filter, list):
                raise TypeError(_('USB device filter must be a list.'))
            for vendor_id in vendor_filter:
                if not isinstance(vendor_id, str) or len(vendor_id) != 4:
                    raise ValueError(_("Invalid USB vendor/manufacturer id") + f' ({vendor_id}).')
            self._filters = vendor_filter

        self._find_devices()

    def __iter__(self):
        return iter(self._usb_devices)

    def filter(self, class_id=None, bus=None, address=None):
        """
        Return iterator for all devices that match the filter.
        :param class_id: string
        :param bus: integer
        :param address: integer
        :return: iter(list)
        """
        if (class_id and not isinstance(class_id, (str, DeviceClassID))) or (bus and not isinstance(bus, int)) or \
                (address and not isinstance(address, int)):
            raise ValueError(_('Invalid filter method argument'))
        devices = list()
        for dev in self._usb_devices:
            if class_id and dev.class_id != (class_id if isinstance(class_id, str) else class_id.value):
                continue
            if bus and dev.bus != bus:
                continue
            if address and dev.address != address:
                continue
            devices.append(dev)

        return iter(devices)

    def rescan(self):
        """ Reload connected USB devices from local host. """
        self._find_devices()

    def get_device_classes(self):
        """ Return a list of device class descriptions for the devices we have. """
        return list(set([d.class_descr for d in self._usb_devices]))

    def _find_devices(self):
        """ Find all attached USB devices that match the filter. """
        self.error = False
        self.device_count = 0
        self._usb_devices = list()

        # Get device list from libusb.
        dev_list = ct.POINTER(ct.POINTER(usb.device))()
        cnt = usb.get_device_list(None, ct.byref(dev_list))
        if cnt < 0:
            usb_error(cnt, _('Failed to find attached USB devices.'))
            self.error = True
            return

        _logger.debug(_('Vendor filters: ') + ', '.join(self._filters))
        _logger.debug(_('Searching for USB devices...'))
        for dev in dev_list:
            if not dev:  # We must always look for the Null device and quit the loop.
                break

            dev_desc = usb.device_descriptor()
            ret = usb.get_device_descriptor(dev, ct.byref(dev_desc))
            if ret != usb.LIBUSB_SUCCESS:
                usb_error(ret, _('failed to get USB device descriptor.'))
                continue

            if not self._filters or f'{dev_desc.idVendor:04x}' in self._filters:
                ud = USBDeviceInfo(dev, dev_desc)
                self._usb_devices.append(ud)
                self.device_count += 1

        _logger.debug(_('Device search complete.'))

        usb.free_device_list(dev_list, 1)
