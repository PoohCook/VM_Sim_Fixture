/*
 * adc.c
 *
 *  Created on: Sept 27, 2023
 *      Author: Pooh
 */

#include "main.h"
#include "adc.h"
#include "ticks.h"
#include <stdlib.h>

#if 0
#define TP_SET(pin){ tp_Set((pin)); }
#define TP_RESET(pin){ tp_Reset((pin)); }
#else
#define TP_SET(pin){  }
#define TP_RESET(pin){  }
#endif

static bool adc_in_progress;
static ACTIVITY_TIMER adc_convertion;

typedef enum{
    SenseIeDiff = 3,
    SenseLedPow = 5,
    SenseVtSync = 6,
    SenseHtIrMosi = 10,
    SenseHtMcMiso = 11,
    SenseVtsSlvMosi = 12,
    SenseVtsMcMiso = 15
} SenseChannel;

typedef enum{
    TriggerSoftware = 0,
    TriggerIeDetect = 1
} TriggerSource;


static uint32_t adc_get_sense_channel(uint8_t sense){
    switch((SenseChannel)sense){
        case SenseIeDiff:
            return ADC_CHANNEL_3;
        case SenseLedPow:
            return ADC_CHANNEL_5;
        case SenseVtSync:
            return ADC_CHANNEL_6;
        case SenseHtIrMosi:
            return ADC_CHANNEL_10;
        case SenseHtMcMiso:
            return ADC_CHANNEL_11;
        case SenseVtsSlvMosi:
            return ADC_CHANNEL_12;
        case SenseVtsMcMiso:
            return ADC_CHANNEL_15;
        default:
            return ADC_CHANNEL_1;
    }

}


static inline uint16_t adc_get_value(void)
{
    uint16_t adc_value = 0;
    TP_SET(TP1);
    HAL_ADC_Start(&hadc1);
    if(HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK){
        TP_SET(TP2);
        adc_value = HAL_ADC_GetValue (&hadc1);
        TP_RESET(TP2);
    }
    HAL_ADC_Stop(&hadc1);
    TP_RESET(TP1);

    return adc_value;
}

static inline uint16_t adc_single_conversion()
{

    ADC1_COMMON->CCR = (0x1) << 24;

    int adc_sum = 0;
    for( int i=0; i< ADC_AVG_SAMPLING; i++){
        adc_sum += adc_get_value();
    }


    ADC1_COMMON->CCR = 0x00;

    return adc_sum / ADC_AVG_SAMPLING;

}

uint16_t adc_getBatteryValue()
{
    uint16_t vbat = (3 * ADC_TO_MV(adc_single_conversion()));
    return vbat;
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc) {
    TP_SET(TP8);
    if(hadc == &hadc1){
        adc_in_progress = false;
    }
    TP_RESET(TP8);
}

static void adc_configureExtTrigger(TriggerSource source){

    switch(source){
        case TriggerIeDetect:
            hadc1.Init.ExternalTrigConv = ADC_EXTERNALTRIG_EXT_IT11;
            hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_RISING;
            break;

        case TriggerSoftware:
        default:
            hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
            hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
            break;

    }

    if (HAL_ADC_Init(&hadc1) != HAL_OK)
    {
        Error_Handler();
    }

}

int adc_getChannelSeries(uint8_t channel, uint16_t* data, int length, uint8_t source, uint16_t timeout){

    TP_SET(TP1);
    HAL_ADC_Stop_DMA(&hadc1);
    adc_configureExtTrigger(source);

    // Configure the list of channels to scan
    ADC_ChannelConfTypeDef sConfig;
    sConfig.Channel = adc_get_sense_channel(channel);
    sConfig.Rank = ADC_REGULAR_RANK_1;
    sConfig.SamplingTime = ADC_SAMPLETIME_24CYCLES_5;
    sConfig.SingleDiff =  channel == SenseIeDiff ? ADC_DIFFERENTIAL_ENDED : ADC_SINGLE_ENDED;
    sConfig.OffsetNumber = ADC_OFFSET_NONE;
    sConfig.Offset = 0;


    if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK){
        TP_RESET(TP1);
        return 0;
    }


    if (HAL_ADC_Start_DMA(&hadc1, (uint32_t *)data, length) != HAL_OK){
        TP_RESET(TP1);
        return 0;
    }

    TP_SET(TP3);
    adc_in_progress = true;
    activity_initialize(&adc_convertion, timeout);
    activity_refresh(&adc_convertion);
    while(adc_in_progress){
        if(activity_isExpired(&adc_convertion)){
            TP_RESET(TP1);
            TP_RESET(TP3);
            return 0;
        }
        osDelay(1);
    }
    TP_RESET(TP3);

    for(int i=0 ; i<length ; i++){
        data[i] = ADC_TO_MV(data[i]);
    }

    HAL_ADC_Stop_DMA(&hadc1);

    TP_RESET(TP1);
    return length;

}

bool dac_setChannelValue(uint8_t channel, uint16_t value_mv){
    TP_SET(TP3);
    if (HAL_DAC_SetValue(&hdac1, DAC_CHANNEL_1, DAC_ALIGN_12B_R, ADC_VALUE(value_mv)) != HAL_OK){
        TP_SET(TP1);
        TP_RESET(TP1);
        TP_RESET(TP3);
        return false;
    }

    TP_RESET(TP3);
    return true;
}
