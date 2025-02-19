/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; Copyright (c) 2022 STMicroelectronics.
  * All rights reserved.</center></h2>
  *
  * This software component is licensed by ST under BSD 3-Clause license,
  * the "License"; You may not use this file except in compliance with the
  * License. You may obtain a copy of the License at:
  *                        opensource.org/licenses/BSD-3-Clause
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32l4xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */
extern TIM_HandleTypeDef htim1;
extern TIM_HandleTypeDef htim2;
extern TIM_HandleTypeDef htim15;
extern TIM_HandleTypeDef htim6;
extern DMA_HandleTypeDef hdma_tim2_ch1;

extern UART_HandleTypeDef hlpuart1;
extern UART_HandleTypeDef huart1;
extern UART_HandleTypeDef huart2;
extern UART_HandleTypeDef huart3;
extern DMA_HandleTypeDef hdma_lpuart_rx;
extern DMA_HandleTypeDef hdma_lpuart_tx;
extern DMA_HandleTypeDef hdma_usart3_rx;
/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define BLUE_DRV_SENSE_Pin GPIO_PIN_13
#define BLUE_DRV_SENSE_GPIO_Port GPIOC
#define IE_BiasOut_Pin GPIO_PIN_4
#define IE_BiasOut_GPIO_Port GPIOA
#define TP7_Pin GPIO_PIN_4
#define TP7_GPIO_Port GPIOC
#define TP8_Pin GPIO_PIN_5
#define TP8_GPIO_Port GPIOC
#define HT_IR_MOSI_TX_EN_Pin GPIO_PIN_1
#define HT_IR_MOSI_TX_EN_GPIO_Port GPIOB
#define HT_MC_MISO_TX_EN_Pin GPIO_PIN_2
#define HT_MC_MISO_TX_EN_GPIO_Port GPIOB
#define TP3_Pin GPIO_PIN_10
#define TP3_GPIO_Port GPIOB
#define TP4_Pin GPIO_PIN_11
#define TP4_GPIO_Port GPIOB
#define COM_RTS_Pin GPIO_PIN_12
#define COM_RTS_GPIO_Port GPIOB
#define COM_CTS_Pin GPIO_PIN_13
#define COM_CTS_GPIO_Port GPIOB
#define TP5_Pin GPIO_PIN_14
#define TP5_GPIO_Port GPIOB
#define TP6_Pin GPIO_PIN_15
#define TP6_GPIO_Port GPIOB
#define TP9_Pin GPIO_PIN_6
#define TP9_GPIO_Port GPIOC
#define TP10_Pin GPIO_PIN_7
#define TP10_GPIO_Port GPIOC
#define TP11_Pin GPIO_PIN_8
#define TP11_GPIO_Port GPIOC
#define TP12_Pin GPIO_PIN_9
#define TP12_GPIO_Port GPIOC
#define HT_IR_MISO_RX_EN_Pin GPIO_PIN_8
#define HT_IR_MISO_RX_EN_GPIO_Port GPIOA
#define SERIAL_TX_DATA_Pin GPIO_PIN_10
#define SERIAL_TX_DATA_GPIO_Port GPIOA
#define SERIAL_RX_DATA_Pin GPIO_PIN_9
#define SERIAL_RX_DATA_GPIO_Port GPIOA
#define HT_MC_MOSI_RX_EN_Pin GPIO_PIN_11
#define HT_MC_MOSI_RX_EN_GPIO_Port GPIOA
#define VTS_MC_MOSI_RX_EN_Pin GPIO_PIN_12
#define VTS_MC_MOSI_RX_EN_GPIO_Port GPIOA
#define VTS_MC_MISO_RX_EN_Pin GPIO_PIN_15
#define VTS_MC_MISO_RX_EN_GPIO_Port GPIOA
#define RED_DRV_SENSE_Pin GPIO_PIN_10
#define RED_DRV_SENSE_GPIO_Port GPIOC
#define IE_BusDetect_Pin GPIO_PIN_11
#define IE_BusDetect_GPIO_Port GPIOC
#define GREEN_DRV_SENSE_Pin GPIO_PIN_12
#define GREEN_DRV_SENSE_GPIO_Port GPIOC
#define VTS_SLV_MOSI_TX_EN_Pin GPIO_PIN_4
#define VTS_SLV_MOSI_TX_EN_GPIO_Port GPIOB
#define VTS_MC_MISO_TX_EN_Pin GPIO_PIN_5
#define VTS_MC_MISO_TX_EN_GPIO_Port GPIOB
#define TP1_Pin GPIO_PIN_6
#define TP1_GPIO_Port GPIOB
#define TP2_Pin GPIO_PIN_7
#define TP2_GPIO_Port GPIOB
#define VTS_SYNC_IN_Pin GPIO_PIN_8
#define VTS_SYNC_IN_GPIO_Port GPIOB
#define VTS_SYNC_OUT_Pin GPIO_PIN_9
#define VTS_SYNC_OUT_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

extern DMA_HandleTypeDef hdma_spi1_rx;
extern DMA_HandleTypeDef hdma_spi1_tx;
extern DMA_HandleTypeDef hdma_usart1_tx;

typedef struct{
  GPIO_TypeDef * base;
  uint16_t pin;
} TEST_PIN;


void tp_Set(TEST_PIN pin);
void tp_Reset(TEST_PIN pin);
void tp_Toggle(TEST_PIN pin);

TEST_PIN get_pin_def(GPIO_TypeDef * base, uint16_t pin);

#define TP1   (get_pin_def(GPIOB, TP1_Pin))
#define TP2   (get_pin_def(GPIOB, TP2_Pin))
#define TP3   (get_pin_def(GPIOB, TP3_Pin))
#define TP4   (get_pin_def(GPIOB, TP4_Pin))
#define TP5   (get_pin_def(GPIOB, TP5_Pin))
#define TP6   (get_pin_def(GPIOB, TP6_Pin))
#define TP7   (get_pin_def(GPIOC, TP7_Pin))
#define TP8   (get_pin_def(GPIOC, TP8_Pin))
#define TP9   (get_pin_def(GPIOC, TP9_Pin))
#define TP10  (get_pin_def(GPIOC, TP10_Pin))
#define TP11  (get_pin_def(GPIOC, TP11_Pin))
#define TP12  (get_pin_def(GPIOC, TP12_Pin))

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
