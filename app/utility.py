from flask import request
from werkzeug.datastructures import ImmutableMultiDict

# from app import geoip
from app import ip2location
from app import cache

from binascii import *
from Crypto.Hash import MD5
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
from Crypto.Util.py3compat import *
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto import Random

from sqlalchemy.ext.declarative import DeclarativeMeta
import json
import datetime
import decimal
import uuid
import os
import time
import base64
import requests
import re
import random


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def get_json(dict):
    return json.dumps(dict, cls=CJsonEncoder)


def get_dict(str):
    return json.loads(str)


def get_md5(plain):
    obj = MD5.new()
    obj.update(plain.encode("utf-8"))  # gb2312 Or utf-8
    cipher = obj.hexdigest()
    return cipher


def get_file_md5(path):
    chunk_size = 8192
    obj = MD5.new()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if len(chunk):
                obj.update(chunk)
            else:
                break

    cipher = obj.hexdigest()
    return cipher


def get_file_mtime(path):
    t = os.path.getmtime(path)
    return int(t)


def get_file_size(path):
    size = os.path.getsize(path)
    return size


def get_short(text, length):
    if len(text) > length:
        return text[0:length] + "..."
    else:
        return text


def get_all_files(path):
    all_files = []
    for root, dirs, files in os.walk(path):
        for name in files:
            all_files.append((name, root, os.path.join(root, name)))
            print(root)
        for name in dirs:
            # all_files.append(os.path.join(root, name))
            pass
    return all_files


def dt_2_dts(date_time):
    return date_time.strftime('%Y-%m-%d %H:%M:%S')


def dts_2_dt(date_time_string):
    return datetime.datetime.strptime(date_time_string, '%Y-%m-%d %H:%M:%S')


def ts_2_dts(time_stamp):
    time_struct = time.localtime(time_stamp)
    return time.strftime('%Y-%m-%d %H:%M:%S', time_struct)


def dts_2_ts(date_time_string):
    time_struct = time.strptime(date_time_string, '%Y-%m-%d %H:%M:%S')
    return int(time.mktime(time_struct))


def dt_2_ts(date_time):
    return int(time.mktime(date_time.timetuple()))


def ts_2_dt(time_stamp):
    return datetime.datetime.fromtimestamp(time_stamp)


def get_current_timestamp13():
    return round(time.time() * 1000)


def get_current_timestamp10():
    return int(time.time())


def get_date_list(days):
    result = []

    current_date = datetime.datetime.now()

    for i in range(days):
        date_str = current_date.strftime("%Y-%m-%d")
        result.append(date_str)

        current_date -= datetime.timedelta(days=1)

    return result


def format_file_size(size):
    KB = 1024
    MB = 1024 * KB
    GB = 1024 * MB
    TB = 1024 * GB

    if size > TB:
        return "%.2f TB" % (size / TB)
    elif size > GB:
        return "%.2f GB" % (size / GB)
    elif size > MB:
        return "%.2f MB" % (size / MB)
    elif size > KB:
        return "%.2f KB" % (size / KB)
    else:
        return "%d Byte" % (size)


def get_rand_string(len, force=False):
    result = ""

    while True:
        seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

        sa = []
        for i in range(len):
            sa.append(random.choice(seed))
        result = ''.join(sa)

        if not force:
            break

        if re.search('[a-z]', result) and re.search('[A-Z]', result) and re.search('[0-9]', result):
            break

    return result

def pad(data_to_pad, block_size, style='pkcs7'):
    padding_len = block_size - len(data_to_pad) % block_size  # 1-8
    if style == 'pkcs7':
        padding = bchr(padding_len) * padding_len
    elif style == 'x923':
        padding = bchr(0) * (padding_len - 1) + bchr(padding_len)
    elif style == 'iso7816':
        padding = bchr(128) + bchr(0) * (padding_len - 1)  # iso7816时填充长度为1-8
    elif style == 'zero':
        padding = bchr(0) * (padding_len % block_size)  # zero时填充长度为0-7
    else:
        raise ValueError("Unknown padding style")
    return data_to_pad + padding


