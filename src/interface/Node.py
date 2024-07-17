'''Node class for the RotorHazard interface.'''

class Node:
    '''Node class represents the arduino/rx pair.'''
    def __init__(self):
        self.api_level = 0
        self.api_valid_flag = False
        self.index = -1
        self.multi_node_index = -1
        self.multi_curnode_index_holder = None
        self.multi_node_slot_index = -1
        self.rhfeature_flags = 0
        self.firmware_version_str = None
        self.firmware_proctype_str = None
        self.firmware_timestamp_str = None
        self.frequency = 0
        self.current_rssi = 0
        self.trigger_rssi = 0
        self.node_peak_rssi = 0
        self.node_nadir_rssi = 0
        self.pass_peak_rssi = 0
        self.pass_nadir_rssi = 0
        self.max_rssi_value = 999
        self.node_lap_id = -1
        self.current_pilot_id = 0
        self.crossing = 0 
        # self.lap_ms_since_start = -1
        self.lap_timestamp = -1
        self.lap_time = 0
        self.debug_pass_count = 0
        self.bad_rssi_count = 0

        self.trigger_threshold = 15 
        self.calibration_threshold = 90 
        self.calibration_offset = 20 

        self.under_min_lap_count = 0

        self.history_values = []
        self.history_times = []

        self.scan_enabled = False
        self.scan_interval = 0 # scanning frequency interval
        self.min_scan_frequency = 0
        self.max_scan_frequency = 0
        self.max_scan_interval = 0
        self.min_scan_interval = 0
        self.scan_zoom = 0

        self.io_request = None # request time of last I/O read
        self.io_response = None # response time of last I/O read
        
        self.read_block_count = 0
        self.read_error_count = 0

    def init(self):
        if self.api_level >= 10:
            self.api_valid_flag = True  # set flag for newer API functions supported
        if self.api_valid_flag and self.api_level >= 18:
            self.max_rssi_value = 255
        else:
            self.max_rssi_value = 999

    def set_scan_interval(self, minFreq, maxFreq, maxInterval, minInterval, zoom):
        if minFreq > 0 and minFreq <= maxFreq and minInterval > 0 and minInterval <= maxInterval and zoom > 0:
            self.scan_enabled = True
            self.min_scan_frequency = minFreq
            self.max_scan_frequency = maxFreq
            self.max_scan_interval = maxInterval
            self.min_scan_interval = minInterval
            self.scan_zoom = zoom
            self.scan_interval = maxInterval
        else:
            self.scan_enabled = False
            self.min_scan_frequency = 0
            self.max_scan_frequency = 0
            self.max_scan_interval = 0
            self.min_scan_interval = 0
            self.scan_zoom = 0
            self.scan_interval = 0

    def get_settings_json(self):
        return {
            'frequency': self.frequency,
            'current_rssi': self.current_rssi,
            'trigger_threshold': self.trigger_threshold,
            'calibration_threshold': self.calibration_threshold,
            'calibration_offset': self.calibration_offset
        }

    def is_valid_rssi(self, value):
        return value > 0 and value < self.max_rssi_value

    def inc_read_block_count(self, interface):
        if interface:
            self.read_block_count += 1
            interface.inc_intf_read_block_count()

    def inc_read_error_count(self, interface):
        if interface:
            self.read_error_count += 1
            interface.inc_intf_read_error_count()

    def get_read_error_report_str(self):
        return "Node{0}:{1}/{2}({3:.2%})".format(self.index+1, self.read_error_count, \
                self.read_block_count, (float(self.read_error_count) / float(self.read_block_count)))
