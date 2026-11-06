import time
import json
import ssl
import network
import ntptime
import machine
from machine import Pin, SoftI2C
from umqtt.simple import MQTTClient
from bme280 import bme280_instance
import constants

# ============================================================================
# 1. KONFIGURACJA SIECI I AWS
# ============================================================================
WIFI_SSID = "dhaixbcisb"
WIFI_PASS = "Chorwacja2019"

AWS_ENDPOINT = "awfa1k04coxt8-ats.iot.eu-north-1.amazonaws.com"
CLIENT_ID    = "esp32_1"
TOPIC_PUB    = "esp32/telemetry"

FILE_CA   = "AmazonRootCA1.pem"
FILE_CERT = "certificate.pem.crt"
FILE_KEY  = "private.pem.key"

# ============================================================================
# 2. FUNKCJE POMOCNICZE
# ============================================================================
def get_formatted_time(utc_offset_hours=1):
    # ntptime.settime() ustawia czas w strefie UTC (0).
    # Dodajemy przesunięcie dla Polski (1h dla czasu zimowego CET, 2h dla letniego CEST).
    local_seconds = time.time() + (utc_offset_hours * 3600)
    t = time.localtime(local_seconds)
    
    # Formatowanie do czytelnego ciągu: YYYY-MM-DD HH:MM:SS
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )

def get_sleep_ms_until_next_hour():
    now = time.localtime()
    minute = now[4]
    second = now[5]
    
    # Obliczenie sekund pozostałych do pełnej godziny
    seconds_remaining = (59 - minute) * 60 + (60 - second)
    
    # Zabezpieczenie przed zbyt krótkim uśpieniem (min. 5 sekund)
    if seconds_remaining < 5:
        seconds_remaining = 3600

    print(f"Aktualny czas: {now[3]:02d}:{minute:02d}:{second:02d}. Uśpienie na {seconds_remaining} sekund.")
    return seconds_remaining * 1000

def get_sleep_ms_until_next_5_minutes():
    now = time.localtime()
    minute = now[4]
    second = now[5]
    
    # Sekundy od początku bieżącego 5-minutowego okna
    seconds_in_block = (minute % 5) * 60 + second
    
    # Sekundy pozostałe do najbliższych pełnych 5 minut (300 s)
    seconds_remaining = 300 - seconds_in_block
    
    if seconds_remaining < 5:
        seconds_remaining = 300

    print(f"Aktualny czas: {now[3]:02d}:{minute:02d}:{second:02d}. Uśpienie na {seconds_remaining} sekund (do równych 5 min).")
    return seconds_remaining * 1000

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Łączenie z Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        retries = 0
        while not wlan.isconnected() and retries < 20:
            time.sleep(0.5)
            print(".", end="")
            retries += 1
    if wlan.isconnected():
        print("\nPołączono z Wi-Fi! IP:", wlan.ifconfig()[0])
        return True
    else:
        print("\nNie udało się połączyć z Wi-Fi.")
        return False

def sync_time():
    print("Synchronizacja czasu NTP...")
    for _ in range(5):
        try:
            ntptime.settime()
            print("Czas zsynchronizowany!")
            return True
        except Exception as e:
            print("Ponawianie próby NTP...", e)
            time.sleep(2)
    return False

def read_file(filename):
    with open(filename, "rb") as f:
        return f.read()

# ============================================================================
# 3. GŁÓWNA LOGIKA POMIARU I UŚPIENIA
# ============================================================================
def run():
    wifi_ok = connect_wifi()
    if wifi_ok:
        sync_time()

    # Inicjalizacja I2C oraz czujnika BME280
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    bme = bme280_instance(i2c_connection=i2c, bme_address=0x76)
    bme.set_mode(constants.MODE_NORMAL)

    if wifi_ok:
        try:
            ca_cert  = read_file(FILE_CA)
            dev_cert = read_file(FILE_CERT)
            dev_key  = read_file(FILE_KEY)

            ssl_params = {
                "key": dev_key,
                "cert": dev_cert,
                "server_hostname": AWS_ENDPOINT
            }

            client = MQTTClient(
                client_id=CLIENT_ID,
                server=AWS_ENDPOINT,
                port=8883,
                keepalive=60,
                ssl=True,
                ssl_params=ssl_params
            )

            print("Łączenie z AWS IoT Core...")
            client.connect()
            print("Połączono pomyślnie z AWS IoT Core!")

            # Pobranie danych z czujnika
            press, temp, hum = bme.get_data()

            payload = json.dumps({
                "device_id": CLIENT_ID,
                "temperature": round(temp, 2),
                "humidity": round(hum, 2),
                "pressure": round(press, 2),
                "timestamp": get_formatted_time(utc_offset_hours=1)
            })

            client.publish(TOPIC_PUB, payload)
            print("Wysłano ramkę JSON do AWS:", payload)
            time.sleep(1)
            client.disconnect()

        except Exception as e:
            print("Błąd wysyłania danych do AWS:", e)

    # Obliczenie czasu uśpienia do pełnej godziny i przejście w tryb Deep Sleep
    sleep_ms = get_sleep_ms_until_next_5_minutes()
    print("Przejście w tryb Deep Sleep...")
    machine.deepsleep(sleep_ms)

while True:
    run()