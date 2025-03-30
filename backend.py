from flask import Flask, jsonify
from flask_cors import CORS  # CORS'u import ediyoruz
from pymavlink import mavutil
import time

app = Flask(__name__)

# CORS'u tüm kaynaklardan gelen isteklere izin verecek şekilde yapılandırıyoruz
CORS(app)

# MAVLink bağlantısı (Simülatör veya Drone bağlantısı)
connection = mavutil.mavlink_connection('tcp:127.0.0.1:5762')

# Bağlantıyı bekliyoruz ve simülatörden heartbeat mesajını alıyoruz
connection.wait_heartbeat(timeout=10)  # 10 saniye boyunca bağlantıyı bekle
print("Bağlantı başarılı, sistem ID:", connection.target_system)

# Telemetri verilerini gönderen fonksiyon
def generate_telemetry():
    # Bu fonksiyon sürekli olarak telemetri verisi döndürür
    drone_data = {}

    # Hedef bilgilerini başlangıç olarak tanımlayalım
    drone_data['takim_numarasi'] = 1
    drone_data['hedef_merkez_X'] = 300
    drone_data['hedef_merkez_Y'] = 230
    drone_data['hedef_genislik'] = 30
    drone_data['hedef_yukseklik'] = 43

    # GPS verilerini almak
    msg = connection.recv_match(type='GPS_RAW_INT', blocking=True)
    drone_data['iha_enlem'] = msg.lat / 1e7  # Enlem
    drone_data['iha_boylam'] = msg.lon / 1e7  # Boylam
    drone_data['iha_irtifa'] = msg.alt  # Yükseklik

    # Dikilme (pitch), yatış (roll) ve yönelme (heading) verilerini almak
    msg = connection.recv_match(type='ATTITUDE', blocking=True)
    drone_data['iha_dikilme'] = msg.pitch  # Pitch
    drone_data['iha_yatis'] = msg.roll  # Roll
    drone_data['iha_yonelme'] = msg.yaw  # Yaw (heading)

    # Hız bilgisini almak
    msg = connection.recv_match(type='VFR_HUD', blocking=True)
    drone_data['iha_hiz'] = msg.groundspeed  # Hız (ground speed)

    # Batarya bilgisini almak
    msg = connection.recv_match(type='BATTERY_STATUS', blocking=True)
    drone_data['iha_batarya'] = msg.battery_remaining  # Batarya yüzdesi

    # Otonomi durumu (Açık / Kapalı)
    drone_data['iha_otonom'] = 1  # Eğer otonomi aktifse, 1 (aktif)

    # Kilitlenme durumu (Açık / Kapalı)
    drone_data['iha_kilitlenme'] = 1  # Simülasyonda kilitli olduğunu varsayalım

    # GPS saati (UTC)
    msg = connection.recv_match(type='SYSTEM_TIME', blocking=True)
    time_unix_usec = msg.time_unix_usec
    time_unix_sec = time_unix_usec // 1000000  # Mikro saniyeyi saniyeye çevir
    gps_saat = time.gmtime(time_unix_sec)  # UTC zamanını alıyoruz
    drone_data['gps_saati'] = {
        'saat': gps_saat.tm_hour,
        'dakika': gps_saat.tm_min,
        'saniye': gps_saat.tm_sec,
        'milisaniye': (time_unix_usec // 1000) % 1000  # Milisaniyeyi de ekliyoruz
    }

    return drone_data

@app.route('/telemetry', methods=['GET'])
def get_telemetry():
    # Telemetri verilerini döndürüyoruz
    drone_data = generate_telemetry()
    return jsonify(drone_data)  # JSON formatında veri döndürüyoruz

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)  # Flask uygulamasını başlatıyoruz
