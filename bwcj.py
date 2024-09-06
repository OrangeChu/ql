"""
霸王茶姬签到

打开微信小程序抓webapi.qmai.cn里面的qm-user-token(一般在请求头里)填到变量bwcjck里面即可

还需要抓取 userId(在https://webapi.qmai.cn/web/cmk-center/sign/takePartInSign接口的返回值中可找到), 填到变量bwcjuid

支持多用户运行

多用户用&或者@隔开
例如账号1：10086 账号2： 1008611
则变量为10086&1008611
export bwcjck=""
export bwcjuid=""

注意：ck 和 uid 需要顺序对应

cron: 0 0,7 * * *
const $ = new Env("霸王茶姬签到");
"""
import requests
import re
import os
import time
import hashlib
from os import path

global send_msg
send_msg = ''

# 发送通知
def load_send():
    cur_path = path.abspath(path.dirname(__file__))
    notify_file = cur_path + "/notify.py"

    if path.exists(notify_file):
        try:
            from notify import send  # 导入模块的send为notify_send
            print("加载通知服务成功！")
            return send  # 返回导入的函数
        except ImportError:
            print("加载通知服务失败~")
    else:
        print("加载通知服务失败~")

    return False  # 返回False表示未成功加载通知服务

# 分割变量
if 'bwcjck' in os.environ:
    bwcjck = re.split("@|&", os.environ.get("bwcjck"))
    print(f'查找到{len(bwcjck)}个账号')
    send_msg += f'查找到{len(bwcjck)}个账号\n'
else:
    bwcjck = ['']
    print('无bwcjck变量')
    send_msg += '无bwcjck变量\n'
if 'bwcjuid' in os.environ:
    bwcjuid = re.split("@|&", os.environ.get("bwcjuid"))
else:
    bwcjuid = ['']
    print('无bwcjuid变量')
    send_msg += '无bwcjuid变量\n'


# 生成哈希
def generate_hash(activity_id, timestamp, user_id):
    # 反转 activity_id
    reversed_activity_id = activity_id[::-1]

    store_id = 49006

    # 构建参数对象
    params = {
        'activityId': activity_id,
        'sellerId': str(store_id) if store_id is not None else None,
        'timestamp': timestamp,
        'userId': user_id
    }

    # 按键排序并构建查询字符串
    sorted_params = sorted(params.items())
    query_string = '&'.join(f'{key}={value}' for key,
                            value in sorted_params if value is not None)
    query_string += f'&key={reversed_activity_id}'

    # 生成 MD5 哈希
    md5_hash = hashlib.md5(query_string.encode()).hexdigest().upper()

    return md5_hash


def yx(ck, uid):
    global send_msg
    headers = {'qm-user-token': ck, 'User-Agent': 'Mozilla/5.0 (Linux; Android 14; 2201122C Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 XWEB/1160065 MMWEBSDK/20231202 MMWEBID/2247 MicroMessenger/8.0.47.2560(0x28002F30) WeChat/arm64 Weixin NetType/5G Language/zh_CN ABI/arm64 MiniProgramEnv/android', 'qm-from': 'wechat'}
    dl = requests.get(
        url='https://webapi.qmai.cn/web/catering/crm/personal-info', headers=headers).json()
    if dl['message'] == 'ok':
        print(f"账号：{dl['data']['mobilePhone']}登录成功")
        send_msg += f"账号：{dl['data']['mobilePhone']}登录成功\n"
        # 新增旧版签到查询逻辑
        try:
            json_data = {
                "appid": "wxafec6f8422cb357b"
            }
            
            response = requests.post(
                'https://webapi.qmai.cn/web/catering/integral/sign/detail',
                json=json_data,
                headers=headers
            )
            
            result = response.json()
            status_code = result['code']
            
            if status_code == '0':
                continuity_total = result['data']['continuityTotal']
                sign_in_date_list = result['data']['signInDateList']
                activity_id = result['data']['activityId']
                
                today = time.strftime("%Y-%m-%d")
                is_signed_today = today in sign_in_date_list
                
                print(f"旧版签到今天{'已' if is_signed_today else '未'}签到, 已连续签到{continuity_total}天")
                send_msg += f"旧版签到今天{'已' if is_signed_today else '未'}签到, 已连续签到{continuity_total}天\n"

                if not is_signed_today:
                    # 执行签到
                    sign_in(activity_id, headers, dl['data']['mobilePhone'], dl['data'].get('name', ''))
                    send_msg += f"旧版签到成功\n"
            else:
                error_message = result.get('message', '')
                print(f"查询旧版签到失败[{status_code}]: {error_message}")
                send_msg += f"查询旧版签到失败[{status_code}]: {error_message}\n"

        except Exception as e:
            print(f"查询旧版签到出错: {str(e)}")
            send_msg += f"查询旧版签到出错: {str(e)}\n"
        # 继续执行原有的签到逻辑
        timestamp = str(int(time.time() * 1000))
        signature = generate_hash("947079313798000641", timestamp, uid)
        data = {"activityId": "947079313798000641", "appid": "wxafec6f8422cb357b",
                "timestamp": timestamp, "signature": signature, "storeId": 49006}
        lq = requests.post(
            url='https://webapi.qmai.cn/web/cmk-center/sign/takePartInSign', data=data, headers=headers).json()
        if lq['message'] == 'ok':
            print(
                f"签到情况：获得{lq['data']['rewardDetailList'][0]['rewardName']}：{lq['data']['rewardDetailList'][0]['sendNum']}")
            send_msg += f"签到情况：获得{lq['data']['rewardDetailList'][0]['rewardName']}：{lq['data']['rewardDetailList'][0]['sendNum']}\n"
        else:
            print(f"签到情况：{lq['message']}")
            send_msg += f"签到情况：{lq['message']}\n"
    else:
        print('太久不打开小程序存在错误')
        print(dl)
        send_msg += '太久不打开小程序存在错误\n'

def sign_in(activity_id, headers, mobile_phone, user_name):
    global send_msg
    json_data = {
        'activityId': activity_id,
        'mobilePhone': mobile_phone,
        'userName': user_name,
        'appid': 'wxafec6f8422cb357b'
    }
    
    response = requests.post(
        'https://webapi.qmai.cn/web/catering/integral/sign/signIn',
        json=json_data,
        headers=headers
    )
    
    result = response.json()
    status_code = result.get('code', response.status_code)
    
    if status_code == 0:
        print("旧版签到成功")
        send_msg += "旧版签到成功\n"
    else:
        error_message = result.get('message', '')
        print(f"旧版签到失败[{status_code}]: {error_message}")
        send_msg += f"旧版签到失败[{status_code}]: {error_message}\n"


def main():
    global send_msg
    z = 1
    for i, ck in enumerate(bwcjck):
        uid = bwcjuid[i]
        try:
            print(f'登录第{z}个账号')
            send_msg += f'登录第{z}个账号\n'
            print('----------------------')
            yx(ck, uid)
            print('----------------------')
            z = z + 1
        except Exception as e:
            print(f'未知错误：{e}')
            send_msg += f'未知错误：{e}\n'


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'未知错误：{e}')
        send_msg += f'未知错误：{e}\n'
    
    try:
        # 在load_send中获取导入的send函数
        send = load_send()

        # 判断send是否可用再进行调用
        if send:
            send('霸王茶姬签到', send_msg)
        else:
            print('通知服务不可用')
    except Exception as e:
        if e:
            print('发送通知消息失败！')
