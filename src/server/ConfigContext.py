
import Config
import logging

logger = logging.getLogger(__name__)

class ConfigContext():
    def __init__(self):
        self.interface = None
        self.sensors = None
        self.cluster = None
        self.calibration = None

        self.language = None

        self.serverconfig = Config.Config(self)
        self.serverstate = ServerState(self)

class ServerState:
    def __init__(self, configcontext):
        self._configcontext = configcontext

    # PLUGIN STATUS
    plugins = None


    @property
    def info_dict(self):
        return {
            'release_version': self.release_version,
            'server_api': self.server_api_version,
            'json_api': self.json_api_version,
            'prog_start_epoch': self._program_start_epoch_formatted,
            'prog_start_time': self._program_start_time_formatted,
            'node_api_match': self.node_api_match,
            'node_api_lowest': self.node_api_lowest,
            'node_api_best': self.node_api_best,
            'node_api_levels': self.node_api_levels,
            'node_version_match': self.node_version_match,
            'node_fw_versions': self.node_fw_versions,
        }

