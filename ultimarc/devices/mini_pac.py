#
# This file is subject to the terms and conditions defined in the
# file 'LICENSE', which is part of this source code package.
#
import ctypes as ct
import logging

from ultimarc import translate_gettext as _
from ultimarc.devices._device import USBDeviceHandle
from ultimarc.devices._device import UltimarcStruct


MINIPAC_SET = ct.c_ubyte(0x09)
MINIPAC_REPORTID = 3
MINIPACWIndex = ct.c_uint16(0x02)


class Request(ct.Structure):
    _fields_ = [
        ('header', ct.c_ubyte),
        ('led_packet', ct.c_ubyte),
        ('quadrature', ct.c_ubyte),
        ('configuration', ct.c_ubyte)
    ]


class MiniPACDevice(USBDeviceHandle):
    """ Manage a MINI-pac device """
    class_id = 'mini-pac'  # Used to match/filter devices
    class_descr = _('Mini-PAC')


    def get_device_configuration(self):
        """ Return the current Mini-PAC device values """
        request = Request(0x59, 0xdd, 0x0f, 0)

        data = UltimarcStruct()
        ret = self.write(MINIPAC_SET, MINIPAC_REPORTID, MINIPACWIndex, ct.sizeof(request), request, ct.sizeof(request))
        if ret:
            ret = self.read()
