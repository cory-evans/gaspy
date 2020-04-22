import json
import pickle
import smtplib
import requests

import os
import configparser

try:
    os.mkdir('data')
except FileExistsError:
    pass

config = configparser.ConfigParser()

if os.path.exists('config.ini'):
    config.read('config.ini')
else:
    config['gaspy'] = {
        'email': 'example @ domain.com',
        'password': 'passwd',
        'fuel_type': '5',
        'latitude': '',
        'longitude': ''
    }

    config['email'] = {
        'from_addr': 'example @ domain.com',
        'from_addr_password': 'passwd',
        'to_addr': 'example @ domain.com'
    }

    config.write(open('config.ini', 'w'))
    print('please edit config.ini')
    quit()


base_url = 'https://gaspy.nz/api/v1'
cookie_save_file = 'data/.cookies.pickle'


def send_email(config, email):
    from_addr = config['email']['from_addr']
    to_addr = config['email']['to_addr']

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(from_addr, config['email']['from_addr_password'])

    msg = f'''\
From: {from_addr}
To: {to_addr}
Subject: {email['subject']}

{email['body']}
    '''

    server.sendmail(from_addr, to_addr, msg)
    server.close()


def has_expired_cookies_or_no_cookies(cookie_jar: requests.cookies.RequestsCookieJar):
    # A crued way of finding expired cookies. . .

    cookie_jar_clone = cookie_jar.copy()
    cookie_num = len(cookie_jar_clone.keys())
    if cookie_num == 0:
        return True

    cookie_jar_clone.clear_expired_cookies()

    return not cookie_num == len(cookie_jar_clone.keys())

def load_cookies(filename=cookie_save_file):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return requests.cookies.RequestsCookieJar()

def save_cookies(cookie_jar, filename=cookie_save_file):
    with open(filename, 'wb') as f:
        pickle.dump(cookie_jar, f)

def init_client(cookie_jar=None):
    url = base_url + '/Public/init'
    headers = {
        'user-agent': 'okhttp/3.10.0'
    }

    return requests.get(url, headers=headers, cookies=cookie_jar)


def login_client(cookie_jar, email, password):
    url = base_url + '/Public/login'
    headers = {
        'user-agent': 'okhttp/3.10.0'
    }

    data = {
        'email': email,
        'password': password
    }

    return requests.post(url, headers=headers, cookies=cookie_jar, data=data)


def search_prices(cookie_jar, lat, lon, fuel_type: str = '5', distance: int = 20):
    url = base_url + '/FuelPrice/searchFuelPrices'
    headers = {
        'user-agent': 'okhttp/3.10.0'
    }

    # make sure distance is in between 10 & 100
    distance = min(100, distance)
    distance = max(10, distance)

    data = {
        'device_type': 'A',
        'distance':  str(distance) + '.0',
        'fuel_type_id': fuel_type,
        'is_mock_location': 'false',
        'latitude': lat,
        'longitude': lon,
        'order_by': 'price',
        'start': '0'
    }

    return requests.post(url, headers=headers, cookies=cookie_jar, data=data)


auth_cookie_jar = requests.cookies.RequestsCookieJar()
auth_cookie_jar.update(
    load_cookies()
)

# refresh cookies if needed
if has_expired_cookies_or_no_cookies(auth_cookie_jar):
    print('Initialising client. . .')
    init = init_client(auth_cookie_jar)
    auth_cookie_jar.update(init.cookies)

    client_data_r = login_client(auth_cookie_jar, config['gaspy']['email'], config['gaspy']['password'])

    save_cookies(auth_cookie_jar)

else:
    init_client(auth_cookie_jar)


prices = search_prices(
    auth_cookie_jar,
    config['gaspy']['latitude'],
    config['gaspy']['longitude'],
    fuel_type=config['gaspy']['fuel_type']
)

prices_data = prices.json()['data'][:4]
prices_data = {s['station_key']: s for s in prices_data}

try:
    with open('data/current_prices.json', 'r') as f:
        last_prices = json.load(f)
except FileNotFoundError:
    last_prices = {}

with open('data/current_prices.json', 'w') as f:
    json.dump(prices_data, f)


cheapest_key = list(prices_data.keys())[0]
if cheapest_key in last_prices:
    send_notif = float(prices_data[cheapest_key]['current_price']) < float(last_prices[cheapest_key]['current_price'])
else:
    quit()

email_body = ''
for key, s in prices_data.items():
    email_body += s['station_name'] + ' - $' + str(round(float(s['current_price']) / 100, 3)) + '\n'


email = {
    'subject': f'FUEL - {prices_data[cheapest_key]["station_name"]} has dropped from {last_prices[cheapest_key]["current_price"]}c to {prices_data[cheapest_key]["current_price"]}c per litre.',
    'body': email_body
}

if send_notif:
    send_email(config, email)
