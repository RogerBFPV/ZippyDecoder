#include "config.h"
#include "RssiNode.h"

RssiNode RssiNode::rssiNodeArray[MULTI_RHNODE_MAX];
uint8_t RssiNode::multiRssiNodeCount = 1;
mtime_t RssiNode::lastRX5808BusTimeMs = 0;

RssiNode::RssiNode()
{
    filter = &defaultFilter;
}

void RssiNode::initRx5808Pins(int nIdx)
{
    nodeIndex = nIdx;
    slotIndex = nIdx;
#if STM32_MODE_FLAG
    rx5808DataPin = RX5808_DATA_PIN;  //DATA (CH1) output line to (all) RX5808 modules
    rx5808ClkPin = RX5808_CLK_PIN;    //CLK (CH3) output line to (all) RX5808 modules
    rx5808SelPin = rx5808SelPinForNodeIndex(nIdx);  //SEL (CH2) output line to RX5808 module
    rssiInputPin = rssiInputPinForNodeIndex(nIdx);  //RSSI input from RX5808
#else
    rx5808DataPin = RX5808_DATA_PIN;  //DATA (CH1) output line to RX5808 module
    rx5808SelPin = RX5808_SEL_PIN;    //SEL (CH2) output line to RX5808 module
    rx5808ClkPin = RX5808_CLK_PIN;    //CLK (CH3) output line to RX5808 module
    rssiInputPin = RSSI_INPUT_PIN;    //RSSI input from RX5808
#endif
    pinMode(rx5808DataPin, OUTPUT);   //setup RX5808 pins
    pinMode(rx5808SelPin, OUTPUT);
    pinMode(rx5808ClkPin, OUTPUT);
    digitalWrite(rx5808SelPin, HIGH);
    digitalWrite(rx5808ClkPin, LOW);
    digitalWrite(rx5808DataPin, LOW);
}

// Initialize and set frequency on RX5808 module
void RssiNode::initRxModule()
{
    resetRxModule();
    setRxModuleToFreq(settings.vtxFreq);
}

void RssiNode::copyNodeData(RssiNode *srcPtr)
{
    slotIndex = srcPtr->slotIndex;
    rx5808DataPin = srcPtr->rx5808DataPin;
    rx5808ClkPin = srcPtr->rx5808ClkPin;
    rx5808SelPin = srcPtr->rx5808SelPin;
    rssiInputPin = srcPtr->rssiInputPin;
    rxPoweredDown = srcPtr->rxPoweredDown;
    recentSetFreqFlag = srcPtr->recentSetFreqFlag;
    lastSetFreqTimeMs = srcPtr->lastSetFreqTimeMs;
}

// Set frequency on RX5808 module to given value
void RssiNode::setRxModuleToFreq(uint16_t vtxFreq)
{
    // check if enough time has elapsed since last set freq
    mtime_t timeVal = millis() - lastRX5808BusTimeMs;
    if(timeVal < RX5808_MIN_BUSTIME)
        delay(RX5808_MIN_BUSTIME - timeVal);  // wait until after-bus-delay time is fulfilled

    if (settings.vtxFreq == 1111) // frequency value to power down rx module
    {
        powerDownRxModule();
        rxPoweredDown = true;
        return;
    }
    if (rxPoweredDown)
    {
        resetRxModule();
        rxPoweredDown = false;
    }

    // Get the hex value to send to the rx module
    uint16_t vtxHex = freqMhzToRegVal(vtxFreq);

    // Channel data from the lookup table, 20 bytes of register data are sent, but the
    // MSB 4 bits are zeros register address = 0x1, write, data0-15=vtxHex data15-19=0x0
    rx5808SerialEnableHigh();
    rx5808SerialEnableLow();

    rx5808SerialSendBit1();  // Register 0x1
    rx5808SerialSendBit0();
    rx5808SerialSendBit0();
    rx5808SerialSendBit0();

    rx5808SerialSendBit1();  // Write to register

    // D0-D15, note: loop runs backwards as more efficent on AVR
    uint8_t i;
    for (i = 16; i > 0; i--)
    {
        if (vtxHex & 0x1)
        {  // Is bit high or low?
            rx5808SerialSendBit1();
        }
        else
        {
            rx5808SerialSendBit0();
        }
        vtxHex >>= 1;  // Shift bits along to check the next one
    }

    for (i = 4; i > 0; i--)  // Remaining D16-D19
        rx5808SerialSendBit0();

    rx5808SerialEnableHigh();  // Finished clocking data in
    delay(2);

    digitalWrite(rx5808ClkPin, LOW);
    digitalWrite(rx5808DataPin, LOW);

    recentSetFreqFlag = true;  // indicate need to wait RX5808_MIN_TUNETIME before reading RSSI
    lastRX5808BusTimeMs = lastSetFreqTimeMs = millis();  // mark time of last tune of RX5808 to freq
}

