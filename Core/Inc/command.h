#ifndef __COMMAND__
#define __COMMAND__


#include "stm32l4xx_hal.h"
#include "cmsis_os.h"

#include <stdint.h>
#include <stdbool.h>
#include "ticks.h"
#include "circular.h"

typedef enum {
  CMD_STATE_LENGTH,
  CMD_STATE_COMPLIMENT,
  CMD_STATE_COMMAND,
  CMD_STATE_FRAME_ID,
  CMD_STATE_DATA
} CMD_STATE;

typedef enum {
  Ping = 1,
  Pong = 2,
  Ack = 3,
  Nak = 4,
  VersionRead = 5,
  UutPower = 6,
  SerialSend = 0x10,
  SerialSendNoWait = 0x11,
  SerialReset = 0x12,
  SerialRead = 0x13,
  SerialSendComRequest = 0x14,
  SetupMux = 0x20,
  SyncWrite = 0x21,
  SyncRead = 0x22,
  AdcRead = 0x30,
  DacWrite = 0x31,
  LedStatus = 0x40


} COMMAND;


#define MAX_TX_DATA_LENGTH 250
typedef struct {
  CMD_STATE state;
ACTIVITY_TIMER buffering;
uint8_t frm_len;
uint8_t rx_len;
  uint8_t command;
  uint8_t frame_id;
  uint8_t data[MAX_TX_DATA_LENGTH] __attribute__((aligned(16)));  // this needs ot be half word aligned as it gets used
                                                                  // to recieve DMA words
} CMD_FRAME;

typedef uint8_t RES_FRAME[MAX_TX_DATA_LENGTH+2];


void cmd_handle_uart_error();
void cmd_handle_uart_complete();
void cmd_init_interface();
void cmd_service();

#endif  //__COMMAND__
