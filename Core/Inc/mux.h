#ifndef __MUX__
#define __MUX__


#include "stm32l4xx_hal.h"
#include "cmsis_os.h"

#include <stdint.h>
#include <stdbool.h>

typedef enum{
    OUT_MUX_HT_IR_MISO = 0X01,
    OUT_MUX_HT_MC_MOSI = 0X02,
    OUT_MUX_VTS_MC_MOSI = 0X04,
    OUT_MUX_VTS_MC_MISO = 0X08,
} OUT_MUX;

typedef enum{
    IN_MUX_HT_IR_MOSI = 0X01,
    IN_MUX_HT_MC_MISO = 0X02,
    IN_MUX_VTS_SLV_MOSI = 0X04,
    IN_MUX_VTS_MC_MISO = 0X08,
} IN_MUX;


typedef enum{
    DriverStatusRed = 0X01,
    DriverStatusGreen = 0X02,
    DriverStatusBlue = 0X04
} DriverStatus;

void mux_initialize(void);
void mux_setup_output(OUT_MUX enable);
void mux_setup_input(IN_MUX enable);
void mux_sync_write(bool active);
bool mux_sync_read(void);
uint8_t led_status_read(void);
void mux_power(bool on);

#endif // __MUX__
