import serial
import time
import mysql.connector
from mysql.connector import Error
import re
# 串口设置
ser = serial.Serial('COM8', 38400, timeout=1)  # 根据实际情况调整
time.sleep(2)  # 等待串口稳定

# MySQL连接设置
try:
    db = mysql.connector.connect(
        host="localhost",  # 使用主机名或IP地址
        user="newuser",             # 使用 root 用户
        password="qwe12345",      # 输入你的密码
        database="health_monitoring"  # 连接到 health_monitoring 数据库
    )
    cursor = db.cursor()

    # 创建表格（如果不存在）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        heart_rate INT,
        spo2 INT,
        blood_pressure INT,
        std INT,
        spd INT
    )
    """)
    print("Database connection successful!")
except Error as e:
    print(f"Error while connecting to MySQL: {e}")
    exit()

# 将数据插入到数据库
def insert_data(hr, spo2, std, spd):
    try:
        # 转换为整数，确保数据类型正确
        hr = int(hr)
        spo2 = int(spo2)
        std = int(std)
        spd = int(spd)
        cursor.execute("INSERT INTO sensor_data (heart_rate, spo2, std, spd) VALUES (%s, %s,  %s, %s)", (hr, spo2,  std, spd))
        db.commit()
        print(f"Inserted: HR={hr} bpm, SpO2={spo2}%,  std={std}, spd={spd}")
    except Error as e:
        print(f"Error while inserting data: {e}")


# 读取数据

def read_data():
    try:
        while True:
            if ser.in_waiting > 0:
                # 读取一行数据，并忽略解码错误
                data = ser.readline().decode('utf-8', errors='ignore').strip()

                # 打印并存储数据
                if "HR=" in data and "SPO2=" in data and "std=" in data and "spd=" in data:
                    # 使用正则表达式提取 HR, SPO2, std 和 spd 的数值
                    hr_match = re.search(r"HR=(\d+)", data)
                    spo2_match = re.search(r"SPO2=(\d+)", data)
                    std_match = re.search(r"std=(\d+)", data)
                    spd_match = re.search(r"spd=(\d+)", data)

                    if hr_match and spo2_match and std_match and spd_match:
                        # 提取匹配到的数值
                        hr = int(hr_match.group(1))
                        spo2 = int(spo2_match.group(1))
                        std = int(std_match.group(1))
                        spd = int(spd_match.group(1))

                        # 打印读取的传感器数据
                        print(f"Heart Rate (HR): {hr} bpm")
                        print(f"SpO2: {spo2}%")
                        print(f"Blood Pressure (BP): {std} mmHg")
                        print(f"std: {std}, spd: {spd}")
                        
                         # 只有当所有数据都不为零时才插入数据库
                        if hr != 0 and spo2 != 0 and std != 0 and spd != 0:
                            try:
                                # 将数据插入数据库
                                insert_data(hr, spo2, std, spd)
                            except ValueError as ve:
                                print(f"Error while inserting data: {ve}")
                        else:
                            print("Sensor data contains zero value, skipping database insertion.")
                    else:
                        print("Invalid data format received.")
            time.sleep(1)  # 每秒检查一次串口数据
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 关闭资源
        ser.close()  # 关闭串口连接
        cursor.close()
        db.close()  # 关闭数据库连接
        print("Resources closed.")

if __name__ == "__main__":
    read_data()
