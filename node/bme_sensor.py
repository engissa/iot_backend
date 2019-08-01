import bme680
import time


class bme_sensor(object):
    '''
    class to manage sensor hardware component and get readings
    '''
    def __init__(self):
        self.sensor = bme680.BME680()
        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)
        self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        self.sensor.set_gas_heater_temperature(320)
        self.sensor.set_gas_heater_duration(150)
        self.sensor.select_gas_heater_profile(0)
        self.hum_baseline = 40.0
        self.hum_weighting = 0.25
        self.burn_in_data = []
        self. gas_baseline = 0.0

    def activate_sensor(self):

        start_time = time.time()
        curr_time = time.time()
        burn_in_time = 300
        burn_in_data = []
        while curr_time - start_time < burn_in_time:
            curr_time = time.time()
            if self.sensor.get_sensor_data() and self.sensor.data.heat_stable:
                gas = self.sensor.data.gas_resistance
                burn_in_data.append(gas)
                print("Gas: {0} Ohms".format(gas))
                time.sleep(1)
        self.gas_baseline = sum(burn_in_data[-50:]) / 50.0

    def get_readings(self):
        # hum_baseline = 40.0
        # This sets the balance between humidity and gas reading in the
        # calculation of air_quality_score (25:75, humidity:gas)
        # hum_weighting = 0.25

        while True:
            if self.sensor.get_sensor_data() and self.sensor.data.heat_stable:
                gas = self.sensor.data.gas_resistance
                gas_offset = self.gas_baseline - gas
                hum = self.sensor.data.humidity
                hum_offset = hum - self.hum_baseline
                # Calculate hum_score as the distance from the hum_baseline.
                if hum_offset > 0:
                    hum_score = (100 - self.hum_baseline - hum_offset) / (100 - self.hum_baseline) * (self.hum_weighting * 100)
                else:
                    hum_score = (self.hum_baseline + hum_offset) / self.hum_baseline * (self.hum_weighting * 100)
                # Calculate gas_score as the distance from the gas_baseline.
                if gas_offset > 0:
                    gas_score = (gas / self.gas_baseline) * (100 - (self.hum_weighting * 100))

                else:
                    gas_score = 100 - (self.hum_weighting * 100)

                # Calculate air_quality_score.
                air_quality_score = hum_score + gas_score

                temp_dict = {'temp': self.sensor.data.temperature, 'humid': hum, 'iaq': air_quality_score}
                return temp_dict
