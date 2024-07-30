# Hardware Setup Instructions

For general information on the Arduino-nodes version of the timer, see '[doc/Timer Build with Arduinos.md](Timer%20Build%20with%20Arduinos.md)'

(If it seems like one or more RX5808 modules are not responding to frequency changes, if may be that they need the "SPI mod" -- see [here for more info](Timer%20Build%20with%20Arduinos.md#rx5808-video-receivers).)

### Add a Directional RF Shield
A directional RF shield significantly improves the system's ability to reject false passes. See [RF shielding](Shielding%20and%20Course%20Position.md)

-----------------------------

All supported build styles offer full timing accuracy but differ in size, cost, and ease of use.

<br />

## Full-featured S32_BPill

Standard, current build using the STM32 "Blue Pill" in place of individual Arduinos. Recommended for event managers with the available time and resources to acquire parts and complete the build.

- Supports up to 8 receivers 
- Supports all optional hardware features: current sensing, voltage sensing, RTC, buzzer, Status LED
- Ease-of-use features: power switch, shutdown button

<br />

## NuclearHazard Core

Designed for PCB manufacturer to be able to populate components instead of ordering individually. Available for purchase from the board designer.

- Supports up to 8 receivers 
- Lowest cost self-contained build
- Smallest size
- Simplest assembly

[NuclearHazard Core (Prepopulated S32)](NuclearHazardCore/)

<br />

## Delta 5

Existing Delta 5 builds may be used but are not recommended for new builds.

- Supports up to 8 receivers when paired with second PCB 
- Highest cost for required components
- Arduinos must be manually addressed with code modification
- Arduinos must be removed to reprogram

Replace the Delta5 server software using the current RotorHazard server [setup instructions](doc/Software%20Setup.md), ensuring that you complete a [re-flash of the Arduinos](doc/Software%20Setup.md#rotorhazard-node-code).

See Also:<br/>
[doc/Software Setup.md](Software%20Setup.md)<br/>
[doc/User Guide.md](User%20Guide.md)<br/>
