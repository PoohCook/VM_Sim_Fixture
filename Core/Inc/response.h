#ifndef __RESPONSE__
#define __RESPONSE__

#include <stdint.h>
#include <stdbool.h>
#include "command.h"

void resp_handle_uart_error();
void resp_handle_uart_complete();

void response_initialize();
void response_serviceSend(void);
bool response_send(RES_FRAME *send_frame);


#endif //  __RESPONSE__
