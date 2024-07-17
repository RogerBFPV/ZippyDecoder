#!/usr/bin/env python
import logging
import log
import LTUtils
import gevent
import gevent.monkey
import functools
import ConfigContext
gevent.monkey.patch_all()

import json
import Config

from flask import Flask, render_template, session, request, Response
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

import sys

import argparse
import util.stm32loader as stm32loader

NODE_FW_PATHNAME = "src/node/node.ino.BLUEPILL_F103C8.bin"

parser = argparse.ArgumentParser(description='Timing Server')
parser.add_argument('--mock', dest='mock', action='store_true', default=False, help="use mock data for testing")
args = parser.parse_args()
log.early_stage_setup()
logger = logging.getLogger(__name__)
ConfigContext = ConfigContext.ConfigContext()

LTUtils.idAndLogSystemInfo()
# check if 'log' directory owned by 'root' and change owner to 'pi' user if so
if LTUtils.checkSetFileOwnerPi(log.LOG_DIR_NAME):
    logger.info("Changed '{0}' dir owner from 'root' to 'pi'".format(log.LOG_DIR_NAME))

sys.path.append('../interface')
print (sys.platform.lower())
if args.mock or sys.platform.lower().startswith('win'):
    from MockInterface import get_hardware_interface
    hardwareInterface = get_hardware_interface()
elif args.mock or sys.platform.lower().startswith('darwin'):
    from MockInterface import get_hardware_interface
    hardwareInterface = get_hardware_interface()
elif sys.platform.lower().startswith('linux'):
    from LTInterface import get_hardware_interface 
    hardwareInterface = get_hardware_interface(config=Config,isS32BPillFlag=LTUtils.is_S32_BPill_board())


# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = "gevent"

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins='*')
heartbeat_thread = None
# thus set up logging for good.^M
Current_log_path_name = log.later_stage_setup(ConfigContext.serverconfig.get_section('LOGGING'), socketio)

firmware_version = {'major': 0, 'minor': 1}


# LED Code
import time
def check_auth(username, password):
    '''Check if a username password combination is valid.'''
    return username == ConfigContext.serverconfig.get_item('SECRETS', 'ADMIN_USERNAME') and password == ConfigContext.serverconfig.get_item('SECRETS', 'ADMIN_PASSWORD')