// Read the RSSI value for the current channel
rssi_t RssiNode::rssiRead()
{
    if (recentSetFreqFlag)
    {  // check if RSSI is stable after tune
        mtime_t timeVal = millis() - lastSetFreqTimeMs;
        if(timeVal < RX5808_MIN_TUNETIME)
            delay(RX5808_MIN_TUNETIME - timeVal);  // wait until after-tune-delay time is fulfilled
        recentSetFreqFlag = false;  // don't need to check again until next freq change
    }

    // reads 5V value as 0-1023, RX5808 is 3.3V powered so RSSI pin will never output the full range
    int raw = analogRead(rssiInputPin);
    // clamp upper range to fit scaling
    if (raw > 0x01FF)
        raw = 0x01FF;
    // rescale to fit into a byte and remove some jitter
    return raw >> 1;
}

void RssiNode::rx5808SerialSendBit1()
{
    digitalWrite(rx5808DataPin, HIGH);
    delayMicroseconds(300);
    digitalWrite(rx5808ClkPin, HIGH);
    delayMicroseconds(300);
    digitalWrite(rx5808ClkPin, LOW);
    delayMicroseconds(300);
}

void RssiNode::rx5808SerialSendBit0()
{
    digitalWrite(rx5808DataPin, LOW);
    delayMicroseconds(300);
    digitalWrite(rx5808ClkPin, HIGH);
    delayMicroseconds(300);
    digitalWrite(rx5808ClkPin, LOW);
    delayMicroseconds(300);
}

void RssiNode::rx5808SerialEnableLow()
{
    digitalWrite(rx5808SelPin, LOW);
    delayMicroseconds(200);
}

void RssiNode::rx5808SerialEnableHigh()
{
    digitalWrite(rx5808SelPin, HIGH);
    delayMicroseconds(200);
}

// Reset rx5808 module to wake up from power down
void RssiNode::resetRxModule()
{
    rx5808SerialEnableHigh();
    rx5808SerialEnableLow();

    rx5808SerialSendBit1();  // Register 0xF
    rx5808SerialSendBit1();
    rx5808SerialSendBit1();
    rx5808SerialSendBit1();

    rx5808SerialSendBit1();  // Write to register

    for (uint8_t i = 20; i > 0; i--)
        rx5808SerialSendBit0();

    rx5808SerialEnableHigh();  // Finished clocking data in

    setupRxModule();
}

// Set power options on the rx5808 module
void RssiNode::setRxModulePower(uint32_t options)
{
    rx5808SerialEnableHigh();
    rx5808SerialEnableLow();

    rx5808SerialSendBit0();  // Register 0xA
    rx5808SerialSendBit1();
    rx5808SerialSendBit0();
    rx5808SerialSendBit1();

    rx5808SerialSendBit1();  // Write to register

    for (uint8_t i = 20; i > 0; i--)
    {
        if (options & 0x1)
        {  // Is bit high or low?
            rx5808SerialSendBit1();
        }
        else
        {
            rx5808SerialSendBit0();
        }
        options >>= 1;  // Shift bits along to check the next one
    }

    rx5808SerialEnableHigh();  // Finished clocking data in

    digitalWrite(rx5808DataPin, LOW);
}

// Power down rx5808 module
void RssiNode::powerDownRxModule()
{
    setRxModulePower(0b11111111111111111111);
}

// Set up rx5808 module (disabling unused features to save some power)
void RssiNode::setupRxModule()
{
    setRxModulePower(0b11010000110111110011);
}

// Calculate rx5808 register hex value for given frequency in MHz
uint16_t RssiNode::freqMhzToRegVal(uint16_t freqInMhz)
{
    uint16_t tf, N, A;
    tf = (freqInMhz - 479) / 2;
    N = tf / 32;
    A = tf % 32;
    return (N << (uint16_t)7) + A;
}


void RssiNode::rssiSetFilter(Filter<rssi_t> *f)
{
    filter = f;
}

void RssiNode::rssiInit()
{
    state.lastloopMicros = micros();
}

bool RssiNode::rssiStateValid()
{
    return 0 <= state.rssi && state.rssi <= state.nodeRssiPeak;
}

void RssiNode::rssiStateReset()
{
    state.crossing = false;
    state.nodeRssiPeak = 0;
}

