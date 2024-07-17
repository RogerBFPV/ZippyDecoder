import gevent
import logging
from time import monotonic

ENTER_AT_PEAK_MARGIN = 5 # closest that captured enter-at level can be to node peak RSSI
CAP_ENTER_EXIT_AT_MILLIS = 3000  # number of ms for capture of enter/exit-at levels

logger = logging.getLogger(__name__)


class BaseHardwareInterface(object):

    LAP_SOURCE_REALTIME = 0
    LAP_SOURCE_MANUAL = 1
    LAP_SOURCE_RECALC = 2
    LAP_SOURCE_AUTOMATIC = 3
    LAP_SOURCE_API = 4
    LAP_SOURCE_LABEL_STRS = ["realtime", "manual", "recalc", "automatic", "API"]

    RACE_STATUS_READY = 0
    RACE_STATUS_STAGING = 3
    RACE_STATUS_RACING = 1
    RACE_STATUS_DONE = 2

    def __init__(self):
        self.calibration_threshold = 20
        self.calibration_offset = 10
        self.trigger_threshold = 20
        self.start_time = int(1000*monotonic()) # millis
        self.environmental_data_update_tracker = 0
        self.race_status = BaseHardwareInterface.RACE_STATUS_READY
        self.pass_record_callback = None # Function added in server.py
        self.new_enter_or_exit_at_callback = None # Function added in server.py
        self.node_crossing_callback = None # Function added in server.py
        self.nodes = []

    # returns the elapsed milliseconds since the start of the program
    def milliseconds(self):
        return int(1000*monotonic()) - self.start_time

    def log(self, message):
        logger.info('Interface: {0}'.format(message))

    def get_lap_source_str(self, source_idx):
        return BaseHardwareInterface.LAP_SOURCE_LABEL_STRS[source_idx] \
            if source_idx >= 0 and source_idx < len(BaseHardwareInterface.LAP_SOURCE_LABEL_STRS) \
            else "unknown ({})".format(source_idx)


    #
    # External functions for setting data
    #

    def intf_simulate_lap(self, node_index, ms_val):
        node = self.nodes[node_index]
        node.lap_timestamp = monotonic() - (ms_val / 1000.0)
        node.enter_at_timestamp = node.exit_at_timestamp = 0
        self.pass_record_callback(node, node.lap_timestamp, BaseHardwareInterface.LAP_SOURCE_MANUAL)  #pylint: disable=not-callable

    def set_race_status(self, race_status):
        self.race_status = race_status

    def enable_calibration_mode(self):
        pass 

    #
    # Get Json Node Data Functions
    #

    def get_settings_json(self):
        return {
            'nodes': [node.get_settings_json() for node in self.nodes],
        }

    def get_heartbeat_json(self):
        json = {
            'current_rssi': [node.current_rssi for node in self.nodes],
            'trigger_rssi': [node.trigger_rssi for node in self.nodes],
            'frequency': [node.frequency for node in self.nodes],
            'crossing': [node.crossing for node in self.nodes]
        }
        for i, node in enumerate(self.nodes):
            if node.scan_enabled:
                new_freq = node.frequency + node.scan_interval
                if new_freq < node.min_scan_frequency or new_freq > node.max_scan_frequency:
                    new_freq = node.min_scan_frequency
                    node.scan_interval /= node.scan_zoom
                    if node.scan_interval < node.min_scan_interval:
                        node.scan_interval = node.max_scan_interval
                self.set_frequency(i, new_freq)
        return json

    def get_calibration_threshold_json(self,node_index):
        node = self.nodes[node_index]
        return {
            'node': node.index,
            'calibration_threshold': node.calibration_threshold
        }

    def get_calibration_offset_json(self,node_index):
        node = self.nodes[node_index]
        return {
            'node': node.index,
            'calibration_offset': node.calibration_offset
        }

    def get_trigger_threshold_json(self,node_index):
        node = self.nodes[node_index]
        return {
            'node': node.index,
            'trigger_threshold': node.trigger_threshold
        }

    def get_frequency_json(self, node_index):
        node = self.nodes[node_index]
        return {
            'node': node.index,
            'frequency': node.frequency
        }

    def set_frequency(self, node_index, frequency):
        pass

