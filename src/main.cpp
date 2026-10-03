#include <Arduino.h>
#include <driver/timer.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <BluetoothSerial.h>

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth nie jest włączony!
#endif

BluetoothSerial SerialBT;

hw_timer_t *timer = NULL;

volatile int sekundy = 0;
int minuta = 0;
volatile bool flagaSekundy = false;

float temperature[24];
float humidity[24];
float pressure[24];

Adafruit_BME280 bme;

void printData(int minuta){
  for (byte i = 0; i <= minuta; i++){
    SerialBT.print("Minuta: ");
    SerialBT.print(i);
    SerialBT.print(" ,temperatura: ");
    SerialBT.print(temperature[i]);
    SerialBT.print(" ,wilgotnosc: ");
    SerialBT.print(humidity[i]);
    SerialBT.print(" ,cisnienie: ");
    SerialBT.print(pressure[i]);
    SerialBT.println();
  }
}

void pomiar(int minuta){
  if(minuta > 24){
    minuta = 0;
  }
  temperature[minuta] = bme.readTemperature();
  humidity[minuta] = bme.readHumidity();
  pressure[minuta] = bme.readPressure() / 100.0F; // Zamiana Pa na hPa
}

void IRAM_ATTR onTimer(){
  sekundy++;
  flagaSekundy = true;
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);

  timer = timerBegin(0, 80, true);

  timerAttachInterrupt(timer, &onTimer, true);

  timerAlarmWrite(timer, 1000000, true);

  timerAlarmEnable(timer);

  //inicjalizacja bme
  if (!bme.begin(0x76)){
    Serial.println("Nie znaleziono czujnika bme!");
    while(1);
  }

  SerialBT.begin("Stacja_pogodowa"); 
  Serial.println("Bluetooth gotowy. Czekam na polecenia...");
}

void loop() {
  if(flagaSekundy && sekundy % 60 == 0){
    minuta++;
    pomiar(minuta);
    flagaSekundy = false;
  }

  if(SerialBT.available()){
    char incomingChar = SerialBT.read();

    if(incomingChar == '1'){
      printData(minuta);
    }
  }
}