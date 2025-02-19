/*
 * frame.c
 *
 *  Created on: Feb 20, 2025
 *      Author: Pooh
 */


#include "buffers.h"
#include "command.h"
#include "main.h"
#include <string.h>

typedef StaticSemaphore_t osStaticSemaphoreDef_t;

osSemaphoreId_t responseRingLock_id;
osStaticSemaphoreDef_t responseRingLockCtlblk;
const osSemaphoreAttr_t responseRingLock_attributes = {
  .name = "responseRingLock",
  .cb_mem = &responseRingLockCtlblk,
  .cb_size = sizeof(responseRingLockCtlblk),
};

#if 1
#define TP_SET(pin){ tp_Set((pin)); }
#define TP_RESET(pin){ tp_Reset((pin)); }
#else
#define TP_SET(pin){  }
#define TP_RESET(pin){  }
#endif

/*
 * Rings
 */
typedef struct
{
    uint32_t mask;
    uint32_t start;
    uint32_t end;
    RES_FRAME data[1];
} ResponseRing;

#define FrameRingDef(data_size) \
    struct\
    {\
        uint32_t mask;\
        uint32_t start;\
        uint32_t end;\
        RES_FRAME data[(data_size)];\
    }

#define FRAME_SEND_RING_DATA_SIZE 0x08
FrameRingDef(FRAME_SEND_RING_DATA_SIZE) frameSendRing;

static inline void initializeFrameRing(ResponseRing *ring, uint32_t size)
{
    ring->mask = size - 1;
    ring->start = 0;
    ring->end = 0;
}
#define dataInFrameRing(ring) (int)(((ring).start - (ring).end) & (ring).mask)
#define frameRingIsFull(ring) (dataInFrameRing((ring)) == (ring).mask)

static inline bool getFromFrameRing(ResponseRing *ring, RES_FRAME *output_frame_buffer)
{
    if(dataInFrameRing(*ring) <= 0)
    {
        return false;
    }

    if(output_frame_buffer != NULL)
    {
        RES_FRAME *source = ((RES_FRAME *)ring->data) + ring->end;
        memcpy(output_frame_buffer, source, sizeof(RES_FRAME));
    }
    ring->end = (ring->end + 1) & ring->mask;

    return true;
}

static inline void putToFrameRing(ResponseRing *ring, RES_FRAME *input_frame)
{
    if(frameRingIsFull(*ring))
    {
        getFromFrameRing(ring, NULL);
    }

    RES_FRAME *destination = ((RES_FRAME *)ring->data) + ring->start;
    memcpy(destination, input_frame, sizeof(RES_FRAME));
    ring->start = (ring->start + 1) & ring->mask;

}

static inline bool getNextFrameToSend(RES_FRAME *out)
{
    if(getFromFrameRing((ResponseRing *)&frameSendRing, out))
    {
       return true;
    }
    return false;
}


// Referenced from ht.c
volatile uint32_t baseTix = 0;
#define refreshActivityCounter() {baseTix = getCurrentTicks();}
#define ACTIVITY_COUNTER_TIMEOUT_MS (uint32_t)(100) /*1 millisecond*/
#define osKernelSysTickMSec(ms) (((uint32_t)ms * (osKernelGetTickFreq())) / 1000)
#define getCurrentTicks() ((uint32_t)osKernelSysTick())
volatile uint32_t elapsed_tix = 0;
volatile uint32_t timeout_tix = 0;

#define MSEC_PER_CHAR   1
static bool resp_tx_in_progress;
static ACTIVITY_TIMER resp_transmitting;

void resp_handle_uart_error(){
    TP_SET(TP12);
    resp_tx_in_progress = false;
    TP_RESET(TP12)
}

void resp_handle_uart_complete(){
    resp_tx_in_progress = false;

}

static bool ser_response_send(uint8_t* data, int length){

    if( HAL_UART_Transmit_DMA(&hlpuart1, data, length) != HAL_OK){
        return false;
    }

    
    resp_tx_in_progress = true;
    activity_initialize(&resp_transmitting, MSEC_PER_CHAR * length);
    activity_refresh(&resp_transmitting);
    while(resp_tx_in_progress){
        if(activity_isExpired(&resp_transmitting)){
            resp_handle_uart_error();
            return false;
        }
        osDelay(1);
    }

    return true;

}

void response_initialize()
{
    resp_tx_in_progress = false;
	responseRingLock_id = osSemaphoreNew(1, 1, &responseRingLock_attributes);
    osSemaphoreRelease(responseRingLock_id);
    initializeFrameRing((ResponseRing *)&frameSendRing, FRAME_SEND_RING_DATA_SIZE);
}

RES_FRAME service_send_frame;
int frame_spi_send_count = 0;
void response_serviceSend(void)
{
     bool hasFrame = false;
    osSemaphoreAcquire(responseRingLock_id, osWaitForever);
    hasFrame = getNextFrameToSend(&service_send_frame);
    osSemaphoreRelease(responseRingLock_id);

    if(hasFrame)
    {
        TP_SET(TP1);
        uint16_t length = service_send_frame[0];
        ser_response_send(service_send_frame, length+2);
        TP_RESET(TP1);
    }

}

bool response_send(RES_FRAME *send_frame)
{
    /* Frame Length will be morphed */
    uint8_t data_length = *send_frame[0];
    if(data_length == 0 || data_length >= MAX_TX_DATA_LENGTH+2)
    {
        return false;
    }

    bool result = false;

    osSemaphoreAcquire(responseRingLock_id, osWaitForever);

    putToFrameRing((ResponseRing *)&frameSendRing, send_frame);

    osSemaphoreRelease(responseRingLock_id);

    return result;
}
