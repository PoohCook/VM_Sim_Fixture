/*
 * buffers.c
 *
 *  Created on: May 5, 2022
 *      Author: Pooh
 */


#include <stdint.h>
#include "buffers.h"

uint8_t spi_read_buffer[SPI_READ_BUFFER_SIZE];
uint8_t spi_read_dma[SPI_READ_DMA_SIZE];
uint8_t spi_write_dma[SPI_WRITE_DMA_SIZE];
RINGBUF spi_ringbuf;

pwm_pulse_t iebus_pulsemem[IEBUS_PULSEMEM_SIZE];
uint32_t iebus_rx_buffer[IEBUS_USREAD_BUFFER_SIZE];
RINGBUF16 iebus_usringbuf;
