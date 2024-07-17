# ZippyDecoder User Guide

- [Initial Setup](#initial-setup)
    - [Hardware and Software Setup](#hardware-and-software-setup)
    - [Connect to the Server](#connect-to-the-server)

## Initial Setup

### Hardware and Software Setup
Follow the instructions here if not done already:<br>
[Hardware Setup](Hardware%20Setup.md)<br>
[Software Setup](Software%20Setup.md)<br>
[RF shielding](Shielding%20and%20Course%20Position.md)

### Connect 
In LiveTime Scoring engine, select Decoders, add the decoder, and select 'ZippyDecoder'  as the type of decoder. 

A computer, phone or tablet may be used to interact with the race timer by launching a web browser and entering the IP address of the Raspberry Pi. The Raspberry Pi may be connected using an ethernet cable, or to an available WiFi network. If the IP address of the Pi is not known, it may be viewed using the terminal command "ifconfig", and it can configured to a static value on the Pi desktop via the "Network Preferences." If the Pi is connected to a WiFi network, its IP address may be found in the 'Clients' list on the admin page for the network's router.

```
XXX.XXX.XXX.XXX:5000
```

Generally this web interface never needs to be used unless your updating the firmware of the BPill stm32 node. 
It also provides a mechanism to tune nodes, and see RSSI values. However these operations can be handled from the LiveTime Scoring Engine application.

<br/>

-----------------------------

See Also:<br/>
[doc/Tuning Parameters.md](Tuning%20Parameters.md)<br/>
[doc/Software Setup.md](Software%20Setup.md)<br/>
[doc/Hardware Setup.md](Hardware%20Setup.md)<br/>
[Build Resources (PCB, etc) &#10132;&#xFE0E;](https://github.com/ZippyDecoder/ZippyDecoder/tree/main/resources/README.md)
