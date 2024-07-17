#include "config.h"
#include "RssiNode.h"
#include "commands.h"

#ifdef __TEST__
  static uint8_t i2cAddress = 0x08;
#else
#if !STM32_MODE_FLAG
  extern uint8_t i2cAddress;
#else
  void doJumpToBootloader();
#endif
#endif

// informational strings (defined in 'rhnode.cpp')
extern const char *firmwareVersionString;    // version string
extern const char *firmwareBuildDateString;  // build date/time strings
extern const char *firmwareBuildTimeString;
extern const char *firmwareProcTypeString;   // node processor type

// Handle status message sent from server (defined in 'rhnode.cpp')
void handleStatusMessage(byte msgTypeVal, byte msgDataVal);

uint8_t settingChangedFlags = 0;

RssiNode *cmdRssiNodePtr = &(RssiNode::rssiNodeArray[0]);  //current RssiNode for commands

RssiNode *getCmdRssiNodePtr()
{
    return cmdRssiNodePtr;
}

byte Message::getPayloadSize()
{
    byte size;
    switch (command)
    {
        case WRITE_FREQUENCY:
            size = 2;
            break;

        case WRITE_CALIBRATION_MODE:  
            size = 1;
            break;

        case WRITE_TRIGGER_THRESHOLD:  
            size = 1;
            break;

        case WRITE_CALIBRATION_THRESHOLD:  
            size = 1;
            break;

        case WRITE_CALIBRATION_OFFSET:  
            size = 1;
            break;

        case SEND_STATUS_MESSAGE:  // status message sent from server to node
            size = 2;
            break;

        case FORCE_END_CROSSING:  // kill current crossing flag regardless of RSSI value
            size = 1;
            break;

        case RESET_PAIRED_NODE:  // reset paired node for ISP
            size = 1;
            break;

        case WRITE_CURNODE_INDEX:  // index of current node for this processor
            size = 1;
            break;

        case JUMP_TO_BOOTLOADER:  // jump to bootloader for flash update
            size = 1;
            break;

        default:  // invalid command
            LOG_ERROR("Invalid write command: ", command, HEX);
            size = -1;
    }
    return size;
}

// Node reset for ISP; resets other node wired to this node's reset pin
void resetPairedNode(int pinState)
{
#if !STM32_MODE_FLAG
    if (pinState)
    {
        pinMode(NODE_RESET_PIN, INPUT_PULLUP);
    }
    else
    {
        pinMode(NODE_RESET_PIN, OUTPUT);
        digitalWrite(NODE_RESET_PIN, LOW);
    }
#endif
}

// Generic IO write command handler
void Message::handleWriteCommand(bool serialFlag)
{
    uint8_t u8val;
    uint16_t u16val;
    rssi_t rssiVal;
    uint8_t nIdx;

    buffer.flipForRead();
    bool actFlag = true;

    switch (command)
    {
        case WRITE_FREQUENCY:
            u16val = buffer.read16();
            if (u16val >= MIN_FREQ && u16val <= MAX_FREQ)
            {
                if (u16val != cmdRssiNodePtr->getVtxFreq())
                {
                    cmdRssiNodePtr->setVtxFreq(u16val);
                    settingChangedFlags |= FREQ_CHANGED;
#if STM32_MODE_FLAG
                    cmdRssiNodePtr->rssiStateReset();  // restart rssi peak tracking for node
#endif
                }
                settingChangedFlags |= FREQ_SET;
#if STM32_MODE_FLAG  // need to wait here for completion to avoid data overruns
                cmdRssiNodePtr->setRxModuleToFreq(u16val);
                cmdRssiNodePtr->setActivatedFlag(true);
#endif
            }
            break;

        case WRITE_CALIBRATION_MODE:  // signal to autocalibrate now 
                cmdRssiNodePtr->rssiAutoCalibrate();
            break;

        case WRITE_CALIBRATION_THRESHOLD:  // lap pass begins when RSSI is at or above this level
            rssiVal = ioBufferReadRssi(buffer);
            if (rssiVal != cmdRssiNodePtr->getCalibrationThreshold())
            {
                cmdRssiNodePtr->setCalibrationThreshold(rssiVal);
                settingChangedFlags |= CT_CHANGED;
            }
            break;

        case WRITE_TRIGGER_THRESHOLD:  
            rssiVal = ioBufferReadRssi(buffer);
            if (rssiVal != cmdRssiNodePtr->getTriggerThreshold())
            {
                cmdRssiNodePtr->setTriggerThreshold(rssiVal);
                settingChangedFlags |= TT_CHANGED;
            }
            break;

        case WRITE_CALIBRATION_OFFSET:  
            rssiVal = ioBufferReadRssi(buffer);
            if (rssiVal != cmdRssiNodePtr->getCalibrationOffset())
            {
                cmdRssiNodePtr->setCalibrationOffset(rssiVal);
                settingChangedFlags |= CO_CHANGED;
            }
            break;

        case WRITE_CURNODE_INDEX:  // index of current node for this processor
            nIdx = buffer.read8();
            if (nIdx < RssiNode::multiRssiNodeCount && nIdx != cmdRssiNodePtr->getNodeIndex())
                cmdRssiNodePtr = &(RssiNode::rssiNodeArray[nIdx]);
            break;

        case SEND_STATUS_MESSAGE:  // status message sent from server to node
            u16val = buffer.read16();  // upper byte is message type, lower byte is data
            handleStatusMessage((byte)(u16val >> 8), (byte)(u16val & 0x00FF));
            break;

        case FORCE_END_CROSSING:  // kill current crossing flag regardless of RSSI value
            cmdRssiNodePtr->rssiEndCrossing();
            break;

        case RESET_PAIRED_NODE:  // reset paired node for ISP
            u8val = buffer.read8();
            resetPairedNode(u8val);
            break;

        case JUMP_TO_BOOTLOADER:  // jump to bootloader for flash update
#if STM32_MODE_FLAG
            doJumpToBootloader();
#endif
            break;

        default:
            LOG_ERROR("Invalid write command: ", command, HEX);
            actFlag = false;  // not valid activity
    }

    // indicate communications activity detected
    if (actFlag)
    {
        settingChangedFlags |= COMM_ACTIVITY;
        if (serialFlag)
            settingChangedFlags |= SERIAL_CMD_MSG;
    }

    command = 0;  // Clear previous command
}


