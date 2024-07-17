'''RotorHazard hardware interface layer.'''

import os
import logging
import gevent # For threads and timing
import i2c_helper
import Config
import ConfigContext
from time import monotonic # to capture read timing


from Plugins import Plugins
from i2c_node import I2CNode,discover
from BaseHardwareInterface import BaseHardwareInterface
from commonvars import *
from serial_node import *

ConfigContext = ConfigContext.ConfigContext() 
class LTInterface(BaseHardwareInterface):
    def __init__(self, *args, **kwargs):
        BaseHardwareInterface.__init__(self)
        self.FW_TEXT_BLOCK_SIZE = FW_TEXT_BLOCK_SIZE
        self.FW_VERSION_PREFIXSTR = FW_VERSION_PREFIXSTR
        self.FW_BUILDDATE_PREFIXSTR = FW_BUILDDATE_PREFIXSTR
        self.FW_BUILDTIME_PREFIXSTR = FW_BUILDTIME_PREFIXSTR
        self.FW_PROCTYPE_PREFIXSTR = FW_PROCTYPE_PREFIXSTR
        self.update_thread = None      # Thread for running the main update loop
        self.fwupd_serial_obj = None   # serial object for in-app update of node firmware
        self.info_node_obj = None      # node object containing info (like node version, etc)

        self.intf_read_block_count = 0  # number of blocks read by all nodes
        self.intf_read_error_count = 0  # number of read errors for all nodes
        self.intf_write_block_count = 0  # number of blocks write by all nodes
        self.intf_write_error_count = 0  # number of write errors for all nodes
        self.intf_error_report_limit = 0.0  # log if ratio of comm errors is larger

        #self.nodes = Plugins(suffix='node')
        #self.discover_nodes(*args, **kwargs)

        kwargs['idxOffset'] = 0; # may need to fix this later on
        kwargs['i2c_helper'] = i2c_helper.create(Config.Config(self))
        kwargs['config'] = Config.Config(self)
        self.nodes = discover(includeOffset=True, *args, **kwargs)
        if len(self.nodes) == 0:
            kwargs['config'] = Config.Config(self)
            self.nodes = discoverserial(includeOffset=True, *args, **kwargs)
        
        self.data_loggers = {}
        if len(self.nodes) > 0:
            for node in self.nodes:
                node.frequency = self.get_value_16(node, READ_FREQUENCY)
                if not node.frequency:
                    raise RuntimeError('Unable to read frequency value from node {0}'.format(node.index+1))

                node.init()
                if node.api_level >= 10:
                    node.node_peak_rssi = self.get_value_rssi(node, READ_NODE_RSSI_PEAK)
                    if node.api_level >= 13:
                        node.trigger_threshold = self.get_value_rssi(node, READ_TRIGGER_THRESHOLD)
                        node.calibration_threshold = self.get_value_rssi(node, READ_CALIBRATION_THRESHOLD)
                        node.calibration_offset = self.get_value_rssi(node, READ_CALIBRATION_OFFSET)
                    if node.multi_node_index < 0:  # (non multi-nodes will always have default values)
                        logger.debug("Node {}: Freq={}, Trigger Threshold={}, Calibraiton Threshold={}, Calibration Offset={}".format(\
                                     node.index+1, node.frequency, node.trigger_threshold, node.calibration_threshold, node.calibration_offset))
                    if node.multi_node_index >= 0:  # (multi-nodes )
                        #roger
                        self.set_frequency(node.multi_node_index,  ConfigContext.serverconfig.get_item_int('NODE','FREQ'+str(node.multi_node_index)))
                        self.set_trigger_threshold(node.multi_node_index,  ConfigContext.serverconfig.get_item_int('NODE','TT'+str(node.multi_node_index)))
                        self.set_calibration_threshold(node.multi_node_index,  ConfigContext.serverconfig.get_item_int('NODE','CT'+str(node.multi_node_index)))
                        self.set_calibration_offset(node.multi_node_index,  ConfigContext.serverconfig.get_item_int('NODE','CO'+str(node.multi_node_index)))
                        logger.debug("MultiNode {}: Freq={}, Trigger Threshold={}, Calibraiton Threshold={}, Calibration Offset={}".format(\
                                     node.index+1, node.frequency, node.trigger_threshold, node.calibration_threshold, node.calibration_offset))
    
                    if "RH_RECORD_NODE_{0}".format(node.index+1) in os.environ:
                        self.data_loggers[node.index] = open("data_{0}.csv".format(node.index+1), 'w')
                        logger.info("Data logging enabled for node {0}".format(node.index+1))

                    print("Node {}: Freq={}, Trigger Threshold={}, Calibraiton Threshold={}, Calibration Offset={}".format(\
                                     node.index+1, node.frequency, node.trigger_threshold, node.calibration_threshold, node.calibration_offset))

                else:
                    logger.warning("Node {} has obsolete API_level ({})".format(node.index+1, node.api_level))
                if node.api_level >= 32:
                    flags_val = self.get_value_16(node, READ_RHFEAT_FLAGS)
                    if flags_val:
                        node.rhfeature_flags = flags_val
                        # if first node that supports in-app fw update then save port name
                        if (not self.fwupd_serial_obj) and hasattr(node, 'serial') and node.serial and \
                                (node.rhfeature_flags & (RHFEAT_STM32_MODE|RHFEAT_IAP_FIRMWARE)) != 0:
                            self.set_fwupd_serial_obj(node.serial)
        else:
            node = self.info_node_obj  # handle S32_BPill board with no receiver modules attached
            if node and node.api_level >= 32:
                flags_val = self.get_value_16(node, READ_RHFEAT_FLAGS)
                if flags_val:
                    node.rhfeature_flags = flags_val
                    # if node supports in-app fw update then save port name
                    if (not self.fwupd_serial_obj) and hasattr(node, 'serial') and node.serial and \
                            (node.rhfeature_flags & (RHFEAT_STM32_MODE|RHFEAT_IAP_FIRMWARE)) != 0:
                        self.set_fwupd_serial_obj(node.serial)
            

    def discover_nodes(self, *args, **kwargs):
        kwargs['set_info_node_obj_fn'] = self.set_info_node_obj
        print ("in the discover_nodes LTInterface")
        self.nodes.discover(includeOffset=True, *args, **kwargs)


    #
    # Update Loop
    #

    def start(self):
        if self.update_thread is None:
            self.log('Starting LTInterface background thread')
            self.update_thread = gevent.spawn(self.update_loop)

    def stop(self):
        if self.update_thread:
            self.log('Stopping background thread')
            self.update_thread.kill(block=True, timeout=0.5)
            self.update_thread = None

    def update_loop(self):
        while True:
            try:
                while True:
                    self.update()
                    gevent.sleep(UPDATE_SLEEP)
            except KeyboardInterrupt:
                logger.info("Update thread terminated by keyboard interrupt")
                raise
            except SystemExit:
                raise
            except Exception:
                logger.exception('Exception in RHInterface update_loop():')
                gevent.sleep(UPDATE_SLEEP*10)

    def update(self):
        startThreshLowerNode = None
        for node in self.nodes:
            if node.frequency:
                data = node.read_block(self, READ_LAP_STATS, 13)

                if data != None and len(data) > 0:
                    lap_id = data[0]
                    ms_since_lap = unpack_32(data[1:])
                    node.current_rssi = unpack_8(data[5:])
                    node.trigger_rssi = unpack_8(data[6:])
                    node.peak_rssi = unpack_8(data[7:])
                    node.lap_time = unpack_32(data[8:])
                    node.crossing = unpack_8(data[12:])

                    if node.is_valid_rssi(node.current_rssi):
                        if lap_id != node.node_lap_id:
                            if node.node_lap_id != -1 and callable(self.pass_record_callback):
                                self.pass_record_callback(node, ms_since_lap)
                            node.node_lap_id = lap_id

                    else:
                        node.bad_rssi_count += 1
                        # log the first ten, but then only 1 per 100 after that
                        if node.bad_rssi_count <= 10 or node.bad_rssi_count % 100 == 0:
                            self.log('RSSI reading ({}) out of range on Node {}; rejected; count={}'.\
                                     format(node.current_rssi, node.index+1, node.bad_rssi_count))


    #
    # Internal helper functions for setting single values
    #

    def get_value_8(self, node, command):
        data = node.read_block(self, command, 1)
        result = None
        if data != None:
            result = unpack_8(data)
        return result

    def get_value_16(self, node, command):
        data = node.read_block(self, command, 2)
        result = None
        if data != None:
            result = unpack_16(data)
        return result

    def get_value_32(self, node, command):
        data = node.read_block(self, command, 4)
        result = None
        if data != None:
            result = unpack_32(data)
        return result

    def set_and_validate_value_8(self, node, write_command, read_command, in_value):
        success = False
        retry_count = 0
        out_value = None
        while success is False and retry_count <= MAX_RETRY_COUNT:
            node.write_block(self, write_command, pack_8(in_value))
            out_value = self.get_value_8(node, read_command)
            if out_value == in_value:
                success = True
            else:
                retry_count = retry_count + 1
                self.log('Value 8v Not Set (retry={0}): cmd={1}, val={2}, node={3}'.\
                         format(retry_count, hex(write_command), in_value, node.index+1))

        if out_value == None:
            out_value = in_value
        return out_value

    def set_and_validate_value_16(self, node, write_command, read_command, in_value):
        success = False
        retry_count = 0
        out_value = None
        while success is False and retry_count <= MAX_RETRY_COUNT:
            node.write_block(self, write_command, pack_16(in_value))
            out_value = self.get_value_16(node, read_command)
            # confirm same value (also handle negative value)
            if out_value == in_value or out_value == in_value + (1 << 16):
                success = True
            else:
                retry_count = retry_count + 1
                self.log('Value 16v Not Set (retry={0}): cmd={1}, val={2}, node={3}'.\
                         format(retry_count, write_command, in_value, node.index+1))

        if out_value == None:
            out_value = in_value
        return out_value

    def set_and_validate_value_32(self, node, write_command, read_command, in_value):
        success = False
        retry_count = 0
        out_value = None
        while success is False and retry_count <= MAX_RETRY_COUNT:
            node.write_block(self, write_command, pack_32(in_value))
            out_value = self.get_value_32(node, read_command)
            # confirm same value (also handle negative value)
            if out_value == in_value or out_value == in_value + (1 << 32):
                success = True
            else:
                retry_count = retry_count + 1
                self.log('Value Not Set 32v (retry={0}): cmd={1}, val={2}, node={3}'.\
                         format(retry_count, write_command, in_value, node.index+1))

        if out_value == None:
            out_value = in_value
        return out_value

    def set_value_8(self, node, write_command, in_value):
        success = False
        retry_count = 0
        while success is False and retry_count <= MAX_RETRY_COUNT:
            if node.write_block(self, write_command, pack_8(in_value)):
                success = True
            else:
                retry_count = retry_count + 1
                self.log('Value 8 Not Set (retry={0}): cmd={1}, val={2}, node={3}'.\
                         format(retry_count, write_command, in_value, node.index+1))
        return success

    def set_value_32(self, node, write_command, in_value):
        success = False
        retry_count = 0
        while success is False and retry_count <= MAX_RETRY_COUNT:
            if node.write_block(self, write_command, pack_32(in_value)):
                success = True
            else:
                retry_count = retry_count + 1
                self.log('Value 32 Not Set (retry={0}): cmd={1}, val={2}, node={3}'.\
                         format(retry_count, write_command, in_value, node.index+1))
        return success

    def set_and_validate_value_rssi(self, node, write_command, read_command, in_value):
        return self.set_and_validate_value_8(node, write_command, read_command, in_value)

    def get_value_rssi(self, node, command):
        return self.get_value_8(node, command)

    #
    # External functions for setting data
    #

    def set_frequency(self, node_index, frequency):
        node = self.nodes[node_index]
        node.debug_pass_count = 0  # reset debug pass count on frequency change
        if frequency:
            node.frequency = self.set_and_validate_value_16(node,
                WRITE_FREQUENCY,
                READ_FREQUENCY,
                frequency)
        else:  # if freq=0 (node disabled) then write frequency value to power down rx module, but save 0 value
            self.set_and_validate_value_16(node,
                WRITE_FREQUENCY,
                READ_FREQUENCY,
                1111 if node.api_level >= 24 else 5800)
            node.frequency = 0

    def transmit_trigger_threshold(self, node, trigger_threshold):
        return self.set_and_validate_value_rssi(node,
            WRITE_TRIGGER_THRESHOLD,
            READ_TRIGGER_THRESHOLD,
            trigger_threshold)

    def set_trigger_threshold(self, node_index, trigger_threshold):
        node = self.nodes[node_index]
        if node.api_valid_flag and node.is_valid_rssi(trigger_threshold):
            if self.transmit_trigger_threshold(node, trigger_threshold):
                node.trigger_threshold = trigger_threshold 

    def transmit_calibration_threshold(self, node, calibration_threshold):
        return self.set_and_validate_value_rssi(node,
            WRITE_CALIBRATION_THRESHOLD,
            READ_CALIBRATION_THRESHOLD,
            calibration_threshold)

    def set_calibration_threshold(self, node_index, calibration_threshold):
        node = self.nodes[node_index]
        if node.api_valid_flag and node.is_valid_rssi(calibration_threshold):
            if self.transmit_calibration_threshold(node, calibration_threshold):
                node.calibration_threshold = calibration_threshold 

    def transmit_calibration_offset(self, node, calibration_offset):
        return self.set_and_validate_value_rssi(node,
            WRITE_CALIBRATION_OFFSET,
            READ_CALIBRATION_OFFSET,
            calibration_offset)

    def set_calibration_offset(self, node_index, calibration_offset):
        node = self.nodes[node_index]
        if node.api_valid_flag and node.is_valid_rssi(calibration_offset):
            if self.transmit_calibration_offset(node, calibration_offset):
                node.calibration_offset = calibration_offset 

    def enable_calibration_mode(self):
        for node in self.nodes:
            self.set_value_8(node, WRITE_CALIBRATION_MODE, 0)

    def force_end_crossing(self, node_index):
        node = self.nodes[node_index]
        if node.api_level >= 14:
            self.set_value_8(node, FORCE_END_CROSSING, 0)

    def jump_to_bootloader(self):
        for node in self.nodes:
            if (node.rhfeature_flags & RHFEAT_JUMPTO_BOOTLDR) != 0:
                node.jump_to_bootloader(self)
                return
        node = self.get_info_node_obj()
        if node and (node.rhfeature_flags & RHFEAT_JUMPTO_BOOTLDR) != 0:
            node.jump_to_bootloader(self)
            return
        self.log("Unable to find any nodes with jump-to-bootloader support")

    def send_status_message(self, msgTypeVal, msgDataVal):
        node = self.get_info_node_obj()
        return node.send_status_message(self, msgTypeVal, msgDataVal) if node else False

    def send_shutdown_button_state(self, stateVal):
        return self.send_status_message(STATMSG_SDBUTTON_STATE, stateVal)

    def send_shutdown_started_message(self):
        return self.send_status_message(STATMSG_SHUTDOWN_STARTED, 0)

    def send_server_idle_message(self):
        return self.send_status_message(STATMSG_SERVER_IDLE, 0)

    def set_fwupd_serial_obj(self, serial_obj):
        self.fwupd_serial_obj = serial_obj

    def set_mock_fwupd_serial_obj(self, port_name):
        serial_obj = type('', (), {})()  # empty base object
        def mock_no_op():
            pass
        serial_obj.name = port_name
        serial_obj.open = mock_no_op
        serial_obj.close = mock_no_op
        self.fwupd_serial_obj = serial_obj

    def get_fwupd_serial_name(self):
        return self.fwupd_serial_obj.name if self.fwupd_serial_obj else None

    def close_fwupd_serial_port(self):
        try:
            if self.fwupd_serial_obj:
                self.fwupd_serial_obj.close()
        except Exception as ex:
            self.log("Error closing FW node serial port: " + str(ex))

    def set_info_node_obj(self, node):
        self.info_node_obj = node

    def get_info_node_obj(self):
        if self.info_node_obj:
            return self.info_node_obj
        return self.nodes[0] if self.nodes and len(self.nodes) > 0 else None

    def inc_intf_read_block_count(self):
        self.intf_read_block_count += 1

    def inc_intf_read_error_count(self):
        self.intf_read_error_count += 1

    def inc_intf_write_block_count(self):
        self.intf_write_block_count += 1

    def inc_intf_write_error_count(self):
        self.intf_write_error_count += 1

    def get_intf_total_error_count(self):
        return self.intf_read_error_count + self.intf_write_error_count

    # log comm errors if error percentage is >= this value
    def set_intf_error_report_percent_limit(self, percentVal):
        self.intf_error_report_limit = percentVal / 100

    def get_intf_error_report_str(self, forceFlag=False):
        try:
            if self.intf_read_block_count <= 0:
                return None
            r_err_ratio = float(self.intf_read_error_count) / float(self.intf_read_block_count) \
                          if self.intf_read_error_count > 0 else 0
            w_err_ratio = float(self.intf_write_error_count) / float(self.intf_write_block_count) \
                          if self.intf_write_block_count > 0 and self.intf_write_error_count > 0 else 0
            if forceFlag or r_err_ratio > self.intf_error_report_limit or \
                                        w_err_ratio > self.intf_error_report_limit:
                retStr = "CommErrors:"
                if forceFlag or self.intf_write_error_count > 0:
                    retStr += "Write:{0}/{1}({2:.2%}),".format(self.intf_write_error_count, \
                                    self.intf_write_block_count, w_err_ratio)
                retStr += "Read:{0}/{1}({2:.2%})".format(self.intf_read_error_count, \
                                    self.intf_read_block_count, r_err_ratio)
                for node in self.nodes:
                    retStr += ", " + node.get_read_error_report_str()
                return retStr
        except Exception as ex:
            self.log("Error in RHInterface 'get_intf_error_report_str()': " + str(ex))
        return None

def get_hardware_interface(*args, **kwargs):
    '''Returns the interface object.'''
    return LTInterface(*args, **kwargs)
