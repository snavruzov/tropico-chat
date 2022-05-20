from collections import deque

import requests
from fastapi import Request
from loguru import logger

PROPERTY_FULL_TYPES = [
    "Apartment",
    "Penthouse",
    "Villa",
    "Townhouse",
    "Wholebuilding",
    "Shortterm",
    "Bulk",
    "Bungalow",
    "Duplex",
    "Fullfloor",
    "Halffloor",
    "Plot",
    "Compound",
    "Commercialproperty",
    "Showroom",
    "Offplan",
    "Hotel"
]


def get_ip_info(ip):
    req = requests.get(f'http://ip-api.com/json/{ip}')
    if req.status_code == 200:
        return req.json()

    return None


def get_client_ip(request: Request):
    x_forwarded_for = request.headers.get('x-forwarded-for')
    if x_forwarded_for:
        ip = list(map(str.strip, filter(lambda x: len(x) > 5, x_forwarded_for.split(','))))
        if ip and len(ip) > 0:
            ip = ip[0]
    else:
        ip = request.headers.get('x-real-ip')

    return ip


def json_fixer(js_str: str):
    indexes_js = {}
    queue = deque()
    result = set()

    try:
        for i, c in enumerate(js_str):
            if c == '{':
                queue.append(i)
            elif c == '}':
                if len(queue) == 0:
                    raise IndexError("No matching closing parens at: " + str(i))
                indexes_js[queue.pop()] = i

        if len(queue) > 0:
            raise IndexError("No matching opening parens at: " + str(queue.pop()))

        start_idx = 0
        while indexes_js.get(start_idx):
            vl = indexes_js[start_idx]
            pjs = js_str[start_idx:vl + 1]
            result.add(pjs)
            start_idx = vl + 1
    except Exception as err:
        logger.exception(err)

    return result


def create_colored_png(webhexcolor):
    from PIL import Image
    from io import BytesIO
    with Image.new("RGB", (100, 100), webhexcolor) as image:
        f = BytesIO()
        image.save(f, format='PNG')
        f.close()

    return image

