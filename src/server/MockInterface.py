import gevent
from random import randint

import sys

from Node import Node
from BaseHardwareInterface import BaseHardwareInterface

# prefix strings for finding text values in firmware '.bin' files
FW_TEXT_BLOCK_SIZE = 16     # length of data returned by 'READ_FW_...' fns
FW_VERSION_PREFIXSTR = "FIRMWARE_VERSION: "
FW_BUILDDATE_PREFIXSTR = "FIRMWARE_BUILDDATE: "
FW_BUILDTIME_PREFIXSTR = "FIRMWARE_BUILDTIME: "
FW_PROCTYPE_PREFIXSTR = "FIRMWARE_PROCTYPE: "


class MockInterface(BaseHardwareInterface):
    def __init__(self, *args, **kwargs):
        BaseHardwareInterface.__init__(self)
        self.update_thread = None
        self.nodes = []
        self.calibration_threshold = 20
        self.FW_TEXT_BLOCK_SIZE = FW_TEXT_BLOCK_SIZE
        self.FW_VERSION_PREFIXSTR = FW_VERSION_PREFIXSTR
        self.FW_BUILDDATE_PREFIXSTR = FW_BUILDDATE_PREFIXSTR
        self.FW_BUILDTIME_PREFIXSTR = FW_BUILDTIME_PREFIXSTR
        self.FW_PROCTYPE_PREFIXSTR = FW_PROCTYPE_PREFIXSTR

        frequencies = [5685, 5760, 5800, 5860, 5905, 5645]
        for index, frequency in enumerate(frequencies):
            node = Node()
            node.frequency = frequency
            node.index = index
            self.nodes.append(node)

    def update_loop(self):
        while True:
            self.update()
            gevent.sleep(0.5)

    def update(self):
        for node in self.nodes:
            node.current_rssi = randint(0,255);
            if node.current_rssi > 100:
              node.crossing = 1 
            else:
              node.crossing = 0 
            gevent.sleep(0.01)

    def start(self):
        if self.update_thread is None:
            self.log('starting background thread')
            self.update_thread = gevent.spawn(self.update_loop)

    def set_frequency(self, node_index, frequency):
        node = self.nodes[node_index]
        node.frequency = frequency

    def set_calibration_threshold_global(self, calibration_threshold):
        self.calibration_threshold = calibration_threshold

    def set_calibration_offset_global(self, calibration_offset):
        self.calibration_offset = calibration_offset

    def set_trigger_threshold_global(self, trigger_threshold):
        self.trigger_threshold = trigger_threshold

    def set_filter_ratio_global(self, filter_ratio):
        self.filter_ratio = filter_ratio

    def set_calibration_mode(self, node_index, calibration_mode):
        pass

    def enable_calibration_mode(self):
        pass

    def log(self, message):
        string = 'MockInterface: {0}'.format(message)
        print(string)

    ## stuff for firmware update
    def get_fwupd_serial_name(self):
        return None

    def jump_to_bootloader(self):
        self.log("MockInterace - no jump-to-bootloader support")

    def send_status_message(self, msgTypeVal, msgDataVal):
        return False

    def send_shutdown_button_state(self, stateVal):
        return False

    def send_shutdown_started_message(self):
        return False    
                        
    def send_server_idle_message(self):
        return False

    def close_fwupd_serial_port(self):
        pass

    def get_info_node_obj(self):
        return self.nodes[0] if self.nodes and len(self.nodes) > 0 else None
        
    def inc_intf_read_block_count(self):
        pass
        
    def inc_intf_read_error_count(self):
        pass

    def inc_intf_write_block_count(self): 
        pass
        
    def inc_intf_write_error_count(self): 
        pass
            
    def get_intf_total_error_count(self): 
        return 0
            
    def set_intf_error_report_percent_limit(self, percentVal):
        pass





def get_hardware_interface(*args, **kwargs):
    '''Returns the interface object.'''
    return MockInterface(*args, **kwargs)
