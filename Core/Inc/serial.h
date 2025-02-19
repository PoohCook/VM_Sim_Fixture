#ifndef __SERIAL__
#define __SERIAL__


#include "stm32l4xx_hal.h"
#include "cmsis_os.h"

#include <stdint.h>
#include <stdbool.h>


void ser_initialize(void);
void ser_handle_uart_error();
void ser_handle_uart_complete();
bool ser_send(uint8_t* data, int length, bool wait);
void ser_reset(void);
int ser_read(uint8_t* data, int length);
void ser_send_com_req();

#endif //  __SERIAL__
