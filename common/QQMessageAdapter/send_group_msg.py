import requests
import json

def send_group_msg(group_id,msg):
    try:
        # 使用post上报的请求头
        headers = {
            "Authorization": "^:X,=56L7o4F#e;y",  # Token
            "Content-Type": "application/json"
        }
        # 使用post上报的请求体
        json_data = {
            "group_id": group_id,
            "message": msg
        }

        response = requests.post('http://127.0.0.1:3001/send_group_msg', headers=headers, json=json_data)
        status_code = response.status_code
        # 消息发送状态返回
        if status_code == 200:
            body = json.loads(response.text)
            status = body["status"]
            if status == "ok":
                data = body['data']
                msg_id = data['message_id']
                return json.dumps({"status":"success","data":str(msg_id)})
            else:
                message = body['message']
                return json.dumps({"status":"error","data":str(message)})
        else:
            return json.dumps({"status":"fatal","data":str(status_code)})
    except:
        return json.dumps({"status":"fatal","data":"Connection Refused"})