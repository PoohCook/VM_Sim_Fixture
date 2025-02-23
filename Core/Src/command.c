/*
 * command.c
 *
 *  Created on:Sept 26, 2023
 *      Author: pooh
 */

#include "main.h"
#include "command.h"
#include "circular.h"
#include "mux.h"
#include "adc.h"
#include "version.h"
#include "serial.h"
#include "response.h"
#include <stdlib.h>
#include <string.h>

#if 0
#define TP_SET(pin){ tp_Set((pin)); }
#define TP_RESET(pin){ tp_Reset((pin)); }
#else
#define TP_SET(pin){  }
#define TP_RESET(pin){  }
#endif

#define FRAME_BUFFERING_TIMEOUT 40

static CIRCULAR_DMA_BUFFER cmd_circ_dma_buffer;

static CMD_FRAME rx_frame;
static RES_FRAME tx_frame;

static void frame_init(CMD_FRAME* frame){
    TP_SET(TP5);
	activity_initialize(&(frame->buffering), FRAME_BUFFERING_TIMEOUT);
    frame->state = CMD_STATE_LENGTH;
	frame->frm_len = 0;
    frame->rx_len = 0;
	frame->command = 0;
	memset(frame->data, 0, sizeof(frame->data));
    TP_RESET(TP5);
}

static bool frame_data_read(CMD_FRAME* frame, CIRCULAR_DMA_BUFFER* circ){

    int read_len = 0;
    uint8_t tmp = 0;

    if(frame->state != CMD_STATE_LENGTH && activity_isExpired(&(frame->buffering))){
        TP_SET(TP7);
        frame_init(frame);
        TP_RESET(TP7);
    }

    switch(frame->state){
        case CMD_STATE_LENGTH:
            if(circular_buffer_read( circ, &frame->frm_len, 1) == 1){
                TP_SET(TP1);
                frame->state = CMD_STATE_COMPLIMENT;
                activity_refresh(&(frame->buffering));
                TP_RESET(TP1);
            }
            break;

        case CMD_STATE_COMPLIMENT:
            if(circular_buffer_read( circ, &tmp, 1) == 1){
                TP_SET(TP2);
                if(frame->frm_len == ((~tmp) & 0xff)){
                   frame->state = CMD_STATE_COMMAND;
                   activity_refresh(&(frame->buffering));
                }else{
                   frame_init(frame);
                }
                TP_RESET(TP2);
            }
            break;

        case CMD_STATE_COMMAND:
            if(circular_buffer_read( circ, &frame->command, 1) == 1){
                TP_SET(TP3);
                frame->state = CMD_STATE_FRAME_ID;
                activity_refresh(&(frame->buffering));
                TP_RESET(TP3);
            }
            break;

        case CMD_STATE_FRAME_ID:
            if(circular_buffer_read( circ, &frame->frame_id, 1) == 1){
                TP_SET(TP4);
                frame->state = CMD_STATE_DATA;
                activity_refresh(&(frame->buffering));
                TP_RESET(TP4);
            }
            break;

        case CMD_STATE_DATA:
            read_len = circular_buffer_read( circ, &frame->data[frame->rx_len], sizeof(frame->data) - frame->rx_len);
            frame->rx_len += read_len;
            if(read_len){
                for( int j=0; j<read_len ; j++){
                    TP_SET(TP5);
                    TP_RESET(TP5);
                }
                activity_refresh(&(frame->buffering));
            }

            if((frame->rx_len + 2) >= frame->frm_len){
                TP_SET(TP6);
                uint8_t checksum = frame->command;
                checksum ^= frame->frame_id;
                for( int i=0 ; i < frame->rx_len ; i++){
                    checksum ^= frame->data[i];
                }

                TP_RESET(TP6);
                if(checksum == 0){
                    TP_SET(TP7);
                    TP_RESET(TP7);
                    return true;
                } else {
                    frame_init(frame);
                }

            }
            break;

        default:
            frame_init(frame);
    }

    return false;
}

void cmd_send_response(COMMAND command, uint8_t frame_id, uint8_t* data, int length){

    memset(tx_frame, 0, sizeof(tx_frame));
    tx_frame[0] = length + 3;
    tx_frame[1] = ((~tx_frame[0]) & 0xff);
    tx_frame[2] = (uint8_t)command;
    tx_frame[3] = frame_id;
    uint8_t checksum = tx_frame[2];
    checksum ^= frame_id;
    for( int i=0 ; i<length ; i++){
        tx_frame[i+4] = data[i];
        checksum ^= data[i];
    }
    tx_frame[4+length] = checksum;

    //HAL_UART_Transmit_DMA(&hlpuart1, tx_frame, length+4);
    response_send(&tx_frame);
}

