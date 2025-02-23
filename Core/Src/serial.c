/*
 * serial.c
 *
 *  Created on:Sept 27, 2023
 *      Author: pooh
 */

#include "main.h"
#include "command.h"
#include "circular.h"
#include "ticks.h"
#include "serial.h"
#include <stdlib.h>
#include <string.h>

#if 1
#define TP_SET(pin){ tp_Set((pin)); }
#define TP_RESET(pin){ tp_Reset((pin)); }
#else
#define TP_SET(pin){  }
#define TP_RESET(pin){  }
#endif

#define MSEC_PER_CHAR   4
static CIRCULAR_DMA_BUFFER ser_circ_dma_buffer;
static ACTIVITY_TIMER ser_transmitting;
static ACTIVITY_TIMER ser_rerceiving;
static bool ser_tx_in_progress;
static uint8_t tx_buffer[MAX_TX_DATA_LENGTH];
static bool com_req_detect_start;
static uint8_t com_req_frame_id;
static void on_com_req_detect();
static ACTIVITY_TIMER comreq_detect;

void ser_set_normal_serial_mode();

static void set_comreq_mode(){
    TP_SET(TP6);
	GPIO_InitTypeDef GPIO_InitStruct = {0};
    com_req_detect_start = false;

	// Configure GPIO pin : Seial_RX as interrupt rising & falling
	GPIO_InitStruct.Pin = SERIAL_RX_DATA_Pin;
	GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING_FALLING;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	HAL_GPIO_Init(SERIAL_RX_DATA_GPIO_Port, &GPIO_InitStruct);

	// EXTI interrupt init
	// HAL_NVIC_SetPriority(EXTI0_IRQn, 5, 0);
	// HAL_NVIC_EnableIRQ(EXTI0_IRQn);
    HAL_NVIC_SetPriority(EXTI9_5_IRQn, 5, 0);  // Set priority for EXTI 5-9
    HAL_NVIC_EnableIRQ(EXTI9_5_IRQn);  // Enable the EXTI interrupt
    TP_RESET(TP6);

}

void ser_initialize(void){
    ser_tx_in_progress = false;
    circular_buffer_start(&ser_circ_dma_buffer, &huart1);

}

static void on_com_req_detect(){
    TP_SET(TP5);
    ser_set_normal_serial_mode();
    cmd_send_response(SerialComReqDetected, com_req_frame_id,  NULL, 0);
    TP_RESET(TP5);
}

void ser_gpio_edge_callback(uint16_t GPIO_Pin){
    TP_SET(TP1);
	if(GPIO_Pin == SERIAL_RX_DATA_Pin){
        TP_SET(TP2);
		if(HAL_GPIO_ReadPin (SERIAL_RX_DATA_GPIO_Port, SERIAL_RX_DATA_Pin)){
			TP_SET(TP3);
			if( com_req_detect_start && activity_isExpired(&comreq_detect)){
                ser_set_normal_serial_mode();
                on_com_req_detect();
			}
			com_req_detect_start = false;
            TP_RESET(TP3);
		}
		else{
            TP_SET(TP4);
			activity_refresh(&comreq_detect);
			com_req_detect_start = true;
			TP_RESET(TP4);
		}
        TP_RESET(TP2);
	}
    TP_RESET(TP1);

}

void ser_handle_uart_error(){
    TP_SET(TP12);
    circular_buffer_stop(&ser_circ_dma_buffer);
    circular_buffer_start(&ser_circ_dma_buffer, &huart1);
    ser_tx_in_progress = false;
    TP_RESET(TP12)
}

void ser_handle_uart_complete(){
    ser_tx_in_progress = false;

}

void ser_set_tx_gpio_mode(){
	GPIO_InitTypeDef GPIO_InitStruct = {0};

	// Configure GPIO pin : PC1 as output PP
	HAL_GPIO_WritePin(SERIAL_TX_DATA_GPIO_Port, SERIAL_TX_DATA_Pin, GPIO_PIN_SET );
	GPIO_InitStruct.Pin = SERIAL_TX_DATA_Pin;
	GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
	HAL_GPIO_Init(SERIAL_TX_DATA_GPIO_Port, &GPIO_InitStruct);

}

void ser_set_normal_serial_mode(){

	GPIO_InitTypeDef GPIO_InitStruct = {0};
	/**USART1 GPIO Configuration
	PA9     ------> USART1_TX
	PA10     ------> USART1_RX
	*/
    HAL_NVIC_DisableIRQ(EXTI9_5_IRQn);  // Enable the EXTI interrupt
	GPIO_InitStruct.Pin = SERIAL_TX_DATA_Pin|SERIAL_RX_DATA_Pin;
	GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
	GPIO_InitStruct.Alternate = GPIO_AF7_USART1;
	HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

}

void ser_send_com_req(){

	ser_set_tx_gpio_mode();
	HAL_GPIO_WritePin(SERIAL_TX_DATA_GPIO_Port, SERIAL_TX_DATA_Pin, GPIO_PIN_RESET );
	vTaskDelay(pdMS_TO_TICKS(200));
	HAL_GPIO_WritePin(SERIAL_TX_DATA_GPIO_Port, SERIAL_TX_DATA_Pin, GPIO_PIN_SET );

	ser_set_normal_serial_mode();

}

void ser_set_wait_com_req(uint8_t frame_id){
    com_req_frame_id = frame_id;
    set_comreq_mode();
}

bool ser_send(uint8_t* data, int length, bool wait){

    if(!wait){
        for(int i=0 ; i<length ; i++){
            tx_buffer[i] = data[i];
        }
        data = tx_buffer;
    }


    TP_SET(TP9);
    if( HAL_UART_Transmit_DMA(&huart1, data, length) != HAL_OK){
        TP_RESET(TP9);
        return false;
    }

    ser_tx_in_progress = true;
    activity_initialize(&ser_transmitting, MSEC_PER_CHAR * length);
    activity_refresh(&ser_transmitting);
    while(wait && ser_tx_in_progress){
        if(activity_isExpired(&ser_transmitting)){
            ser_handle_uart_error();
            TP_RESET(TP9);
            return false;
        }
        osDelay(1);
    }

    TP_RESET(TP9);
    return true;

}

void ser_reset(void){
    ser_handle_uart_error();

    // wait and flush any thing that might slip in
    osDelay(2);
    uint8_t dummy[3] = {0};
    circular_buffer_read(&ser_circ_dma_buffer, dummy, sizeof(dummy));

}

int ser_read(uint8_t* data, int length){

    TP_SET(TP10);
    activity_initialize(&ser_rerceiving, MSEC_PER_CHAR * length);
    activity_refresh(&ser_rerceiving);

    int rx_indx = 0;
    int this_rx = 0;
    while(rx_indx < length){
        this_rx = circular_buffer_read(&ser_circ_dma_buffer, data + rx_indx, length - rx_indx);
        rx_indx += this_rx;
        if(activity_isExpired(&ser_rerceiving)){
            ser_handle_uart_error();
            break;
        }
        if (this_rx > 0){
            activity_initialize(&ser_rerceiving, MSEC_PER_CHAR * 2);
        }

    }

    TP_RESET(TP10);
    return rx_indx;
}
