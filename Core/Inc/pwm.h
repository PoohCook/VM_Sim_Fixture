

#ifndef __PWM__
#define __PWM__

#include "stm32l4xx_hal.h"
#include "cmsis_os.h"

#include <stdint.h>

#include <stdbool.h>

#define PWM_PULSE_SIZE 3
typedef uint32_t pwm_pulse_t;
typedef struct {
    pwm_pulse_t pulseCount[PWM_PULSE_SIZE];
}PWM_PULSE;

#define pwm_usecToPulseCount(usec) (((usec) * 80))

void pwm_initialize(void);

#define pwm_isBusy() (DMA1_Channel5->CNDTR != 0)

void pwm_sendPulse(PWM_PULSE *pulse, int length, volatile bool *bus_is_busy);


#endif // __PWM__