// Generic IO read command handler
void Message::handleReadCommand(bool serialFlag)
{
    buffer.flipForWrite();
    bool actFlag = true;

    switch (command)
    {
        case READ_ADDRESS:
#if !STM32_MODE_FLAG
            buffer.write8(i2cAddress);
#else
            buffer.write8((uint8_t)0);
#endif
            break;

        case READ_FREQUENCY:
            buffer.write16(cmdRssiNodePtr->getVtxFreq());
            break;

        case READ_LAP_STATS:  // deprecated; use READ_LAP_PASS_STATS and READ_LAP_EXTREMUMS
            {
                mtime_t timeNowVal = millis();
                handleReadLapPassStats(timeNowVal);
                settingChangedFlags |= LAPSTATS_READ;
            }
            break;

        case READ_LAP_PASS_STATS:
            handleReadLapPassStats(millis());
            settingChangedFlags |= LAPSTATS_READ;
            break;

        case READ_TRIGGER_THRESHOLD:  
            ioBufferWriteRssi(buffer, cmdRssiNodePtr->getTriggerThreshold());
            break;

        case READ_CALIBRATION_THRESHOLD:  
            ioBufferWriteRssi(buffer, cmdRssiNodePtr->getCalibrationThreshold());
            break;

        case READ_CALIBRATION_OFFSET:  
            ioBufferWriteRssi(buffer, cmdRssiNodePtr->getCalibrationOffset());
            break;

        case READ_REVISION_CODE:  // reply with NODE_API_LEVEL and verification value
            buffer.write16((0x25 << 8) + NODE_API_LEVEL);
            break;

        case READ_NODE_RSSI_PEAK:
            ioBufferWriteRssi(buffer, cmdRssiNodePtr->getState().nodeRssiPeak);
            break;

        case READ_TIME_MILLIS:
            buffer.write32(millis());
            break;

        case READ_RHFEAT_FLAGS:   // reply with feature flags value
            buffer.write16(RHFEAT_FLAGS_VALUE);
            break;

        case READ_MULTINODE_COUNT:
            buffer.write8(RssiNode::multiRssiNodeCount);
            break;

        case READ_CURNODE_INDEX:
            buffer.write8(cmdRssiNodePtr->getNodeIndex());
            break;

        case READ_NODE_SLOTIDX:
            buffer.write8(cmdRssiNodePtr->getSlotIndex());
            break;

        case READ_FW_VERSION:
            buffer.writeTextBlock(firmwareVersionString);
            break;

        case READ_FW_BUILDDATE:
            buffer.writeTextBlock(firmwareBuildDateString);
            break;

        case READ_FW_BUILDTIME:
            buffer.writeTextBlock(firmwareBuildTimeString);
            break;

        case READ_FW_PROCTYPE:
            buffer.writeTextBlock(firmwareProcTypeString);
            break;

        default:  // If an invalid command is sent, write nothing back, master must react
            LOG_ERROR("Invalid read command: ", command, HEX);
            actFlag = false;  // not valid activity
    }

    // indicate communications activity detected
    if (actFlag)
    {
        settingChangedFlags |= COMM_ACTIVITY;
        if (serialFlag)
            settingChangedFlags |= SERIAL_CMD_MSG;
    }

    if (!buffer.isEmpty())
    {
        buffer.writeChecksum();
    }

    command = 0;  // Clear previous command
}

void Message::handleReadLapPassStats(mtime_t timeNowVal)
{
    uint8_t crossing = cmdRssiNodePtr->getState().crossing ?  (uint8_t)1 : (uint8_t)0;
    buffer.write8(cmdRssiNodePtr->getLastPass().lap);
    buffer.write32(timeNowVal - cmdRssiNodePtr->getLastPass().nodeRssiPeakTimestamp);  // sortof a lap time in progress? 
    ioBufferWriteRssi(buffer, cmdRssiNodePtr->getState().rssi);
    ioBufferWriteRssi(buffer, cmdRssiNodePtr->getState().rssiTrigger);
    ioBufferWriteRssi(buffer, cmdRssiNodePtr->getLastPass().nodeRssiPeak);  // RSSI peak for last lap pass
    if (cmdRssiNodePtr->getLastPass().nodeRssiLaptime == 0){
       buffer.write32(timeNowVal - cmdRssiNodePtr->getLastPass().nodeRssiPeakTimestamp);  // ms start of node
    }else{
       buffer.write32(cmdRssiNodePtr->getLastPass().nodeRssiLaptime);  //ms since last peak
    }
    buffer.write8(crossing);
}

