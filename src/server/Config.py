'''
Global configurations
'''
import copy
import logging
import json
import shutil
import time
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, configcontext, filename='config.json'):
        self._configcontext = configcontext
        self.filename = filename

        self.config = {
            'SECRETS': {},
            'GENERAL': {},
            'HARDWARE': {},
            'LOGGING': {},
            'SENSORS': {},
            'NODE': {},
        }
        self.config['NODE']['FREQ0'] = 5658  
        self.config['NODE']['FREQ1'] = 5695  
        self.config['NODE']['FREQ2'] = 5760
        self.config['NODE']['FREQ3'] = 5800
        self.config['NODE']['FREQ4'] = 5880
        self.config['NODE']['FREQ5'] = 5917
        self.config['NODE']['FREQ6'] = 1111
        self.config['NODE']['FREQ7'] = 1111
        self.config['NODE']['TT0'] = 30 
        self.config['NODE']['CT0'] = 80 
        self.config['NODE']['CO0'] = 20 

        self.config['NODE']['TT1'] = 30 
        self.config['NODE']['CT1'] = 80 
        self.config['NODE']['CO1'] = 20 

        self.config['NODE']['TT2'] = 30 
        self.config['NODE']['CT2'] = 80 
        self.config['NODE']['CO2'] = 20 

        self.config['NODE']['TT3'] = 30 
        self.config['NODE']['CT3'] = 80 
        self.config['NODE']['CO3'] = 20 

        self.config['NODE']['TT4'] = 30 
        self.config['NODE']['CT4'] = 80 
        self.config['NODE']['CO4'] = 20 

        self.config['NODE']['TT5'] = 30 
        self.config['NODE']['CT5'] = 80 
        self.config['NODE']['CO5'] = 20 

        self.config['NODE']['TT6'] = 30 
        self.config['NODE']['CT6'] = 80 
        self.config['NODE']['CO6'] = 20 

        self.config['NODE']['TT7'] = 30 
        self.config['NODE']['CT7'] = 80 
        self.config['NODE']['CO7'] = 20 

        # hardware default configurations
        self.config['HARDWARE']['I2C_BUS'] = 1

        # other default configurations
        self.config['GENERAL']['HTTP_PORT'] = 5000
        self.config['GENERAL']['ADMIN_USERNAME'] = 'admin'
        self.config['GENERAL']['ADMIN_PASSWORD'] = 'zippyd'
        self.config['GENERAL']['SECONDARIES'] = []
        self.config['GENERAL']['SECONDARY_TIMEOUT'] = 300  # seconds
        self.config['GENERAL']['DEBUG'] = False
        self.config['GENERAL']['CORS_ALLOWED_HOSTS'] = '*'
        self.config['GENERAL']['FORCE_S32_BPILL_FLAG'] = False
        self.config['GENERAL']['DEF_NODE_FWUPDATE_URL'] = ''
        self.config['GENERAL']['SHUTDOWN_BUTTON_GPIOPIN'] = 18
        self.config['GENERAL']['SHUTDOWN_BUTTON_DELAYMS'] = 2500
        self.config['GENERAL']['DB_AUTOBKP_NUM_KEEP'] = 30
        self.config['GENERAL']['RACE_START_DELAY_EXTRA_SECS'] = 0.9  # amount of extra time added to prestage time
        self.config['GENERAL']['LOG_SENSORS_DATA_RATE'] = 300  # rate at which to log sensor data
        self.config['GENERAL']['SERIAL_PORTS'] = []
        self.config['GENERAL']['LAST_MODIFIED_TIME'] = 0


        # logging defaults
        self.config['LOGGING']['CONSOLE_LEVEL'] = "INFO"
        self.config['LOGGING']['SYSLOG_LEVEL'] = "NONE"
        self.config['LOGGING']['FILELOG_LEVEL'] = "INFO"
        self.config['LOGGING']['FILELOG_NUM_KEEP'] = 30
        self.config['LOGGING']['CONSOLE_STREAM'] = "stdout"

        self.InitResultStr = None
        self.InitResultLogLevel = logging.INFO


        # override defaults above with config from file
        try:
            with open(self.filename, 'r') as f:
                ExternalConfig = json.load(f)

            for key in ExternalConfig.keys():
                if key in self.config:
                    self.config[key].update(ExternalConfig[key])

            self.config_file_status = 1
            self.InitResultStr = "Using configuration file '{0}'".format(self.filename)
            self.InitResultLogLevel = logging.INFO
        except IOError:
            self.config_file_status = 0
            self.InitResultStr = "No configuration file found, using defaults"
            self.InitResultLogLevel = logging.INFO
        except ValueError as ex:
            self.config_file_status = -1
            self.InitResultStr = "Configuration file invalid, using defaults; error is: " + str(ex)
            self.InitResultLogLevel = logging.ERROR

        self.check_backup_config_file()
        self.save_config()

    # Writes a log message describing the result of the module initialization.
    def logInitResultMessage(self):
        if self.InitResultStr:
            logger.log(self.InitResultLogLevel, self.InitResultStr)

    def get_item(self, section, key):
        try:
            return self.config[section][key]
        except:
            return False

    def get_item_int(self, section, key, default_value=0):
        try:
            val = self.config[section][key]
            if val:
                return int(val)
            else:
                return default_value
        except:
            return default_value

    def get_section(self, section):
        try:
            return self.config[section]
        except:
            return False

    def set_item(self, section, key, value):
        try:
            self.config[section][key] = value
            self.save_config()
        except:
            return False
        return True

    def save_config(self):
        self.config['GENERAL']['LAST_MODIFIED_TIME'] = int(time.time())
        with open(self.filename, 'w') as f:
            f.write(json.dumps(self.config, indent=2))

    # if config file does not contain 'LAST_MODIFIED_TIME' item or time
    #  does not match file-modified timestamp then create backup of file
    def check_backup_config_file(self):
        try:
            if os.path.exists(self.filename):
                last_modified_time = self.get_item_int('GENERAL', 'LAST_MODIFIED_TIME')
                file_modified_time = int(os.path.getmtime(self.filename))
                if file_modified_time > 0 and abs(file_modified_time - last_modified_time) > 5:
                    time_str = datetime.fromtimestamp(file_modified_time).strftime('%Y%m%d_%H%M%S')
                    (fname_str, fext_str) = os.path.splitext(self.filename)
                    bkp_file_name = "{}_bkp_{}{}".format(fname_str, time_str, fext_str)
                    logger.info("Making backup of configuration file, name: {}".format(bkp_file_name))
                    shutil.copy2(self.filename, bkp_file_name)
        except Exception as ex:
                logger.warning("Error in 'check_backup_config_file()':  {}".format(ex))

    def get_sharable_config(self):
        sharable_config = copy.deepcopy(self.config)
        del sharable_config['SECRETS']
        return sharable_config

