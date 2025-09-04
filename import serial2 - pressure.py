import mysql.connector
import requests
import json

# MySQL连接设置
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",       # 数据库地址
        user="newuser",         # 数据库用户名
        password="qwe12345", # 数据库密码
        database="health_monitoring"  # 连接到 health_monitoring 数据库
    )


# 获取access_token
def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=jGZjxh6BpX6NNXzUDha7n6UA&client_secret=wKpY5AP80wzLddtfa96Xu3kPsDhXBVH4"
    
    response = requests.post(url)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Failed to get access token:", response.text)
        return None

# 从MySQL读取10组数据
def fetch_data_from_db():
    db = connect_to_db()
    cursor = db.cursor()
    cursor.execute("SELECT heart_rate, spo2, std, spd FROM sensor_data LIMIT 10 OFFSET 0")
    data = cursor.fetchall()
    db.close()
    return data


# 生成健康报告
def generate_health_report(data):
    access_token = get_access_token()
    if access_token is None:
        print("Error: No access token. Cannot proceed with generating the report.")
        return

    # 拼接健康报告请求 URL
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={access_token}"

    # 构建合并后的数据内容
    prompt = "根据以下数据综合分析健康状况：\n"
    for row in data:
        # 跳过 id 和 timestamp，只处理数据部分
        hr, spo2, std, spd = row[2], row[3], row[4], row[5]
        prompt += f"心率（HR）：{hr} bpm，血氧（SpO2）：{spo2}%，收缩压（std）：{std} mmHg，舒张压（spd）：{spd} mmHg\n"

    payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    })
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # 发送请求到大语言模型API
    response = requests.post(url, headers=headers, data=payload)
    
    if response.status_code == 200:
        try:
            # 尝试解析JSON
            result = response.json()
          # print(f"API response: {json.dumps(result, indent=2)}")  # 打印完整的API响应，查看实际结构
            
            # 检查返回结构
            if 'result' in result:
                result_content = result['result']  # 直接使用字符串
                print(f"Health Report for the combined data:")
                print(result_content)  # 输出综合健康报告内容
            else:
                print(f"Missing 'result' key in response: {result}")
        
        except json.JSONDecodeError:
            print(f"Failed to decode JSON response: {response.text}")
    else:
        print(f"Failed to generate health report. Error: {response.text}")


# 提问并获取模型回答
def ask_question_to_model(question):
    access_token = get_access_token()
    if access_token is None:
        print("Error: No access token. Cannot proceed with generating the report.")
        return

    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={access_token}"

    payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ]
    })
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers, data=payload)
    
    if response.status_code == 200:
        try:
            result = response.json()
            if 'result' in result:
                result_content = result['result']  # 直接使用字符串
                print(f"Answer from the model:")
                print(result_content)  # 输出模型回答
            else:
                print(f"Missing 'result' key in response: {result}")
        
        except json.JSONDecodeError:
            print(f"Failed to decode JSON response: {response.text}")
    else:
        print(f"Failed to generate model answer. Error: {response.text}")



# 从MySQL读取指定行数据
def fetch_specific_rows_from_db(start_row, end_row):
    db = connect_to_db()
    cursor = db.cursor()

    # 计算偏移量
    offset = start_row - 1  # MySQL LIMIT 从0开始
    query = f"SELECT id, timestamp, heart_rate, spo2, std, spd FROM sensor_data LIMIT {end_row - start_row + 1} OFFSET {offset}"
    # 执行SQL查询
    #query = f"SELECT id, timestamp, heart_rate, spo2, std, spd FROM sensor_data LIMIT {end_row - start_row + 1} OFFSET {offset}"
    cursor.execute(query)

    # 获取查询结果
    data = cursor.fetchall()
    db.close()
    return data


# 打印数据
def print_data(data):
    for row in data:
        # 解包每一行数据
        id, timestamp, heart_rate, spo2, std, spd = row
        # 打印数据
        print(f"ID: {id}, 时间: {timestamp}, 心率: {heart_rate} , 血氧: {spo2}%, 收缩压（std）：{std} mmHg，舒张压（spd）：{spd} mmHg")
# 主程序
def main():

    start_row =  48 # 起始行
    end_row =  53 # 结束行

    # 从数据库读取数据
    dataa = fetch_specific_rows_from_db(start_row, end_row)

    if dataa:
        print(f"Fetched data from row {start_row} to {end_row}:")
        print_data(dataa)

# 从数据库读取数据
    data = fetch_data_from_db()
    # 确保有数据
    if not data:
        print("No data retrieved from database.")
        return    

    print(f"Fetched {len(dataa)} records from the database.")

 
    # 生成健康报告
    generate_health_report(dataa)

    while True:
        # 让用户输入问题
        user_question = input("请输入您的健康问题（输入 'exit' 退出）：")
        ask_question_to_model(user_question)
        
        if user_question.lower() == 'exit':
            print("退出程序。")
            break
 
    

if __name__ == "__main__":
    main()
