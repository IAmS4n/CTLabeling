import base64
import hashlib
import hmac
import json
from io import BytesIO

from PIL import Image
from flask import current_app


def int_key_json_load(x):
    tmp = json.loads(x)
    if type(tmp) is list:
        return tmp
    elif type(tmp) is dict:
        return {int(key): val for key, val in tmp.items()}
    else:
        raise


def encode(img):
    img = Image.fromarray(img, "L")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    myimage = buffer.getvalue()
    org = "data:image/png;base64," + base64.b64encode(myimage).decode("utf-8", "ignore")

    buffer = BytesIO()
    img.thumbnail((32, 32), Image.ANTIALIAS)
    img.save(buffer, format="JPEG")
    myimage = buffer.getvalue()
    thumbnail = "data:image/jpeg;base64," + base64.b64encode(myimage).decode(
        "utf-8", "ignore"
    )

    return org, thumbnail


def zhmac(pid, z):
    key = hashlib.sha224(current_app.config["SECRET_KEY"]).digest()
    assert key is not None

    digest_maker = hmac.new(key, b"%d_%d" % (pid, z), hashlib.md5)

    return digest_maker.hexdigest()
