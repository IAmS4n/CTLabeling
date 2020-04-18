import base64
from io import BytesIO

from PIL import Image


def np2b64(x):
    img = Image.fromarray(x, 'L')
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    myimage = buffer.getvalue()
    org = "data:image/jpeg;base64," + base64.b64encode(myimage).decode('utf-8', 'ignore')

    buffer = BytesIO()
    img.thumbnail((32, 32), Image.ANTIALIAS)
    img.save(buffer, format="JPEG")
    myimage = buffer.getvalue()
    thumbnail = "data:image/jpeg;base64," + base64.b64encode(myimage).decode('utf-8', 'ignore')

    return org, thumbnail
