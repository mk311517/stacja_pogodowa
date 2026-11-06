"""
This file contains the implementation of the bme280 class that let's you
configure the sensor and read-out the data.

Sources that served as guidance during implementation:
* https://github.com/robert-hh/BME280
* https://ae-bst.resource.bosch.com/media/_tech/media/datasheets/BST-BME280-DS002.pdf

"""
from ustruct import unpack
import utime

import constants


class bme280_instance:

    def __init__(self, i2c_connection, bme_address=None):
        self.i2c = i2c_connection
        if bme_address:
            self.bme_i2c_addr = bme_address
        else:
            self.bme_i2c_addr = constants.BME_I2C_ADDR
        self._calibration_t = None
        self._calibration_p = None
        self._calibration_h = None
        self._raw_data_buffer = bytearray(8)
        self._start_up()

    def _start_up(self):
        print("Initializing sensor.")
        self.check_sensor()
        print("Sensor found.")
        self.reset_sensor()
        print("Initiated soft-reset.")
        utime.sleep_ms(100)
        self._auto_config()
        print("Set auto-config.")
        self._read_calibration_data()
        print("Read calibration data.")

    def check_sensor(self):
        # check sensor id:
        chip = self.i2c.readfrom_mem(self.bme_i2c_addr, constants.REG_ID, 2)
        chip_id = unpack("<h", chip)[0]
        if chip_id != 0x60:
            raise OSError(
                "The i2c device does not return the correct chip id: {}".format(chip_id))
        print("Found a BME280 at {}.".format(self.bme_i2c_addr))

    def reset_sensor(self):
        self.i2c.writeto_mem(
            self.bme_i2c_addr, constants.REG_RESET, bytearray([0xB6]))

    def _read_calibration_data(self):
        calib00_25 = self.i2c.readfrom_mem(
            self.bme_i2c_addr, constants.REG_CALIB00_25[0],
            constants.REG_CALIB00_25[1])
        calib26_41 = self.i2c.readfrom_mem(
            self.bme_i2c_addr, constants.REG_CALIB26_41[0],
            constants.REG_CALIB26_41[1])
        dig00_25 = unpack("<HhhHhhhhhhhhBB", calib00_25)
        dig26_41 = unpack("<hBbhb", calib26_41)
        self._calibration_t = dig00_25[:3]
        self._calibration_p = dig00_25[3:12]
        h4 = (dig26_41[2] * 16) + (dig26_41[3] & 0xF)  # additional unpacking
        h5 = dig26_41[3] // 16
        self._calibration_h = (
            dig00_25[13], dig26_41[0], dig26_41[1], h4, h5, calib26_41[6])

    def _set_value(self, value, register, bit_mask):
        ctrl_byte = self.i2c.readfrom_mem(self.bme_i2c_addr, register, 1)
        ctrl_byte = unpack('<b', ctrl_byte)[0]
        out_value = (ctrl_byte & bit_mask) | value
        self.i2c.writeto_mem(self.bme_i2c_addr, register,
                             bytearray([out_value]))

    def _get_value(self, register, bit_mask):
        ctrl_byte = self.i2c.readfrom_mem(
            self.bme_i2c_addr, register, 1)
        ctrl_byte = unpack('<b', ctrl_byte)[0]
        return ctrl_byte & bit_mask

    def set_temp_oversampling(self, rate):
        self._set_value(rate, constants.REG_CTRL_MEAS, 0x1F)

    def get_temp_oversampling(self):
        value = self._get_value(constants.REG_CTRL_MEAS, 0xE0)
        if value == constants.OS_T_1:
            return 'x1', value
        if value == constants.OS_T_2:
            return 'x2', value
        if value == constants.OS_T_4:
            return 'x4', value
        if value == constants.OS_T_8:
            return 'x8', value
        if value in [constants.OS_T_16, 0xE0, 0xC0]:
            return 'x16', value
        return 'reset state', value

    def set_press_oversampling(self, rate):
        self._set_value(rate, constants.REG_CTRL_MEAS, 0xE3)

    def get_press_oversampling(self):
        value = self._get_value(constants.REG_CTRL_MEAS, 0x1C)
        if value == constants.OS_P_1:
            return 'x1', value
        if value == constants.OS_P_2:
            return 'x2', value
        if value == constants.OS_P_4:
            return 'x4', value
        if value == constants.OS_P_8:
            return 'x8', value
        if value in [constants.OS_P_16, 0x1C, 0x18]:
            return 'x16', value
        return 'reset state', value

    def set_hum_oversampling(self, rate):
        self._set_value(rate, constants.REG_CTRL_HUM, 0xF8)
        # it is necessary to do a write operation to ctrl_meas for the changes
        # in ctrl_hum to take place
        ctrl_meas = self.i2c.readfrom_mem(
            self.bme_i2c_addr, constants.REG_CTRL_MEAS, 1)
        ctrl_meas = unpack('<b', ctrl_meas)[0]
        self.i2c.writeto_mem(
            self.bme_i2c_addr, constants.REG_CTRL_MEAS, bytearray([ctrl_meas]))

    def get_hum_oversampling(self):
        value = self._get_value(constants.REG_CTRL_HUM, 0x07)
        if value == constants.OS_H_1:
            return 'x1', value
        if value == constants.OS_H_2:
            return 'x2', value
        if value == constants.OS_H_4:
            return 'x4', value
        if value == constants.OS_H_8:
            return 'x8', value
        if value in [constants.OS_H_16, 0x07, 0x06]:
            return 'x16', value
        return 'reset state', value

    def set_mode(self, mode):
        self._set_value(mode, constants.REG_CTRL_MEAS, 0xFC)

    def get_mode(self):
        value = self._get_value(constants.REG_CTRL_MEAS, 0x03)
        if value == constants.MODE_SLEEP:
            return 'sleep', value
        if value in [constants.MODE_FORCE, 0x02]:
            return 'force', value
        if value == constants.MODE_NORMAL:
            return 'normal', value

    def set_time_standby(self, interval):
        self._set_value(interval, constants.REG_CONFIG, 0x1F)

    def get_time_standby(self):
        value = self._get_value(constants.REG_CONFIG, 0xE0)
        if value == constants.TSB_0_5:
            return '0.5ms', value
        if value == constants.TSB_62_5:
            return '62.5ms', value
        if value == constants.TSB_125:
            return '125ms', value
        if value == constants.TSB_250:
            return '250ms', value
        if value == constants.TSB_500:
            return '500ms', value
        if value == constants.TSB_1000:
            return '1000ms', value
        if value == constants.TSB_10:
            return '10ms', value
        if value == constants.TSB_20:
            return '20ms', value

    def set_filter(self, mode):
        self._set_value(mode, constants.REG_CONFIG, 0xE3)

    def get_filter(self):
        value = self._get_value(constants.REG_CONFIG, 0x1C)
        if value == constants.FILTER_OFF:
            return 'off', value
        if value == constants.FILTER_2:
            return '2x', value
        if value == constants.FILTER_4:
            return '4x', value
        if value == constants.FILTER_8:
            return '8x', value
        if value in [constants.FILTER_16, 0x14, 0x18, 0x1C]:
            return '16x', value

    def set_spi3w(self, mode):
        self._set_value(mode, constants.REG_CONFIG, 0xFE)

    def get_spi3w(self):
        value = self._get_value(constants.REG_CONFIG, 0x01)
        if value == constants.SPI3W_ON:
            return 'on', value
        if value == constants.SPI3W_OFF:
            return 'off', value

    @property
    def is_measuring(self):
        value = self._get_value(constants.REG_STATUS, 0x08)
        if value == 0x08:
            return True
        return False

    @property
    def is_im_update(self):
        value = self._get_value(constants.REG_STATUS, 0x01)
        if value == 0x01:
            return True
        return False

    def __to_20bit__(self, buf):
        # ((msb << 16) | (lsb << 8) | xlsb) >> 4
        return ((buf[0] << 16) | (buf[1] << 8) | buf[2]) >> 4

    def __to_16bit__(self, buf):
        # (msb << 8) | lsb
        return (buf[0] << 8) | buf[1]

    def __t_fine__(self, adc_temperature):
        """Calculate the fine resolution temperature value"""
        var1 = (((adc_temperature >> 3) -
                 (self._calibration_t[0] << 1)) * self._calibration_t[1]) >> 11
        var2 = (((
            ((adc_temperature >> 4) - self._calibration_t[0]) *
            ((adc_temperature >> 4) - self._calibration_t[0])) >> 12)
            * self._calibration_t[2]) >> 14
        return var1 + var2

    def get_data(self):
        # single burst read-out from sensor:
        self.i2c.readfrom_mem_into(
            self.bme_i2c_addr, 0xF7, self._raw_data_buffer)
        # unpack data - pressure + temperature are unsigned 20-bit
        # and humidity is unsigned 16-bit)
        # pressure(0xF7)
        adc_pressure = self.__to_20bit__(self._raw_data_buffer[0:3])
        # temperature(0xFA)
        adc_temperature = self.__to_20bit__(self._raw_data_buffer[3:6])
        # humidity(0xFD)
        adc_humidity = self.__to_16bit__(self._raw_data_buffer[6:8])

        # temperature factor
        t_fine = self.__t_fine__(adc_temperature)

        # calculate values from the raw data
        pressure = self._calculate_pressure(adc_pressure, t_fine)
        temperature = self._calculate_temperature(t_fine)
        humidity = self._calculate_humidity(adc_humidity, t_fine)

        return pressure, temperature, humidity

    @staticmethod
    def _calculate_temperature(t_fine):
        return ((t_fine * 5 + 128) >> 8) / 100

    def _calculate_pressure(self, adc_pressure, t_fine):
        var1 = t_fine - 128000
        var2 = var1 * var1 * self._calibration_p[5]
        var2 = var2 + ((var1 * self._calibration_p[4]) << 17)
        var2 = var2 + (self._calibration_p[3] << 35)
        var1 = (((var1 * var1 * self._calibration_p[2]) >> 8) +
                ((var1 * self._calibration_p[1]) << 12))
        var1 = (((1 << 47) + var1) * self._calibration_p[0]) >> 33
        if var1 == 0:
            return 0  # avoid exception caused by division by zero
        else:
            p = 1048576 - adc_pressure
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self._calibration_p[8] * (p >> 13) * (p >> 13)) >> 25
            var2 = (self._calibration_p[7] * p) >> 19
            # only difference from data sheet is the division by 256 to get
            # pascal
            pressure = ((p + var1 + var2) >> 8) + (self._calibration_p[6] << 4)
            return (pressure >> 8) / 100

    def _calculate_humidity(self, adc_humidity, t_fine):
        h = t_fine - 76800
        h = (((((adc_humidity << 14) - (self._calibration_h[3] << 20) -
                (self._calibration_h[4] * h)) + 16384) >> 15) *
             (((((((h * self._calibration_h[5]) >> 10) *
                  (((h * self._calibration_h[2]) >> 11) + 32768)) >> 10)
                + 2097152) *
               self._calibration_h[1] + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7)
                  * self._calibration_h[0]) >> 4)
        h = 0 if h < 0 else h
        h = 419430400 if h > 419430400 else h
        # only difference from data sheet is division by 1024 to get relative
        # humidity
        return (h >> 12) / 1024

    def _auto_config(self):
        self.set_hum_oversampling(constants.OS_H_1)
        self.set_temp_oversampling(constants.OS_T_1)
        self.set_press_oversampling(constants.OS_P_1)
        self.set_filter(constants.FILTER_OFF)
        self.set_mode(constants.MODE_FORCE)
        # wait for it...
        while self.is_measuring:
            utime.sleep_ms(10)
