# Minimal Makefile for STM32F4xx HAL LED Blink

# Toolchain
CC=arm-none-eabi-gcc
AS=arm-none-eabi-as
CP=arm-none-eabi-objcopy
SZ=arm-none-eabi-size

# MCU and FPU
CPU = -mcpu=cortex-m4
FPU = -mfpu=fpv4-sp-d16
FLOAT-ABI = -mfloat-abi=hard
MCU = $(CPU) -mthumb $(FPU) $(FLOAT-ABI)

# Paths
CORE_INC = Core/Inc
CORE_SRC = Core/Src
HAL_INC = Drivers/STM32F4xx_HAL_Driver/Inc
HAL_SRC = Drivers/STM32F4xx_HAL_Driver/Src
CMSIS_INC = Drivers/CMSIS/Include
CMSIS_DEV_INC = Drivers/CMSIS/Device/ST/STM32F4xx/Include
CMSIS_DEV_SRC = Drivers/CMSIS/Device/ST/STM32F4xx

# Includes
INCLUDES = -I$(CORE_INC) -I$(HAL_INC) -I$(CMSIS_INC) -I$(CMSIS_DEV_INC)

# Minimal Sources (only those required for a HAL LED blink)
SRCS = \
  $(CORE_SRC)/main.c \
  $(CORE_SRC)/stm32f4xx_it.c \
  $(CORE_SRC)/stm32f4xx_hal_msp.c \
  $(HAL_SRC)/stm32f4xx_hal.c \
  $(HAL_SRC)/stm32f4xx_hal_gpio.c \
  $(HAL_SRC)/stm32f4xx_hal_rcc.c \
  $(HAL_SRC)/stm32f4xx_hal_cortex.c \
  $(HAL_SRC)/stm32f4xx_hal_flash.c \
  $(HAL_SRC)/stm32f4xx_hal_pwr.c \
  $(CMSIS_DEV_SRC)/system_stm32f4xx.c

# Output
BUILD_DIR = build
OUT_ELF = $(BUILD_DIR)/led_blink.elf
OUT_BIN = $(BUILD_DIR)/led_blink.bin

# Flags
CFLAGS = $(MCU) -DUSE_HAL_DRIVER -DSTM32F407xx $(INCLUDES) -Og -Wall -fdata-sections -ffunction-sections -g
LDFLAGS = $(MCU) -specs=nosys.specs -Wl,--gc-sections -Wl,-Map=$(BUILD_DIR)/led_blink.map

# Objects
OBJS = $(SRCS:%.c=$(BUILD_DIR)/%.o)

# Default target
all: $(BUILD_DIR) $(OUT_ELF) $(OUT_BIN)

$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(OUT_ELF): $(OBJS)
	$(CC) $(LDFLAGS) $^ -o $@
	$(SZ) $@

$(OUT_BIN): $(OUT_ELF)
	$(CP) -O binary $< $@

clean:
	rm -rf $(BUILD_DIR)

.PHONY: all clean 