def unpad(padded_data, block_size, style='pkcs7'):
    pdata_len = len(padded_data)
    if pdata_len % block_size:
        raise ValueError("Input data is not padded")
    if style in ('pkcs7', 'x923'):
        padding_len = bord(padded_data[-1])
        if padding_len < 1 or padding_len > min(block_size, pdata_len):
            raise ValueError("Padding is incorrect.")
        if style == 'pkcs7':
            if padded_data[-padding_len:] != bchr(padding_len) * padding_len:
                raise ValueError("PKCS#7 padding is incorrect.")
        else:
            if padded_data[-padding_len:-1] != bchr(0) * (padding_len - 1):
                raise ValueError("ANSI X.923 padding is incorrect.")
    elif style == 'iso7816':
        padding_len = pdata_len - padded_data.rfind(bchr(128))
        if padding_len < 1 or padding_len > min(block_size, pdata_len):
            raise ValueError("Padding is incorrect.")
        if padding_len > 1 and padded_data[1 - padding_len:] != bchr(0) * (padding_len - 1):
            raise ValueError("ISO 7816-4 padding is incorrect.")
    elif style == 'zero':
        padding_len = pdata_len - len(padded_data.rstrip(bchr(0)))
        if padding_len < 0 or padding_len > min(block_size, pdata_len) - 1:
            raise ValueError("Padding is incorrect.")
        if padding_len > 0 and padded_data[-padding_len:] != bchr(0) * padding_len:
            raise ValueError("Zero padding is incorrect.")
    else:
        raise ValueError("Unknown padding style")
    return padded_data if padding_len == 0 else padded_data[:-padding_len]


def des_encode(plain, key=None):
    if key == None:
        key = get_des_key()

    # MODE_CBC need IV
    obj = DES.new(key.encode('utf-8'), DES.MODE_ECB)
    plain = plain.encode("utf-8")
    plain = pad(plain, 8, "zero")
    cipher = hexlify(obj.encrypt(plain))
    return cipher.decode("utf-8")


def des_decode(cipher, key=None):
    if key == None:
        key = get_des_key()

    obj = DES.new(key.encode('utf-8'), DES.MODE_ECB)
    plain = obj.decrypt(unhexlify(cipher))
    plain = unpad(plain, 8, "zero")
    return plain.decode("utf-8")


def base64_encode(plain):
    chiper = base64.b64encode(plain.encode('utf-8'))
    return str(chiper, 'utf-8')


def base64_decode(cipher):
    plain = base64.b64decode(cipher.encode('utf-8'))
    return str(plain, 'utf-8')


def get_uuid():
    return str(uuid.uuid4())  # uuid1机器码

def get_args(request):
    args = None
    if request.method == 'POST':
        if request.content_type.startswith("application/json"):
            args = request.get_json()
        elif request.content_type.startswith("application/x-www-form-urlencoded"):
            args = request.form.to_dict()
        elif request.content_type.startswith("multipart/form-data"):
            args = {**request.files.to_dict(), **request.form.to_dict()}
    elif request.method == 'GET':
        args = request.args.to_dict()
    return args


def get_ip(ip):
    ip_info = None

    try:
        # ip_info = geoip.city(ip)
        ip_info = ip2location.get_all(ip)
    except Exception:
        pass

    return ip_info


# --------------------Check--------------------


def compare_version(version1, version2):
    v1 = version1.split(".")
    v2 = version2.split(".")

    if len(v1) != len(v2):
        return False

    for i in range(len(v1)):
        if int(v1[i]) < int(v2[i]):
            return False
        elif int(v1[i]) > int(v2[i]):
            return True

    return True


def str_contains(str, sub, sep=","):
    str_list = str.split(sep)
    str_list = [x.strip() for x in str_list]  # trim一下
    str_list = list(filter(lambda x: x.strip(), str_list))  # 去掉空字符串
    if sub in str_list:
        return True
    else:
        return False


# --------------------Cache--------------------

def get_cache(key):
    return cache.get(key)


def set_cache(key, value):
    return cache.set(key, value)


def set_cachex(key, value, expires):
    return cache.setex(key, expires, value)


def incr_cache(key):
    return cache.incr(key, amount=1)


def decr_cache(key):
    return cache.decr(key, amount=1)


def get_des_key():
    result = get_cache("config:des_key")
    return "" if result == None else result;


def set_des_key(des_key):
    return set_cache("config:des_key", des_key)


def get_is_encrypt():
    result = get_cache("config:is_encrypt")
    return True if result == "True" else False


def set_is_encrypt(is_encrypt):
    return set_cache("config:is_encrypt", is_encrypt)


def get_is_offline():
    result = get_cache("config:is_offline")
    return True if result == "True" else False


def set_is_offline(is_offline):
    return set_cache("config:is_offline", is_offline)


def get_domain():
    result = get_cache("config:domain")
    return "" if result == None else result;


def set_domain(domain):
    return set_cache("config:domain", domain)


def get_ua_regex():
    result = get_cache("config:ua_regex")
    return "" if result == None else result;


def set_ua_regex(ua_regex):
    return set_cache("config:ua_regex", ua_regex)


# --------------------Net--------------------

def get(url, timeout=60):
    res = requests.get(url, timeout=timeout)
    # print(url, res.text)
    return res.text


def post(url, payload, timeout=60):
    res = requests.post(url, data=payload, timeout=timeout)
    # print(url, res.text)
    return res.text
