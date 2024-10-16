# Technical Notes

The ZippyDecoder decoder is an open-source multi-node timing system that uses the video signals from FPV vehicles to determine when they cross the start/finish line.  The heart of the system is a Raspberry Pi, and each node has a dedicated Arduino Nano and RX5808 module.

The Raspberry Pi runs the Raspbian OS (with desktop), and the ZippyDecoder system uses a server component written in Python.  
The stand-alone-server version uses the '[Flask](http://flask.pocoo.org)' library to serve up web pages to a computer or hand-held device, via a network connection.  

The ZippyDecoder project is hosted on GitHub, here:  https://github.com/RogerBFPV/ZippyDecoder
