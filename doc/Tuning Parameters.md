# Calibration and Sensor Tuning Parameters

- [Introduction](#introduction)
- [Parameters](#parameters)
    - [Trigger Threshold](#trigger-threshold)
    - [Calibration Threshold](#calibration-threshold)
    - [Calibration Offset](#calibration-offset)
- [Tuning](#tuning)
    - [Set the *Trigger Threshold* value](#set-the-trigger-threshold-value)
    - [Set the *Calibration Threshold* value](#set-the-calibration-threshold-value)
    - [Set the *Calibration Offset* value](#set-the-calibration-offset-value)
    - [Tuning](#tuning)
- [Notes](#notes)
- [Troubleshooting](#troubleshooting)
    - [Missing Laps (System usually *Clear*)](#missing-laps-system-usually-clear)
    - [Missing Laps (System usually *Crossing*)](#missing-laps-system-usually-crossing)
    - [Laps register on other parts of a course](#laps-register-on-other-parts-of-a-course)
    - [Many laps register at once](#many-laps-register-at-once)
    - [Laps take a long time to register](#laps-take-a-long-time-to-register)
    - [Node is never *crossing*](#node-is-never-crossing)
    - [Node is never *clear*](#node-is-never-clear)

## Introduction

_If you are having trouble calibrating your timer, be sure you have constructed and placed [RF shielding](Shielding%20and%20Course%20Position.md) correctly._

Each node keeps track of the signal strength (RSSI) on a selected frequency and uses this relative strength to determine whether a transmitter is near the timing gate. The ZippyDecoder timing system allows you to calibrate each node individually so that you can compensate for the behavior and hardware differences across your system and environment.

A node can be *Crossing* or *Clear*. If a node is *Clear*, the system believes a transmitter is not near the timing gate because the RSSI is low. If it is *Crossing*, the system believes a transmitter is passing by the timing gate because the RSSI is high. A lap pass will be recorded once the *Crossing* is finished and the system returns to *Clear*.


## Parameters

### Trigger Threshold 
The system reports this lap when RSSI drops this amount from the peak RSSI detected in that lap.
Smaller values result in the lap being reported immediately exiting the gate. Larger values will result in the quad needing to be farther away before reporting.
If too high, a lap may never report.. 

### Calibration Threshold
The RSSI value needed for the system to begin its first pass calibration to detect this quad. To Low, and you risk the system detecting a peak at very low RSSI. Or in rare cases even a neighboring quad to be mistaken..  Too high, and the system will never complete first pass calibration, and will miss laps.   Set this to be above the noise floor RSSI..
Note that during the race the actual value used to detect crossings is automatically set based on the peak rssi on first pass, and will likely be a value much larger than this.

### Calibration Offset
 Determines how wide of a range of RSSI to consider after the first pass calibration. Smaller gates can use smaller values. Larger gates will need larger values.


## Tuning
Before tuning, power up the timer and keep it running for a few minutes to allow the receiver modules to warm up. The RSSI values tend to increase by a few points as the timer heats up.
Common RSSI values: This are typical, but can vary from build to build..
 *No quads powered on: 35-45 
 *Quads powered on but far away: 35-55 
 *Quads peak during crossing:  90-125 

### Set the *Trigger Threshold* value: 
* 20 is a good starting point

### Set the *Calibration Threshold* value: 
* Set value larger than the RSSI value when quads are on the starting blocks.
* 80 is a good starting point. 
* Calibration Threshold helps to avoid mistkenly detecting a nearby channel.

### Set the *Calibration Offset* value: 
* 30 is a good starting point

## Troubleshooting

### Missing Laps intermittently (Node usually *Clear*)
_Some laps in the race recorded but some did not all. This occurs if the first pass RSSI was very high and Calibration Offset was too low.
* Raise *Calibration Threshold* 

### Missing Laps (Node usually *Crossing*)
_Laps are merged together if **Trigger Threshold** is too to high, because the lap crossing never completes._
* Lower *Trigger Threshold*

### Laps register on other parts of a course
_Extra crossings occur when **Calibration Offset** is too high._
* Lower *Calibration Offset* until *crossings* only begin near the timing gate.

### Many laps register at once
_Too many laps occur when **Trigger Threshold** is too low, because laps are reported too quickly._
* Raise *Trigger Threshold*

### Laps take a long time to register
_Lap recording takes a long time to complete if **Trigger Threshold** is high. This does not affect the accuracy of the recorded time._
* Lower *Trigger Threshold*

### Node is never *crossing*
_Laps will not register if RSSI never reaches **Calibration Threshold**._
* Lower *Calibration Threshold* 

### Node is never *clear*
_Laps will not complete if RSSI never drops low enough to trigger 
* Lower *Trigger Threshold*