bool RssiNode::rssiProcessValue(mtime_t millis, rssi_t rssiVal)
{
    filter->addRawValue(millis, rssiVal);

    if (filter->isFilled() && state.activatedFlag)
    {  //don't start operations until after first WRITE_FREQUENCY command is received

        state.lastRssi = state.rssi;
        state.rssi = filter->getFilteredValue();
        state.rssiTimestamp = filter->getFilterTimestamp();
        //if (state.rssiTrigger > 0) {
                if (!state.crossing && state.rssi > state.rssiTrigger && state.rssi >= settings.calibrationThreshold) {
                       state.crossing = true; // Quad is going through the gate
                       digitalWrite(13,HIGH);
                }


                if (state.crossing) {
                        // Find the peak rssi and the time it occured during a crossing event
                        if (state.rssi > state.nodeRssiPeak) {
                           state.nodeRssiPeak = state.rssi;
                           state.nodeRssiPeakTimestamp = state.rssiTimestamp;
                        }else if(state.nodeRssiPeak == state.rssi){
                            // if by some miracle the peak is the same, then creep the timestamp forward
                            //  because the bubble is very big
                            state.nodeRssiPeakTimestamp = (state.rssiTimestamp + state.nodeRssiPeakTimestamp)/2;
                        }

                        int triggerThreshold = settings.triggerThreshold;

                        // If in calibration mode, keep raising the trigger value
                        if (state.calibrationMode) {
                                if(state.rssiTrigger < (state.rssi - settings.calibrationOffset)){
                                    state.rssiTrigger = state.rssi - settings.calibrationOffset;
                                }
                        }else{
                              //just in case first calibration was artifically low, allow
                              // the trigger to slide upward. note that the calibration offset
                              // should be wide enough to ensure passes dont get missed
                              //  REMOVED this: instead we will have the user define the lower calibrationThreshold
                              //if (state.rssiTrigger < state.rssi - settings.calibrationOffset){
                              //   state.rssiTrigger = state.rssi - settings.calibrationOffset;
                              //}
                        }

                        if(state.nodeRssiPeak == state.rssi){
                            // if by some miracle the peak is the same, then creep the timestamp forward
                            //  because the bubble is very big
                            state.nodeRssiPeakTimestamp = (state.rssiTimestamp + state.nodeRssiPeakTimestamp)/2;
                        }

                        state.nodeRssiPeak = max(state.nodeRssiPeak, state.rssi);

                        // Make sure the threshold does not put the trigger below 0 RSSI
                        // See if we have left the gate
                        if ((state.rssiTrigger > triggerThreshold) &&
                                (state.rssi < (state.rssiTrigger - triggerThreshold))) {
                                rssiEndCrossing();
                        }
                }
           //}
    }

    // Calculate the time it takes to run the main loop
    utime_t loopMicros = micros();
    state.loopTimeMicros = loopMicros - state.lastloopMicros;
    state.lastloopMicros = loopMicros;

    return state.crossing;
}

// Function called when crossing ends (by RSSI or I2C command)
void RssiNode::rssiEndCrossing()
{
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE)
    {
                                lastPass.nodeRssiPeak = state.nodeRssiPeak;
                                lastPass.nodeRssiLaptime = state.nodeRssiPeakTimestamp - lastPass.nodeRssiPeakTimestamp;
                                lastPass.nodeRssiPeakTimestamp = state.nodeRssiPeakTimestamp;
                                lastPass.lap = lastPass.lap + 1;
    }

    state.crossing = false;
    state.calibrationMode = false;
    state.nodeRssiPeak = 0;
    digitalWrite(13,LOW);
}

void RssiNode::rssiAutoCalibrate()
{
    state.crossing = false;
    state.calibrationMode = true;
    state.nodeRssiPeak = 0;
    state.rssiTrigger = state.rssi;
    digitalWrite(13,LOW);
}


#if STM32_MODE_FLAG

int RssiNode::rx5808SelPinForNodeIndex(int nIdx)
{
    switch (nIdx)
    {
        case 1:
            return RX5808_SEL1_PIN;
        case 2:
            return RX5808_SEL2_PIN;
        case 3:
            return RX5808_SEL3_PIN;
        case 4:
            return RX5808_SEL4_PIN;
        case 5:
            return RX5808_SEL5_PIN;
        case 6:
            return RX5808_SEL6_PIN;
        case 7:
            return RX5808_SEL7_PIN;
        default:
            return RX5808_SEL0_PIN;
    }
}

int RssiNode::rssiInputPinForNodeIndex(int nIdx)
{
    switch (nIdx)
    {
        case 1:
            return RSSI_INPUT1_PIN;
        case 2:
            return RSSI_INPUT2_PIN;
        case 3:
            return RSSI_INPUT3_PIN;
        case 4:
            return RSSI_INPUT4_PIN;
        case 5:
            return RSSI_INPUT5_PIN;
        case 6:
            return RSSI_INPUT6_PIN;
        case 7:
            return RSSI_INPUT7_PIN;
        default:
            return RSSI_INPUT0_PIN;
    }
}

#endif
