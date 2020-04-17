import base64
from io import BytesIO

import numpy as np
from PIL import Image
from flask import Flask
from flask import render_template, request, redirect, url_for

app = Flask(__name__)


def np2b64(x):
    img = Image.fromarray(x, 'RGB')
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    myimage = buffer.getvalue()
    return "data:image/jpeg;base64," + base64.b64encode(myimage).decode('utf-8', 'ignore')


def get_role(user=None, password=None):
    if user is None and password is None:
        user = request.cookies.get('user')
        password = request.cookies.get('pass')
    if user == "1" and password == "1":
        return 1
    elif user == "2" and password == "2":
        return 2
    else:
        return -1


@app.route('/patient<pid>', methods=['GET', 'POST'])
def show_panel(pid):
    pid = int(pid)
    role = get_role()
    if 0 > role:
        return redirect(url_for('show_login'))

    if request.method == 'POST':
        pass
        # save

    slices = []
    for z in range(5):
        s = np.random.random((128, 128, 3))
        slices.append({"z": z, "img": np2b64(s)})

    if role == 1:
        role_name = "Student"
    elif role == 2:
        role_name = "Professor"
    else:
        role_name = "Unknown"
    return render_template('panel.html', slices=slices, pid=pid, ppid=pid - 1, npid=pid + 1, role_name=role_name)


@app.route('/list')
def show_list():
    role = get_role()

    if 0 > role:
        return redirect(url_for('show_login'))

    plist = list(range(100))
    return render_template('list.html', plist=plist)


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def show_login():
    if request.method == 'POST':
        if 0 < get_role(request.form['user'], request.form['pass']):
            resp = redirect(url_for('show_list'))
            # resp = make_response("Ok")
            resp.set_cookie('user', request.form['user'])
            resp.set_cookie('pass', request.form['pass'])
            return resp

    return render_template('login.html')


if __name__ == '__main__':
    app.run()
