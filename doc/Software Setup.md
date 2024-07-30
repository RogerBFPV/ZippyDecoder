# Software Setup Instructions

- [Introduction](#introduction)
- [Automated Install ZippyDecoder on a Raspberry Pi](#automated-install-zippydecoder-on-a-raspberry-pi)
- [Manual Install ZippyDecoder on a Raspberry Pi](#manual-install-zippydecoder-on-a-raspberry-pi)
- [Running the ZippyDecoder Server](#running-the-zippydecoder-server)
- [ZippyDecoder Node Code](#zippydecoder-node-code)
- [Other Operating Systems](#other-operating-systems)
- [Network Setup](#network-setup)
- [Logging](#logging)
- [Update Existing ZippyDecoder](#update-existing-installation-of-zippydecoder)

## Introduction

The central software component of the ZippyDecoder system is its server, written in Python, which operates its functions and serves up web pages to browsers. In a standard setup, the server is run on a [Raspberry Pi](https://www.raspberrypi.org). (It is also possible to run ZippyDecoder on other types of hardware -- see the [Other Operating Systems](#otheros) section below.)

Once the server is setup and running, see the ZippyDecoder Race Timer [User Guide](User%20Guide.md) for further instructions and setup tips.

If you've previously followed these steps to Install and simply want to refresh the existing installation see the section 
[Update Existing ZippyDecoder](#update-existing-installation-of-zippydecoder)


----------------------------------------------------------------------------
## Automated Install ZippyDecoder on a Raspberry Pi
Once you've installed the Pi OS with the imager, you can run the command below which should automate steps 1-9 of the manual install.
 Note that the username on your Pi OS installation must be NuclearQuads.
 It is also recommended to start out with imager settings to connect to your local wifi, which can help setup.
```
curl -s https://rogerbfpv.github.io/ZippyDecoder/zdnqpisetup.sh | bash -s nuclearwifi
```
The above does enable the local hotspot service. 
To disable the hotspot, do 
```
sudo systemctl disable hotspot.service
```

Skip now to the section to install the Node code - [ZippyDecoder Node Code](#zippydecoder-node-code)

----------------------------------------------------------------------------
## Manual Install ZippyDecoder on a Raspberry Pi

### 1. Install the Raspberry Pi Operating System

Note: Many of the setup commands below require that the Rasperry Pi has internet access.

Install the Raspberry Pi OS, following the official instructions: https://www.raspberrypi.org/help

The standard-recommended setup is to use a Raspberry Pi 3, Pi 4 or Pi 5 board, install the [Raspberry Pi OS](https://www.raspberrypi.org/software/operating-systems/#raspberry-pi-os-32-bit) (Desktop), and configure it with a user named "pi". Also if using the 'Raspberry Pi Imager', Apply custimisation settings, select services, and enable SSH with password authentication. 



Tip: Any time you intend to use a monitor (via HDMI) with the Raspberry Pi, connect it before powering up the Pi. Connecting the monitor after power up tends to not work (blank screen).


### 2. Configure Interface Options

(The options may be configured using step 2a or 2b below.)

#### 2a. Configure interface options using the desktop
If Raspberry Pi OS with Desktop was installed, the interface options may be configured via "Preferences" | "Raspberry Pi Configuration" | "Interfaces":
* Enable SSH, SPI, I2C, and 'Serial Port'
* Disable 'Serial Console'
* For remote access to the desktop (using a program like [RealVNC viewer](https://www.realvnc.com/en/connect/download/viewer)), enable VNC

#### 2b. Configure interface options using a terminal window
If the Pi OS Desktop is not available, the interface options may be configured using the following command:
```
sudo raspi-config
```
* Select 'Interface Options' and enable: SSH, SPI, and I2C
* Select 'Interface Options' | 'Serial Port', and configure:
  * "login shell accessible serial": No
  * "serial port hardware enabled": Yes


### 3. Apply Changes to the 'boot' _config.txt_ file
Open a terminal window and enter:
```
if [ -f "/boot/firmware/config.txt" ]; then sudo nano /boot/firmware/config.txt; else sudo nano /boot/config.txt; fi
```
Add the following lines to the end of the file:
```
dtparam=i2c_baudrate=75000
dtoverlay=miniuart-bt
```
If the Raspberry Pi in use is a Pi 3 model or older (not a Pi 4 or 5) then add this line:
```
core_freq=250
```
<a id="s32btconfig"></a>If your hardware is the S32_BPill setup with [shutdown button](Shutdown%20Button.md) and AUX LED then add these lines:
```
dtoverlay=act-led,gpio=24
dtparam=act_led_trigger=heartbeat
```
If the Raspberry Pi in use is a Pi 4 model or older (not a Pi 5) and your hardware is the S32_BPill setup with [shutdown button](Shutdown%20Button.md) then add this line:
```
dtoverlay=gpio-shutdown,gpio_pin=18,debounce=5000
```
If the Raspberry Pi in use is a Pi 5 model then add these lines:
```
dtoverlay=uart0-pi5
dtoverlay=i2c1-pi5
```
Save and exit the editor (CTRL-X, Y, ENTER)

*Notes:*

On newer versions of the Raspberry Pi OS, the boot-config file location is "/boot/firmware/config.txt". On older versions it is "/boot/config.txt".

The first line sets the transfer rate on the I2C bus (which is used to communicate with the Arduino node processors).

The "dtoverlay=miniuart-bt" line moves the high performance UART from the Bluetooth device to the GPIO pins, which is needed for setups like the S32_BPill that use the serial port as the communications channel to the nodes.

The "core_freq" line fixes a potential variable clock-rate issue, described [here](https://www.abelectronics.co.uk/kb/article/1089/i2c--smbus-and-raspbian-stretch-linux). If a Raspberry Pi 4 or Pi 5 is being used, the "core_freq" line should be omitted (as per the Raspberry Pi documentation [here](https://www.raspberrypi.org/documentation/configuration/config-txt/overclocking.md)).

For the S32_BPill setup, the "dtoverlay=act-led,gpio=24" and "dtparam=act_led_trigger=heartbeat" lines configure a Raspberry-Pi-heartbeat signal that the BPill processor monitors to track the status of the Pi. The "dtoverlay=gpio-shutdown..." line makes it so the shutdown button still operates if the ZippyDecoder server is not running.

If the Raspberry Pi 5 is being used, the "dtoverlay=uart0-pi5" and "dtoverlay=i2c1-pi5" lines configure the devices to operate similar to how they do with the Pi 3 & 4. 


### 4. Perform System Update
Using a terminal window, do a system update and upgrade (this can take a few minutes):
```
sudo apt update && sudo apt upgrade
```

<a id="python"></a>
### 5. Install Python
Using a terminal window, install Python and the Python drivers for the GPIO:
```
sudo apt install python3-dev python3-venv libffi-dev python3-smbus build-essential python3-pip git scons swig python3-rpi.gpio
```

To disable any previous services, such as rotorohazard (so it no longer runs when the system starts up), enter:
```
sudo systemctl disable rotorhazard.service
```

### 6. Reboot System
After the above setup steps are performed, the system should be rebooted by entering the following using a terminal window:
```
sudo reboot
```

### 7. Install the ZippyDecoder Server

```bash
cd ~
git clone https://github.com/RogerBFPV/ZippyDecoder.git
```

Enter the following commands to setup the Python virtual environment:
```
cd ZippyDecoder
python -m venv --system-site-packages .venv
```
Configure the user shell to automatically activate the Python virtual environment by entering the command `nano .bashrc` to edit the ".bashrc" file and adding the following lines to the end of the file:
```
VIRTUAL_ENV_DISABLE_PROMPT=1
source ~/ZippyDecoder/.venv/bin/activate 
```

Install the ZippyDecoder server dependencies (be patient, this may take a few minutes):

```bash
cd ~/ZippyDecoder/src/server
pip install -r requirements.txt
```

### 8. Configuration File
When the ZippyDecoder server is run for the first time, it will create (in the "src/server" directory) a "config.json" file.  The file will contain default values, including these:
```
"ADMIN_USERNAME": "admin",
"ADMIN_PASSWORD": "zippyd"
```
These are the login credentials you will need to enter in (to the browser popup window) to access the pages.

The "config.json" file may be edited to alter the configuration settings, but this must only be done while the ZippyDecoder server is not running (otherwise the changes will be overwritten). When the server starts up, if it detects that the "config.json" has been updated, it will load the settings and then create a backup copy of the file (with a filename in the form "config_bkp_YYYYMMDD_hhmmss.json").

Note that the contents of the "config.json" file must in valid JSON format. A validator utility like [JSONLint](https://jsonlint.com/) can be used to check for syntax errors.

----------------------------------------------------------------------------

## Running the ZippyDecoder Server

The following instructions will start the ZippyDecoder server on the Raspberry Pi, allowing full control and configuration of the system to run races and save lap times.

### Manual Start

Open a terminal window and enter the following:
```bash
cd ~/ZippyDecoder/src/server
python server.py
```
The server may be stopped by hitting Ctrl-C

Once the server is running, its web-GUI interface may be accessed in a browser via http://xx.xx.xx.xx:5000 ; see the [Connect to the Server](User%20Guide.md#connect-to-the-server) section in the [User Guide](User%20Guide.md) for more information.

### 9. Start on Boot

To configure the system to automatically start the ZippyDecoder server when booting up:

Create a service file:
```bash
sudo nano /lib/systemd/system/zippydecoder.service
```

Copy and paste the following contents into the file:
```bash
[Unit]
Description=ZippyDecoder Server
After=multi-user.target

[Service]
User=pi
WorkingDirectory=/home/pi/ZippyDecoder/src/server
ExecStart=/home/pi/ZippyDecoder/.venv/bin/python server.py

[Install]
WantedBy=multi-user.target
```

*Note*: If the username was configured as something other than "pi" during the Operating System setup, be sure to change the value `pi` in `User`, `WorkingDirectory` and `ExecStart` to match your username. For NuclearQuads this may be NuclearQuads username.

Save and exit (CTRL-X, Y, ENTER)

Enter the following command to update the service-file permissions:
```
sudo chmod 644 /lib/systemd/system/zippydecoder.service
```

Enter these commands to enable the service:
```
sudo systemctl daemon-reload
sudo systemctl enable zippydecoder.service
```
The service may now be started manually by entering the command `sudo systemctl start zippydecoder`, and should start up automatically when the Raspberry Pi is started up.

### Stopping the Server Service
If the ZippyDecoder server was started as a service during the boot, it may be stopped with a command like this:
```
sudo systemctl stop zippydecoder
```
To disable the service (so it no longer runs when the system starts up), enter:
```
sudo systemctl disable zippydecoder.service
```
To query the status of the service:
```
sudo systemctl status zippydecoded.service
```
If the service is running then the output will contain `Active: active (running)`. Hit the 'Q' key to exit the status command.


### Shutting Down the System
A system shutdown should always be performed before unplugging the power, either by clicking on the 'Shutdown' button on the 'Settings' page on the web GUI, or by entering the following in a terminal:
```
sudo shutdown now
```

----------------------------------------------------------------------------

## ZippyDecoder Node Code

The firmware for the ZippyDecoder nodes will need to be installed (or updated). The nodes can be Arduino based (with an Arduino processor for each node channel), or use the multi-node S32_BPill board (with a single STM32F1 processor running 1-8 channels).

For Arduino-based node boards, see the '[src/node/readme_Arduino.md](../src/node/readme_Arduino.md)' file for more information and instructions for installing the node firmware code.

For the S32_BPill board, the recommended method for installing the currently-released node firmware is to use the `Update Nodes` button on the ZippyDecoder web GUI.<br>


The "dtoverlay=miniuart-bt" line needs to have been added to the 'boot' _config.txt_ file for the flash-update to succeed (see instructions above).<br>

The node-code version may be viewed via the Update Nodes button. 

----------------------------------------------------------------------------

The ZippyDecoder server defaults to port 5000, as this is necessary for some 3rd party integrations.

----------------------------------------------------------------------------

<a id="otheros"></a>
## Other Operating Systems

The ZippyDecoder server may be run on any computer with an operating system that supports Python but will only support a Mock interface, not real node detection. 

**To install the ZippyDecoder server on these systems:**

1. If the computer does not already have Python installed, download and install Python from https://www.python.org/downloads . The minimum version of Python needed for ZippyDecoder is 3.8. To check if Python is installed and the version, open up a command prompt and enter ```python --version```

2. From the ZippyDecoder [Releases page on github](https://github.com/ZippyDecoder/ZippyDecoder/releases), download the "Source code (zip)" file.

3. Unzip the downloaded file into a directory (aka folder) on the computer.

4. Open up a command prompt and navigate to the topmost ZippyDecoder directory.

5. Create a Python virtual environment ('venv') by entering: ```python -m venv --system-site-packages .venv```

6. Activate the Python virtual environment ('venv'):

  * On a Windows system the command to use will likely be: ```.venv\Scripts\activate.bat```

  * On a Linux system the command to use will likely be: ```source .venv/bin/activate```

7. Using the same command prompt, navigate to the ```src/server``` directory in the ZippyDecoder files (using the 'cd' command).

8. Install the ZippyDecoder server dependencies using the 'reqsNonPi.txt' file, using one of the commands below. (Note that this command may require administrator access to the computer, and the command may take a few minutes to finish).

  * On a Windows system the command to use will likely be:<br/>```python -m pip install -r reqsNonPi.txt```<br>

Note: If the above command fails with a message like "error: Microsoft Visual C++ 14.0 is required", the "Desktop development with C++" Tools may be downloaded (from [here](https://aka.ms/vs/17/release/vs_BuildTools.exe)) and installed to satisfy the requirement.<br>

  * On a Linux system the command to use will likely be:<br/>```pip install -r reqsNonPi.txt```


**To run the ZippyDecoder server on these systems:**

1. Open up a command prompt and navigate to the topmost ZippyDecoder directory.

2. Activate the Python virtual environment ('venv')
  * On a Windows system the command to use will likely be: ```.venv\Scripts\activate.bat```

  * On a Linux system the command to use will likely be: ```source .venv/bin/activate```

3. Using the same command prompt, navigate to the ```src/server``` directory.

4. Enter: ```python server.py```

5. If the server starts up properly, you should see various log messages, including one like this:
    ```
    Running http server at port 5000
    ```

1. The server may be stopped by hitting Ctrl-C


If no hardware nodes are configured, the server will operate using simulated (mock) nodes. In this mode the web-GUI interface may be explored and tested.

To view the web-GUI interface, open up a web browser and enter into the address bar: ```localhost:5000``` (If the HTTP_PORT value in the configuration has been changed then use that value instead of 5000). If the server is running then the ZippyDecoder main page should appear. 

**To update an existing installation:**

1. From the ZippyDecoder [Releases page on github](https://github.com/ZippyDecoder/ZippyDecoder/releases), download the "Source code (zip)" file.

2. Unzip the downloaded file into the ZippyDecoder directory (aka folder) on the computer, overwriting the existing version.

3. Using the command prompt, navigate to the topmost ZippyDecoder directory.

4. Activate the Python virtual environment ('venv'):

  * On a Windows system the command to use will likely be: ```.venv\Scripts\activate.bat```

  * On a Linux system the command to use will likely be: ```source .venv/bin/activate```

5. Using the command prompt, navigate to the ```src/server``` directory.

6. Enter the update command:

  * On a Windows system the command to use will likely be:<br/>```python -m pip install --upgrade --no-cache-dir -r reqsNonPi.txt```

  * On a Linux system the command to use will likely be:<br/>```pip install --upgrade --no-cache-dir -r reqsNonPi.txt```
<br>

----------------------------------------------------------------------------
## Network Setup
* If the system connects to a local wifi, then it will not create a local hotspot. Use the admin console to your WiFi router to determine the IP address assigned..
* If the system is connected via ethernet to a local router, use the router console to determine the ip address assigned.
* If there is no local Wifi, and no Ethernet, then the system should have created a local hotspot:
 SSID: NuclearQuads
 password: nuclearhazard
 Connect your computer to this router, and the IP address should be 10.42.0.1


 Connect to the system and login via ssh.
```
ssh NuclearQuads@10.42.0.1 (or your ip address
```

 Run the command
```
sudo nmtui
```
And configure the network settings

----------------------------------------------------------------------------

<a id="logging"></a>
## Logging

The ZippyDecoder server generates "log" messages containing information about its operations. Below is a sample configuration for logging:

```
    "LOGGING": {
        "CONSOLE_LEVEL": "INFO",
        "SYSLOG_LEVEL": "NONE",
        "FILELOG_LEVEL": "INFO",
        "FILELOG_NUM_KEEP": 30,
        "CONSOLE_STREAM": "stdout"
    }
```
The following log levels may be specified:  DEBUG, INFO, WARNING, WARN, ERROR, FATAL, CRITICAL, NONE

If the FILELOG_LEVEL value is not NONE then the server will generate log files in the `src/server/logs` directory. A new log file is created each time the server starts, with each file having a unique name based on the current date and time (i.e., "rh_20200621_181239.log"). Setting FILELOG_LEVEL to DEBUG will result in more detailed log messages being stored in the log file, which can be useful when debugging problems.

The FILELOG_NUM_KEEP value is the number of log files to keep; the rest will be deleted (oldest first).

The CONSOLE_STREAM value may be "stdout" or "stderr".

If the SYSLOG_LEVEL value is not NONE then the server will send log messages to the logging utility built into the host operating system.

The current Server Log may be displayed via the "View Server Log" item in the drop-down menu. The displayed log is "live" in that it will update as new messages are generated. The log can be displayed in a separate window by clicking on the "View Server Log" menu item with the right-mouse button and selecting the "Open Link in New Window" (or similar) option.

Clicking on the "Select Text" button will select all the displayed log text, which may then be copied and pasted. Clicking on the "Download Logs" button will create and download a '.zip' archive file containing all available log files and the current configuration and database files. The '.zip' archive file can also be generated by running the server with the following command:  `python server.py --ziplogs`

**When reporting issues, using the "Download Logs" button and including the generated '.zip' file is highly recommended.**

When troubleshooting, another place to check for error messages is the system log file, which may be viewed with a command like: `journalctl -n 1000`


<br/>

----------------------------------------------------------------------------

### Update existing installation of ZippyDecoder
If you have ZippyDecoder already installed and just want to refresh its code
```
cd ~/ZippyDecoder
git pull origin main
```
 

-----------------------------

See Also:<br/>
[doc/Hardware Setup.md](Hardware%20Setup.md)<br/>
[doc/User Guide.md](User%20Guide.md)<br/>
