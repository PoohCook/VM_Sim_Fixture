/*
 * mux.c
 *
 *  Created on:Sept 27, 2023
 *      Author: pooh
 */

#include "main.h"
#include "command.h"
#include "circular.h"
#include "ticks.h"
#include "mux.h"
#include <stdlib.h>
#include <string.h>

#if 0
#define TP_SET(pin){ tp_Set((pin)); }
#define TP_RESET(pin){ tp_Reset((pin)); }
#else
#define TP_SET(pin){  }
#define TP_RESET(pin){  }
#endif


void mux_setup_output(OUT_MUX enable){

    HAL_GPIO_WritePin(GPIOA, HT_IR_MISO_RX_EN_Pin|HT_MC_MOSI_RX_EN_Pin|VTS_MC_MISO_RX_EN_Pin|VTS_MC_MOSI_RX_EN_Pin, GPIO_PIN_RESET);
    uint16_t enable_map = 0;
    if( (enable & OUT_MUX_HT_IR_MISO) != 0){
        enable_map |= HT_IR_MISO_RX_EN_Pin;
    }
    if( (enable & OUT_MUX_HT_MC_MOSI) != 0){
        enable_map |= HT_MC_MOSI_RX_EN_Pin;
    }
    if( (enable & OUT_MUX_VTS_MC_MOSI) != 0){
        enable_map |= VTS_MC_MOSI_RX_EN_Pin;
    }
    if( (enable & OUT_MUX_VTS_MC_MISO) != 0){
        enable_map |= VTS_MC_MISO_RX_EN_Pin;
    }

    HAL_GPIO_WritePin(GPIOA, enable_map, GPIO_PIN_SET);

}

void mux_setup_input(IN_MUX enable){

    HAL_GPIO_WritePin(GPIOB, HT_IR_MOSI_TX_EN_Pin|HT_MC_MISO_TX_EN_Pin|VTS_SLV_MOSI_TX_EN_Pin|VTS_MC_MISO_TX_EN_Pin, GPIO_PIN_RESET);

    uint16_t enable_map = 0;
    if( (enable & IN_MUX_HT_IR_MOSI) != 0){
        enable_map |= HT_IR_MOSI_TX_EN_Pin;
    }
    if( (enable & IN_MUX_HT_MC_MISO) != 0){
        enable_map |= HT_MC_MISO_TX_EN_Pin;
    }
    if( (enable & IN_MUX_VTS_SLV_MOSI) != 0){
        enable_map |= VTS_SLV_MOSI_TX_EN_Pin;
    }
    if( (enable & IN_MUX_VTS_MC_MISO) != 0){
        enable_map |= VTS_MC_MISO_TX_EN_Pin;
    }

    HAL_GPIO_WritePin(GPIOB, enable_map, GPIO_PIN_SET);

}

void mux_sync_write(bool active){
    HAL_GPIO_WritePin(GPIOB, VTS_SYNC_IN_Pin, active ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

bool mux_sync_read(){
    return HAL_GPIO_ReadPin(GPIOB, VTS_SYNC_OUT_Pin) == GPIO_PIN_SET;
}

uint8_t led_status_read(void){

    uint8_t status = 0;
    if(HAL_GPIO_ReadPin(GPIOC, RED_DRV_SENSE_Pin) == GPIO_PIN_RESET) status |= DriverStatusRed;
    if(HAL_GPIO_ReadPin(GPIOC, GREEN_DRV_SENSE_Pin) == GPIO_PIN_RESET) status |= DriverStatusGreen;
    if(HAL_GPIO_ReadPin(GPIOC, BLUE_DRV_SENSE_Pin) == GPIO_PIN_RESET) status |= DriverStatusBlue;

    return status;
}

void mux_power(bool on){
    HAL_GPIO_WritePin(GPIOC, TP12_Pin, on ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

void mux_initialize(void){

    mux_setup_output(0);
    mux_setup_input(0);
    mux_power(false);

}
