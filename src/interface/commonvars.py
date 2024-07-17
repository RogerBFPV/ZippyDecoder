import os
import logging

READ_ADDRESS = 0x00         # Gets i2c address of arduino (1 byte)
READ_FREQUENCY = 0x03       # Gets channel frequency (2 byte)
READ_LAP_STATS = 0x05

READ_FILTER_RATIO = 0x19

WRITE_FREQUENCY = 0x51 # Sets frequency (2 byte)
WRITE_CALIBRATION_THRESHOLD = 0x65
WRITE_CALIBRATION_MODE = 0x66
WRITE_CALIBRATION_OFFSET = 0x67
WRITE_TRIGGER_THRESHOLD = 0x68
WRITE_FILTER_RATIO = 0x69



READ_LAP_PASS_STATS = 0x0D
READ_LAP_EXTREMUMS = 0x0E
READ_RHFEAT_FLAGS = 0x11     # read feature flags value
# READ_FILTER_RATIO = 0x20    # node API_level>=10 uses 16-bit value
READ_REVISION_CODE = 0x22    # read NODE_API_LEVEL and verification value
READ_NODE_RSSI_PEAK = 0x23   # read 'nodeRssiPeak' value
READ_NODE_RSSI_NADIR = 0x24  # read 'nodeRssiNadir' value
READ_TRIGGER_THRESHOLD = 0x30
READ_CALIBRATION_THRESHOLD = 0x31
READ_CALIBRATION_OFFSET = 0x32
READ_TIME_MILLIS = 0x33      # read current 'millis()' time value
READ_MULTINODE_COUNT = 0x39  # read # of nodes handled by processor
READ_CURNODE_INDEX = 0x3A    # read index of current node for processor
READ_NODE_SLOTIDX = 0x3C     # read node slot index (for multi-node setup)
READ_FW_VERSION = 0x3D       # read firmware version string
READ_FW_BUILDDATE = 0x3E     # read firmware build date string
READ_FW_BUILDTIME = 0x3F     # read firmware build time string
READ_FW_PROCTYPE = 0x40      # read node processor type

WRITE_FREQUENCY = 0x51       # Sets frequency (2 byte)
WRITE_CALIBRATION_MODE = 0x66
WRITE_TRIGGER_THRESHOLD = 0x70
WRITE_CALIBRATION_THRESHOLD = 0x71
WRITE_CALIBRATION_OFFSET = 0x72
WRITE_CURNODE_INDEX = 0x7A  # write index of current node for processor
SEND_STATUS_MESSAGE = 0x75  # send status message from server to node
FORCE_END_CROSSING = 0x78   # kill current crossing flag regardless of RSSI value
JUMP_TO_BOOTLOADER = 0x7E   # jump to bootloader for flash update

LAPSTATS_FLAG_CROSSING = 0x01  # crossing is in progress
LAPSTATS_FLAG_PEAK = 0x02      # reported extremum is peak

# upper-byte values for SEND_STATUS_MESSAGE payload (lower byte is data)
STATMSG_SDBUTTON_STATE = 0x01    # shutdown button state (1=pressed, 0=released)
STATMSG_SHUTDOWN_STARTED = 0x02  # system shutdown started
STATMSG_SERVER_IDLE = 0x03       # server-idle tick message

FW_TEXT_BLOCK_SIZE = 16     # length of data returned by 'READ_FW_...' fns

# prefix strings for finding text values in firmware '.bin' files
FW_VERSION_PREFIXSTR = "FIRMWARE_VERSION: "
FW_BUILDDATE_PREFIXSTR = "FIRMWARE_BUILDDATE: "
FW_BUILDTIME_PREFIXSTR = "FIRMWARE_BUILDTIME: "
FW_PROCTYPE_PREFIXSTR = "FIRMWARE_PROCTYPE: "

# features flags for value returned by READ_RHFEAT_FLAGS command
RHFEAT_STM32_MODE = 0x0004      # STM 32-bit processor running multiple nodes
RHFEAT_JUMPTO_BOOTLDR = 0x0008  # JUMP_TO_BOOTLOADER command supported
RHFEAT_IAP_FIRMWARE = 0x0010    # in-application programming of firmware supported

UPDATE_SLEEP = float(os.environ.get('RH_UPDATE_INTERVAL', '0.1')) # Main update loop delay
MAX_RETRY_COUNT = 4 # Limit of I/O retries
MIN_RSSI_VALUE = 1               # reject RSSI readings below this value

logger = logging.getLogger(__name__)


def unpack_8(data):
    return data[0]

def pack_8(data):
    return [int(data & 0xFF)]

def unpack_16(data):
    '''Returns the full variable from 2 bytes input.'''
    result = data[0]
    result = (result << 8) | data[1]
    return result

def pack_16(data):
    '''Returns a 2 part array from the full variable.'''
    part_a = (data >> 8)
    part_b = (data & 0xFF)
    return [int(part_a), int(part_b)]

def unpack_32(data):
    '''Returns the full variable from 4 bytes input.'''
    result = data[0]
    result = (result << 8) | data[1]
    result = (result << 8) | data[2]
    result = (result << 8) | data[3]
    return result

def pack_32(data):
    '''Returns a 4 part array from the full variable.'''
    part_a = (data >> 24)
    part_b = (data >> 16) & 0xFF
    part_c = (data >> 8) & 0xFF
    part_d = (data & 0xFF)
    return [int(part_a), int(part_b), int(part_c), int(part_d)]


def calculate_checksum(data):
    checksum = sum(data) & 0xFF
    return checksum

def validate_checksum(data):
    '''Returns True if the checksum matches the data.'''
    if not data:
        return False
    checksum = calculate_checksum(data[:-1])
    return checksum == data[-1]

def unpack_rssi(node, data):
    if node.api_level >= 18:
        return unpack_8(data)
    else:
        return unpack_16(data) / 2