def authenticate():
    '''Sends a 401 response that enables basic auth.'''
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    if ConfigContext.serverconfig.get_item('SECRETS', 'ADMIN_USERNAME') or \
        ConfigContext.serverconfig.get_item('SECRETS', 'ADMIN_PASSWORD'):
        @functools.wraps(f)
        def decorated_auth(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
            return f(*args, **kwargs)
        return decorated_auth
    # allow open access if both ADMIN fields set to empty string:
    @functools.wraps(f)
    def decorated_noauth(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_noauth

def parse_json(data):
    if isinstance(data, (str)):
       return json.loads(data)
    return data

@app.route('/')
@requires_auth
def index():
    template_data = { }
    return render_template('index.html', async_mode=socketio.async_mode,node_fw_updatable=(hardwareInterface.get_fwupd_serial_name()!=None) ,**template_data)

@app.route('/graphs')
def graphs():
    return render_template('graphs.html', async_mode=socketio.async_mode)

@app.route('/rssi')
def rssi():
    return render_template('rssi.html', async_mode=socketio.async_mode)

@app.route('/updatenodes')
@requires_auth
def render_updatenodes():
    return render_template('updatenodes.html', fw_src_str=getDefNodeFwUpdateUrl())

@socketio.on('connect')
def connect_handler():
    print ('connected!!');
    hardwareInterface.start()
    global heartbeat_thread
    if (heartbeat_thread is None):
        heartbeat_thread = gevent.spawn(heartbeat_thread_function)

@socketio.on('disconnect')
def disconnect_handler():
    print ('disconnected!!');

@socketio.on('get_version')
def on_get_version():
    return firmware_version

@socketio.on('get_timestamp')
def on_get_timestamp():
    print('get_timestamp')
    return {'timestamp': hardwareInterface.milliseconds()}

@socketio.on('get_settings')
def on_get_settings():
    print('get_settings')
    return hardwareInterface.get_settings_json()

@socketio.on('set_frequency')
def on_set_frequency(data):
    data = parse_json(data)
    print(data)
    index = data['node']
    frequency = data['frequency']
    ConfigContext.serverconfig.set_item('NODE', 'FREQ'+str(index), frequency)
    hardwareInterface.set_frequency(index, frequency)
    emit('frequency_set', hardwareInterface.get_frequency_json(index), broadcast=True)

@socketio.on('set_calibration_threshold')
def on_set_calibration_threshold(data):
    print("before the parse")
    data = parse_json(data)
    print(data)
    index = data['node']
    calibration_threshold = data['calibration_threshold']
    ConfigContext.serverconfig.set_item('NODE', 'CT'+str(index), calibration_threshold)
    hardwareInterface.set_calibration_threshold(index, calibration_threshold)
    emit('calibration_threshold_set', hardwareInterface.get_calibration_threshold_json(index), broadcast=True)

@socketio.on('set_calibration_offset')
def on_set_calibration_offset(data):
    print("before the parse")
    data = parse_json(data)
    print(data)
    index = data['node']
    calibration_offset = data['calibration_offset']
    ConfigContext.serverconfig.set_item('NODE', 'CO'+str(index), calibration_offset)
    hardwareInterface.set_calibration_offset(index,calibration_offset)
    emit('calibration_offset_set', hardwareInterface.get_calibration_offset_json(index), broadcast=True)

@socketio.on('set_trigger_threshold')
def on_set_trigger_threshold(data):
    print("before the parse")
    data = parse_json(data)
    index = data['node']
    trigger_threshold = data['trigger_threshold']
    ConfigContext.serverconfig.set_item('NODE', 'TT'+str(index), trigger_threshold)
    hardwareInterface.set_trigger_threshold(index,trigger_threshold)
    emit('trigger_threshold_set', hardwareInterface.get_trigger_threshold_json(index), broadcast=True)

@socketio.on('set_filter_ratio')
def on_set_filter_ratio(data):
    data = parse_json(data)
    print(data)
    filter_ratio = data['filter_ratio']
    hardwareInterface.set_filter_ratio_global(filter_ratio)
    emit('filter_ratio_set', hardwareInterface.get_filter_ratio_json(), broadcast=True)

# Keep this around for a bit.. old version of the api # @socketio.on('reset_auto_calibration')
# def on_reset_auto_calibration():
#     print('reset_auto_calibration all')
#     hardwareInterface.enable_calibration_mode();

@socketio.on('reset_auto_calibration')
def on_reset_auto_calibration(data):
    data = parse_json(data)
    print(data)
    index = data['node']
    if index == -1:
        print('reset_auto_calibration all')
        hardwareInterface.enable_calibration_mode()
    else:
        print('reset_auto_calibration {0}'.format(index))
        hardwareInterface.set_calibration_mode(index, True)

@socketio.on('simulate_pass')
def on_simulate_pass(data):
    data = parse_json(data)
    index = data['node']
    # todo: how should frequency be sent?
    emit('pass_record', {'node': index, 'frequency': hardwareInterface.nodes[index].frequency, 'timestamp': hardwareInterface.milliseconds(), 'lap_time':0 }, broadcast=True)

def pass_record_callback(node, ms_since_lap):
    print('Pass record from {0}{1}: {2}, {3}, {4}'.format(node.index, node.frequency,node.peak_rssi, ms_since_lap, hardwareInterface.milliseconds() - ms_since_lap))
    #TODO: clean this up
    socketio.emit('pass_record', {
        'node': node.index,
        'frequency': node.frequency,
        'timestamp': hardwareInterface.milliseconds() - ms_since_lap,
        'lap_time': node.lap_time,
        'trigger_rssi': node.trigger_rssi,
        'peak_rssi': node.peak_rssi})

hardwareInterface.pass_record_callback = pass_record_callback

def hardware_log_callback(message):
    print(message)
    socketio.emit('hardware_log', message)

hardwareInterface.hardware_log_callback = hardware_log_callback

def heartbeat_thread_function():
    while True:
        socketio.emit('heartbeat', hardwareInterface.get_heartbeat_json())
        gevent.sleep(0.5)


# Return 'DEF_NODE_FWUPDATE_URL' config value; if not set in 'config.json'
#  then return default value based on BASEDIR and server RELEASE_VERSION
def getDefNodeFwUpdateUrl():
    return "../../" + NODE_FW_PATHNAME

@socketio.on('check_bpillfw_file')
def check_bpillfw_file(data):
    fileStr = data['src_file_str']
    logger.info("Checking node firmware file: " + fileStr)
    logger.debug("dChecking node firmware file: " + fileStr)
    dataStr = None
    try:
        dataStr = stm32loader.load_source_file(fileStr, False)
    except Exception as ex:
        socketio.emit('upd_set_info_text', "Error reading firmware file: {}<br><br><br><br>".format(ex))
        logger.debug("Error reading file '{}' in 'check_bpillfw_file()': {}".format(fileStr, ex))
        return
    try:  # find version, processor-type and build-timestamp strings in firmware '.bin' file
        rStr = LTUtils.findPrefixedSubstring(dataStr, hardwareInterface.FW_VERSION_PREFIXSTR, \
                                             hardwareInterface.FW_TEXT_BLOCK_SIZE)
        fwVerStr = rStr if rStr else "(unknown)"
        fwRTypStr = LTUtils.findPrefixedSubstring(dataStr, hardwareInterface.FW_PROCTYPE_PREFIXSTR, \
                                             hardwareInterface.FW_TEXT_BLOCK_SIZE)
        fwTypStr = (fwRTypStr + ", ") if fwRTypStr else ""
        rStr = LTUtils.findPrefixedSubstring(dataStr, hardwareInterface.FW_BUILDDATE_PREFIXSTR, \
                                             hardwareInterface.FW_TEXT_BLOCK_SIZE)
        if rStr:
            fwTimStr = rStr 
            rStr = LTUtils.findPrefixedSubstring(dataStr, hardwareInterface.FW_BUILDTIME_PREFIXSTR, \
                                                 hardwareInterface.FW_TEXT_BLOCK_SIZE)
            if rStr:
                fwTimStr += " " + rStr
        else:   
            fwTimStr = "unknown"
        fileSize = len(dataStr)
        logger.debug("Node update firmware file size={}, version={}, {}build timestamp: {}".\
                     format(fileSize, fwVerStr, fwTypStr, fwTimStr))
        infoStr = "Firmware update file size = {}<br>".format(fileSize) + \
                  "Firmware update version: {} ({}Build timestamp: {})<br><br>".\
                  format(fwVerStr, fwTypStr, fwTimStr)
        info_node = hardwareInterface.get_info_node_obj()
        curNodeStr = info_node.firmware_version_str if info_node else None
        if curNodeStr:
            tsStr = info_node.firmware_timestamp_str
            if tsStr:
                curRTypStr = info_node.firmware_proctype_str
                ptStr = (curRTypStr + ", ") if curRTypStr else ""
                curNodeStr += " ({}Build timestamp: {})".format(ptStr, tsStr)
        else:
            curRTypStr = None
            curNodeStr = "(unknown)"
        infoStr += "Current firmware version: " + curNodeStr
        if fwRTypStr and curRTypStr and fwRTypStr != curRTypStr:
            infoStr += "<br><br><b>Warning</b>: Firmware file processor type ({}) does not match current ({})".\
                        format(fwRTypStr, curRTypStr)
        socketio.emit('upd_set_info_text', infoStr)
        socketio.emit('upd_enable_update_button')
    except Exception as ex:
        socketio.emit('upd_set_info_text', "Error processing firmware file: {}<br><br><br><br>".format(ex))
        logger.exception("Error processing file '{}' in 'check_bpillfw_file()'".format(fileStr))

@socketio.on('do_bpillfw_update')
def do_bpillfw_update(data):
    srcStr = data['src_file_str']
    portStr = hardwareInterface.get_fwupd_serial_name()
    msgStr = "Performing S32_BPill update, port='{}', file: {}".format(portStr, srcStr)
    logger.info(msgStr)
    socketio.emit('upd_messages_init', (msgStr + "\n"))
    stop_background_threads()
    gevent.sleep(0.1)
    try:
        jump_to_node_bootloader()
        hardwareInterface.close_fwupd_serial_port()
        s32Logger = logging.getLogger("stm32loader")
        def doS32Log(msgStr):  # send message to update-messages window and log file
            socketio.emit('upd_messages_append', msgStr)
            gevent.idle()  # do thread yield to allow display updates
            s32Logger.info(msgStr)
            gevent.idle()  # do thread yield to allow display updates
            log.wait_for_queue_empty()
        stm32loader.set_console_output_fn(doS32Log)
        successFlag = stm32loader.flash_file_to_stm32(portStr, srcStr)
        msgStr = "Node update " + ("succeeded; Please power off and on" \
                                   if successFlag else "failed")
        logger.info(msgStr)
        socketio.emit('upd_messages_append', ("\n" + msgStr))
        stm32loader.set_console_output_fn(None)
    except:
        logger.exception("Error in 'do_bpillfw_update()'")

    socketio.emit('upd_messages_finish')  # show 'Close' button
    gevent.sleep(0.2)
    logger.info("Shutting down system after attempting firmware update")
    import os
    os.system('sudo shutdown -h now')
    #os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 

def stop_background_threads():
    try:
        stop_shutdown_button_thread()
        global BACKGROUND_THREADS_ENABLED           
        BACKGROUND_THREADS_ENABLED = False
        global HEARTBEAT_THREAD
        if HEARTBEAT_THREAD:
            logger.info('Stopping heartbeat thread')
            HEARTBEAT_THREAD.kill(block=True, timeout=0.5)
            HEARTBEAT_THREAD = None
        hardwareInterface.stop()
    except: 
        logger.exception("Error stopping background threads")

def jump_to_node_bootloader():
    try:
        hardwareInterface.jump_to_bootloader()
    except Exception:
        logger.error("Error executing jump to node bootloader")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000 ,debug=False)
