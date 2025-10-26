import requests
import json

def delete_msg(msg_id):
    try:
        headers = {
            "Authorization": "^:X,=56L7o4F#e;y",  # Token
            "Content-Type": "application/json"
        }
        # 使用post上报的请求体
        json_data = {
      "message_id": msg_id
    }

        response = requests.post('http://127.0.0.1:3001/delete_msg', headers=headers, json=json_data)
        status_code = response.status_code
        # 消息撤回状态返回
        if status_code == 200:
            body = json.loads(response.text)
            status = body["status"]
            if status == "ok":
                return json.dumps({"status":"success","data":None})
            else:
                message = body['message']
                return json.dumps({"status":"error","data":str(message)})
        else:
            return json.dumps({"status":"fatal","data":str(status_code)})
    except:
        return json.dumps({"status":"fatal","data":"Connection Refused"})