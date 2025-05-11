/**
  ******************************************************************************
  * @file    stm32f4xx_hal_msp.c
  * @brief   MSP Initialization and de-Initialization codes.
  ******************************************************************************
  */

/* Includes ------------------------------------------------------------------*/
#include "main.h"

/**
  * @brief  Initializes the Global MSP.
  * @retval None
  */
void HAL_MspInit(void)
{
  __HAL_RCC_SYSCFG_CLK_ENABLE();
  __HAL_RCC_PWR_CLK_ENABLE();

  /* System interrupt init*/
  HAL_NVIC_SetPriority(PendSV_IRQn, 15, 0);
}

/**
  * @brief GPIO MSP Initialization
  * @retval None
  */
void HAL_GPIO_MspInit(void)
{
  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOA_CLK_ENABLE();
}

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/ 