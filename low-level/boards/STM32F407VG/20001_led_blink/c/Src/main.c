#include "main.h"

int main(void) {
    // HAL initialization
    HAL_Init();
    
    // Configure the system clock
    SystemClock_Config();
    
    // Initialize all configured peripherals
    MX_GPIO_Init();
    
    // Infinite loop
    while (1) {
        // Toggle the LED
        HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
        
        // Insert delay
        HAL_Delay(500); // 500 ms delay
    }
}

void SystemClock_Config(void) {
    // System Clock Configuration code
    // ...existing code...
}

void MX_GPIO_Init(void) {
    // GPIO Ports Clock Enable
    __HAL_RCC_GPIOA_CLK_ENABLE();
    
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    
    // Configure GPIO pin : PA5
    GPIO_InitStruct.Pin = GPIO_PIN_5;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
}
