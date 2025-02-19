#ifndef __COMMAND__
#define __COMMAND__


#include "stm32l4xx_hal.h"
#include "cmsis_os.h"

#include <stdint.h>
#include <stdbool.h>

#define MAX_TX_DATA_LENGTH 250

void cmd_handle_uart_error();
void cmd_handle_uart_complete();
void cmd_init_interface();
void cmd_service();

#endif  //__COMMAND__
