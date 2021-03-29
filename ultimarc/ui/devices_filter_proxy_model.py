#
# This file is subject to the terms and conditions defined in the
# file 'LICENSE', which is part of this source code package.
#
import logging
import re

from PySide6.QtCore import Property, Signal, QModelIndex, QObject, QSortFilterProxyModel

from ultimarc.ui.devices_model import DeviceRoles

_logger = logging.getLogger('ultimarc')


class ClassFilterProxyModel(QSortFilterProxyModel, QObject):
    _changed_front_page_ = Signal(bool)
    _changed_filter_class_ = Signal(str)

    _front_page_ = True
    _filter_class_ = 'all'

    def __init__(self):
        super().__init__()

    def get_front_page(self):
        return self._front_page_

    def set_front_page(self, fp):
        if self._front_page_ != fp:
            self._front_page_ = fp
            self._changed_front_page_.emit(self._front_page_)
            self.invalidateFilter()

    def get_filter_class(self):
        return self._filter_class_

    def set_filter_class(self, new_filter):
        if self._filter_class_ != new_filter:
            # _logger.debug(f'class filter: set_filter_class {new_filter}')
            self._filter_class_ = new_filter
            self._changed_filter_class_.emit(self._filter_class_)
            self.invalidateFilter()

    front_page = Property(bool, get_front_page, set_front_page, notify=_changed_front_page_)
    filter_class = Property(str, get_filter_class, set_filter_class, notify=_changed_filter_class_)

    def filterAcceptsRow(self, source_row, source_parent: QModelIndex):
        index = self.sourceModel().index(source_row, 0, source_parent)
        if self.front_page:
            return True
        else:
            if self._filter_class_ == 'all':
                return True
            else:
                device_class_id = index.data(DeviceRoles.DEVICE_CLASS_ID)
                cb_filter = device_class_id == self._filter_class_
                return cb_filter


class DevicesFilterProxyModel(QSortFilterProxyModel, QObject):
    _changed_front_page_ = Signal(bool)
    _changed_filter_class_ = Signal(str)
    _changed_filter_text_ = Signal(str)
    _changed_device_property_ = Signal(object)
    _changed_selected_index_ = Signal(int)
    _changed_selected_ = Signal()

    _front_page_ = True
    _filter_text_ = ''
    _filter_class_ = 0
    _selected_index_ = -1

    def __init__(self):
        super().__init__()

    def get_front_page(self):
        return self._front_page_

    def set_front_page(self, fp):
        if self._front_page_ != fp:
            self._front_page_ = fp
            self._changed_front_page_.emit(self._front_page_)
            self.invalidateFilter()

    def get_filter_text(self):
        return self._filter_text_

    def set_filter_text(self, new_filter):
        if self._filter_text_ != new_filter:
            self._filter_text_ = new_filter
            self._changed_filter_text_.emit(self._filter_text_)
            self.invalidateFilter()

    def get_filter_class(self):
        return self._filter_class_

    def set_filter_class(self, new_filter):
        if self._filter_class_ != new_filter:
            self._filter_class_ = new_filter
            self._changed_filter_class_.emit(self._filter_class_)
            self.invalidateFilter()

    def set_selected_index(self, row):
        if self._selected_index_ != row:
            model_index = self.sourceModel().index(row, 0)
            self._selected_index_ = row
            self._changed_selected_.emit()

    def get_selected_property(self, value):
        index = self.sourceModel().index(self._selected_index_, 0)
        # _logger.debug(
        #    f'proxy: get_selected_property: {value.name}, {index.data(value)}')
        return index.data(value)

    def get_selected_product_name(self):
        return self.get_selected_property(DeviceRoles.PRODUCT_NAME)

    def get_selected_icon(self):
        return self.get_selected_property(DeviceRoles.ICON)

    def get_selected_device_class(self):
        return self.get_selected_property(DeviceRoles.DEVICE_CLASS)

    def get_selected_connected(self):
        return self.get_selected_property(DeviceRoles.CONNECTED)

    def get_selected_product_key(self):
        return self.get_selected_property(DeviceRoles.PRODUCT_KEY)

    selected_device_class = Property(str, get_selected_device_class, notify=_changed_selected_)
    selected_connected = Property(bool, get_selected_connected, notify=_changed_selected_)
    selected_icon = Property(str, get_selected_icon, notify=_changed_selected_)
    selected_product_name = Property(str, get_selected_product_name, notify=_changed_selected_)
    selected_product_key = Property(str, get_selected_product_key, notify=_changed_selected_)
    selected_index = Property(int, fset=set_selected_index, notify=_changed_selected_)
    front_page = Property(bool, get_front_page, set_front_page, notify=_changed_front_page_)
    filter_text = Property(str, get_filter_text, set_filter_text, notify=_changed_filter_text_)

    def filterAcceptsRow(self, source_row, source_parent: QModelIndex):
        index = self.sourceModel().index(source_row, 0, source_parent)
        if self.front_page:
            connected = index.data(DeviceRoles.CONNECTED)
            return True if connected and source_row < 4 else False
        else:
            if len(self._filter_text_) == 0:
                return True
            else:
                product_name = index.data(DeviceRoles.PRODUCT_NAME)
                device_class = index.data(DeviceRoles.DEVICE_CLASS)
                product_key = index.data(DeviceRoles.PRODUCT_KEY)

                re_name = re.search(self._filter_text_, product_name, re.IGNORECASE) is not None
                re_class = re.search(self._filter_text_, device_class, re.IGNORECASE) is not None
                re_key = re.search(self._filter_text_, product_key, re.IGNORECASE) is not None
                re_filter = re_name or re_class or re_key
                # _logger.debug(f're filter ({name}: {re_filter}')
                return re_filter