static void ser_send_with_ack(CMD_FRAME* frame, bool wait){
    if(!ser_send(frame->data, frame->frm_len-3, wait)){
        cmd_send_response(Nak, frame->frame_id, NULL, 0);
    } else{
        cmd_send_response(Ack, frame->frame_id,frame->data, frame->frm_len-3);
    }
}

static void frame_process(CMD_FRAME* frame){
    TP_SET(TP8);
    uint8_t channel = 0;
    int length = 0;
    int rx_len = 0;
    int trigger = 0;
    uint16_t timeout = 0;
    uint16_t value = 0;


    switch((COMMAND)frame->command){
        case Ping:
            cmd_send_response(Pong, frame->frame_id, frame->data, frame->frm_len-3);
            break;

        case VersionRead:
            FIXTURE_VERSION version = version_data();
            cmd_send_response(Ack, frame->frame_id, (uint8_t*)&version, sizeof(version));
            break;

        case UutPower:
            if(frame->frm_len != 4){
                cmd_send_response(Nak,frame->frame_id,  NULL, 0);
                break;
            }
            mux_power(frame->data[0] != 0);
            cmd_send_response(Ack, frame->frame_id, NULL, 0);
            break;

        case  SerialSend:
            ser_send_with_ack(frame, true);
            break;

        case  SerialSendNoWait:
            ser_send_with_ack(frame, false);
            break;

        case SerialReset:
            ser_reset();
            cmd_send_response(Ack, frame->frame_id, NULL, 0);
            break;

        case SerialRead:
            length = frame->data[0];
            rx_len = ser_read(frame->data, length);
            cmd_send_response(rx_len == length ? Ack : Nak, frame->frame_id, frame->data, rx_len);
            break;

         case SerialSendComRequest:
         	ser_send_com_req();
         	cmd_send_response(Ack, frame->frame_id, NULL, 0);
         	break;

        case SerialWaitComRequest:
            ser_set_wait_com_req(frame->frame_id);
            cmd_send_response(Ack, frame->frame_id, NULL, 0);
            break;

        case SetupMux:
            if(frame->frm_len != 5){
                cmd_send_response(Nak,frame->frame_id,  NULL, 0);
                break;
            }
            mux_setup_input((IN_MUX)frame->data[0]);
            mux_setup_output((OUT_MUX)frame->data[1]);
            cmd_send_response(Ack, frame->frame_id, NULL, 0);
            break;

        case SyncWrite:
            if(frame->frm_len != 4){
                cmd_send_response(Nak,frame->frame_id,  NULL, 0);
                break;
            }
            mux_sync_write((bool)frame->data[0]);
            cmd_send_response(Ack,frame->frame_id,  NULL, 0);
            break;

        case SyncRead:
            if(frame->frm_len != 3){
                cmd_send_response(Nak,frame->frame_id,  NULL, 0);
                break;
            }
            bool active = mux_sync_read();
            cmd_send_response(Ack, frame->frame_id, (uint8_t*)&active, 1);
            break;

        case AdcRead:
            if(frame->frm_len != 8){
                cmd_send_response(Nak, frame->frame_id, NULL, 0);
                break;
            }

            channel = frame->data[0];
            length = frame->data[1];
            trigger = frame->data[2];
            timeout = frame->data[3] + (((uint16_t)frame->data[4]) << 8);
            memset(frame->data, 0, sizeof(frame->data));
            rx_len = adc_getChannelSeries(channel, (uint16_t*)frame->data, length, trigger, timeout);
            cmd_send_response(Ack, frame->frame_id, frame->data, rx_len * 2);
            break;

        case DacWrite:
            if(frame->frm_len != 6){
                cmd_send_response(Nak, frame->frame_id, NULL, 0);
                break;
            }
            channel = frame->data[0];
            value = frame->data[1] | (frame->data[2] << 8);
            dac_setChannelValue(channel, value);
            cmd_send_response(Ack, frame->frame_id, NULL, 0);
            break;

        case LedStatus:
            if(frame->frm_len != 3){
                cmd_send_response(Nak, frame->frame_id, NULL, 0);
                break;
            }
            uint8_t led_status = led_status_read();
            cmd_send_response(Ack, frame->frame_id, (uint8_t*)&led_status, 1);
            break;

        default:
            cmd_send_response(Nak, frame->frame_id, &(frame->command), 1);
    }

    TP_RESET(TP8);
}

void cmd_handle_uart_complete(){
    TP_SET(TP6);
    TP_RESET(TP6);

}

void cmd_handle_uart_error(){
	circular_buffer_start(&cmd_circ_dma_buffer, &hlpuart1);
}

void cmd_init_interface(){
    frame_init(&rx_frame);
    circular_buffer_start(&cmd_circ_dma_buffer, &hlpuart1);

}


void cmd_service(){
    if(frame_data_read(&rx_frame, &cmd_circ_dma_buffer)){

        TP_SET(TP7);
        frame_process(&rx_frame);

        frame_init(&rx_frame);
        TP_SET(TP7);
    }
}
