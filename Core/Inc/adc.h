
#ifndef __ADC__
#define __ADC__


#include "stm32l4xx_hal.h"
#include "cmsis_os.h"

#include <stdint.h>
#include <stdbool.h>

extern ADC_HandleTypeDef hadc1;
extern DAC_HandleTypeDef hdac1;
extern ADC_Common_TypeDef hadccom;

#define ADC_RESOLUTION_8        8
#define ADC_RESOLUTION_12       12

#define ADC_RESOLUTION          ADC_RESOLUTION_12

#if ADC_RESOLUTION == ADC_RESOLUTION_12
typedef volatile uint16_t adc_buffer_t;
#elif ADC_RESOLUTION == ADC_RESOLUTION_8
typedef volatile uint8_t adc_buffer_t;
#else
#error
#endif

#define ADC_AVG_SAMPLING         4

#define ADC_MAXIMUM_VALUE        ((0x1 << ADC_RESOLUTION) - 1)
#define ADC_REFERENCE_VOLTAGE    (3400) //millivolts
#define ADC_VALUE(voltage)       ((voltage) * ADC_MAXIMUM_VALUE / ADC_REFERENCE_VOLTAGE)
#define ADC_TO_MV(adcval)        ((ADC_REFERENCE_VOLTAGE * (adcval)) / ADC_MAXIMUM_VALUE)

void adc_initialize(void);
uint16_t adc_getBatteryValue();
int adc_getChannelSeries(uint8_t channel, uint16_t* data, int length, uint8_t source, uint16_t timeout);
bool dac_setChannelValue(uint8_t channel, uint16_t value_mv);

#endif // __ADC__
