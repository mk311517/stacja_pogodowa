"""
BME280 constants

This file includes all constants and default configs of the sensor (e.g. pins, registers).
It is largely a transcription of the information in the data sheet:
https://ae-bst.resource.bosch.com/media/_tech/media/datasheets/BST-BME280-DS002.pdf
"""


"""
I2C adress of the sensor
"""
BME_I2C_ADDR = 0x76

"""
Memory register adresses
The names correspond to the memory map as described in the data sheet.
"""
REG_HUM_LSB = 0xFE  # read only
REG_HUM_MSB = 0xFD  # read only
REG_TEMP_XLSB = 0xFC   # read only
REG_TEMP_LSB = 0xFB  # read only
REG_TEMP_MSB = 0xFA  # read only
REG_PRESS_XLSB = 0xF9  # read only
REG_PRESS_LSB = 0xF8  # read only
REG_PRESS_MSB = 0xF7  # read only
REG_CONFIG = 0xF5  # read/write
REG_CTRL_MEAS = 0xF4  # read/write
REG_STATUS = 0xF3  # read/write
REG_CTRL_HUM = 0xF2  # read/write
REG_CALIB26_41 = (0xE1, 7)  # read 7 bytes until register 0xE7 - read only
REG_RESET = 0xE0  # write only
REG_ID = 0xD0  # read only
REG_CALIB00_25 = (0x88, 26)  # read 26 bytes until register 0xA1 - read only

"""
Oversampling rates
"""
OS_T_1 = 0x20
OS_T_2 = 0x40
OS_T_4 = 0x60
OS_T_8 = 0x80
OS_T_16 = 0xA0

OS_P_1 = 0x04
OS_P_2 = 0x08
OS_P_4 = 0x0C
OS_P_8 = 0x10
OS_P_16 = 0x14

OS_H_1 = 0x01
OS_H_2 = 0x02
OS_H_4 = 0x03
OS_H_8 = 0x04
OS_H_16 = 0x05

"""
Modes
"""
MODE_SLEEP = 0x00
MODE_FORCE = 0x01
MODE_NORMAL = 0x03

"""
Time stand-by [ms]
"""
TSB_0_5 = 0x00
TSB_62_5 = 0x20
TSB_125 = 0x40
TSB_250 = 0x60
TSB_500 = 0x80
TSB_1000 = 0xA0
TSB_10 = 0xC0
TSB_20 = 0xE0

"""
Filter settings
"""
FILTER_OFF = 0x00
FILTER_2 = 0x04
FILTER_4 = 0x08
FILTER_8 = 0x0C
FILTER_16 = 0x10

"""
SPI 3-wire interface
"""
SPI3W_ON = 0x01
SPI3W_OFF = 0x00

"""
Additional constants
"""
SEALEVELPRESSURE_HPA = 1013.25
