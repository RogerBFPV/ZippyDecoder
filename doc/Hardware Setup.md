# Hardware Setup Instructions

For general information on the Arduino-nodes version of the timer, see '[doc/Timer Build with Arduinos.md](Timer%20Build%20with%20Arduinos.md)'

(If it seems like one or more RX5808 modules are not responding to frequency changes, if may be that they need the "SPI mod" -- see [here for more info](Timer%20Build%20with%20Arduinos.md#rx5808-video-receivers).)

### Add a Directional RF Shield
A directional RF shield significantly improves the system's ability to reject false passes. See [RF shielding](Shielding%20and%20Course%20Position.md)

### WS2812b LED Support

For the [S32_BPill board](../resources/S32_BPill_PCB/README.md) connect to J6 "Pi_LED" (near the middle of the board); pin 1 is ground, pin 2 is signal.

For the [6 Node STM32](../resources/6_Node_BPill_PCB/README.md) board use the 'LEDS' connector.

For the [ZippyDecoder PCB 1.2 board](../resources/PCB/README.md) use the LED OUT connector (beware of overloading the 5V power supply).

For direct wiring to the Pi: The pins in the green box is what were already used by the timer. The pins in the red box is where you connect the signal and ground from the ws2812b LEDs.  The LEDs will require a separate power source.


-----------------------------

See Also:<br/>
[doc/USB Nodes.md](USB%20Nodes.md)<br/>
[doc/Software Setup.md](Software%20Setup.md)<br/>
[doc/User Guide.md](User%20Guide.md)<br/>
[Build Resources (PCB, etc) &#10132;&#xFE0E;](https://github.com/ZippyDecoder/ZippyDecoder/tree/main/resources/README.md)
