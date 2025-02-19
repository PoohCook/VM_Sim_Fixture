#include "circular.h"
#include <string.h>



void circular_buffer_start(CIRCULAR_DMA_BUFFER* circ, UART_HandleTypeDef *huart){
	circ->last_pos = 0;
	circ->huart = huart;
	HAL_UART_Receive_DMA(circ->huart, circ->buffer, sizeof(circ->buffer));
}

void circular_buffer_stop(CIRCULAR_DMA_BUFFER* circ){
	HAL_UART_AbortReceive(circ->huart);
}

#define XFR_LEN(start, end, max)  ((end) - (start)) > (max) ? (max) : ((end) - (start))
int circular_buffer_read(CIRCULAR_DMA_BUFFER* circ, uint8_t* buffer, size_t length){
	size_t xfr_len = 0;
	size_t cur_pos = sizeof(circ->buffer) - __HAL_DMA_GET_COUNTER(circ->huart->hdmarx);
	if(cur_pos == circ->last_pos){
		return 0;
	}
	if(cur_pos > circ->last_pos){
		xfr_len = XFR_LEN(circ->last_pos, cur_pos, length);
		memcpy(buffer, &circ->buffer[circ->last_pos], xfr_len);

	} else{
		xfr_len = XFR_LEN(circ->last_pos, sizeof(circ->buffer), length);
		memcpy(buffer, &circ->buffer[circ->last_pos], xfr_len);
		if(xfr_len < length && cur_pos > 0 ){
			size_t xfr_len2 = XFR_LEN(0, cur_pos, length - xfr_len);
			memcpy(&buffer[xfr_len], &circ->buffer[0], xfr_len2);
			xfr_len += xfr_len2;
		}
	}

	circ->last_pos += xfr_len;
	if(circ->last_pos >= sizeof(circ->buffer)){
		circ->last_pos -= sizeof(circ->buffer);
	}
	return xfr_len;
}
