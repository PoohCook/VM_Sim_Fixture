#ifndef CIRCULAR_H
#define CIRCULAR_H

#include "stm32l4xx_hal.h"

#define CIRCULAR_BUFFER_SIZE 128
typedef struct {
	UART_HandleTypeDef* huart;
	size_t last_pos;
	uint8_t buffer[CIRCULAR_BUFFER_SIZE];
} CIRCULAR_DMA_BUFFER;


void circular_buffer_start(CIRCULAR_DMA_BUFFER* circ, UART_HandleTypeDef *huart);
void circular_buffer_stop(CIRCULAR_DMA_BUFFER* circ);
int circular_buffer_read(CIRCULAR_DMA_BUFFER* circ, uint8_t* buffer, size_t length);


#endif // CIRCULAR_H
