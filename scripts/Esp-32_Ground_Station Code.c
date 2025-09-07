#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <RF24.h>

// NRF24 pins
#define RF_CE   4
#define RF_CSN  5
RF24 radio(RF_CE, RF_CSN);
const byte pipeAddress[6] = "NODE1";

// WiFi
const char* ssid = "anusheel";
const char* password = "anusheel123";

// Supabase
const char* supabase_url = "https://lmmnqygkgacfhnirbwas.supabase.co/rest/v1/sensor_data";
const char* supabase_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxtbW5xeWdrZ2FjZmhuaXJid2FzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcxNDAzMzAsImV4cCI6MjA3MjcxNjMzMH0.4q_3cv8kitBnHqEkHHtniNeE64eoC2X0rEJVQ0utxlE"; // replace with your key

#define LED_BUILTIN 2

struct SensorPacket {
  int8_t temperature;
  uint8_t humidity;
  uint16_t light;
  uint8_t soil;
  uint8_t npk;
  uint8_t uv;
};

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  connectWiFi();

  if (!radio.begin()) { Serial.println("⚠ NRF24 not found!"); while (1); }
  radio.setPALevel(RF24_PA_LOW);
  radio.setDataRate(RF24_250KBPS);
  radio.openReadingPipe(1, pipeAddress);
  radio.startListening();

  Serial.println("✅ ESP32 RX ready.");
}

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 30) { delay(500); Serial.print("."); retries++; }
  if (WiFi.status() == WL_CONNECTED) Serial.println(" ✅ Connected to WiFi");
  else Serial.println(" ⚠ WiFi connection failed");
}

void sendToSupabase(String jsonBody) {
  if (WiFi.status() != WL_CONNECTED) { connectWiFi(); if (WiFi.status() != WL_CONNECTED) return; }

  HTTPClient http;
  http.begin(supabase_url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("apikey", supabase_api_key);
  http.addHeader("Authorization", String("Bearer ") + supabase_api_key);

  int code = http.POST(jsonBody);
  if (code > 0) Serial.println("✅ Supabase Response: " + http.getString());
  else Serial.println("⚠ HTTP POST failed: " + String(code));
  http.end();
}

void loop() {
  if (radio.available()) {
    SensorPacket packet;
    radio.read(&packet, sizeof(packet));

    digitalWrite(LED_BUILTIN, HIGH);

    Serial.print("📥 Packet RX -> ");
    Serial.print(packet.temperature); Serial.print(" °C, ");
    Serial.print(packet.humidity); Serial.print(" %, ");
    Serial.print(packet.light); Serial.print(" lux, ");
    Serial.print(packet.soil); Serial.print(" %, ");
    Serial.print(packet.npk); Serial.print(" %, ");
    Serial.print(packet.uv / 10.0); Serial.println(" UV");

    // Build JSON with fixed node_name
String json = "{";
json += "\"node_name\":\"Node1\",";
json += "\"temperature\":" + String((int)packet.temperature) + ",";
json += "\"humidity\":" + String((int)packet.humidity) + ",";
json += "\"light\":" + String((int)packet.light) + ",";
json += "\"soil_moisture\":" + String((int)packet.soil) + ",";
json += "\"npk\":" + String((int)packet.npk) + ",";
json += "\"uv_index\":" + String(packet.uv / 10.0, 1);
json += "}";

    Serial.print("🚀 Sending JSON -> ");
    Serial.println(json);

    sendToSupabase(json);

    delay(500);
    digitalWrite(LED_BUILTIN, LOW);
  }
}
