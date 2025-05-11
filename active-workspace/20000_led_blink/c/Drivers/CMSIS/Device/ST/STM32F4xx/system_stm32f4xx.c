/**
  ******************************************************************************
  * @file    system_stm32f4xx.c
  * @brief   CMSIS Cortex-M4 Device Peripheral Access Layer System Source File.
  ******************************************************************************
  */

#include "stm32f4xx.h"

/* This variable is required by the HAL library */
uint32_t SystemCoreClock = 16000000U;

void SystemInit(void)
{
    /* FPU settings ------------------------------------------------------------*/
#if (__FPU_PRESENT == 1) && (__FPU_USED == 1)
    SCB->CPACR |= ((3UL << 10*2)|(3UL << 11*2));
#endif
    /* Reset the RCC clock configuration to the default reset state */
    RCC->CR |= (uint32_t)0x00000001;
    RCC->CFGR = 0x00000000;
    RCC->CR &= (uint32_t)0xFEF6FFFF;
    RCC->PLLCFGR = 0x24003010;
    RCC->CR &= (uint32_t)0xFFFBFFFF;
    RCC->CIR = 0x00000000;
    /* Configure the Vector Table location add offset address ------------------*/
#ifdef VECT_TAB_SRAM
    SCB->VTOR = SRAM_BASE | 0x00;
#else
    SCB->VTOR = FLASH_BASE | 0x00;
#endif
}

void SystemCoreClockUpdate(void)
{
    SystemCoreClock = 16000000U; // Default HSI value
} 