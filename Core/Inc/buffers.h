
#ifndef __BUFFER__
#define __BUFFER__

#include <stdint.h>
#include "pwm.h"
#include "ringbuf32.h"
#include "ringbuf16.h"
#include "ringbuf.h"

#define SPI_READ_BUFFER_SIZE  256
extern uint8_t spi_read_buffer[SPI_READ_BUFFER_SIZE];

#define SPI_READ_DMA_SIZE 48
extern uint8_t spi_read_dma[SPI_READ_DMA_SIZE];

#define SPI_WRITE_DMA_SIZE 48
extern uint8_t spi_write_dma[SPI_WRITE_DMA_SIZE];

extern RINGBUF spi_ringbuf;

#define IEBUS_PULSEMEM_SIZE 512
extern pwm_pulse_t iebus_pulsemem[IEBUS_PULSEMEM_SIZE];
//
#define IEBUS_USREAD_BUFFER_SIZE 512
extern uint32_t iebus_rx_buffer[IEBUS_USREAD_BUFFER_SIZE];

extern RINGBUF16 iebus_usringbuf;

#endif //__BUFFER__

