from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import emit, join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Silahkan Input Nama", code=code, name=name)

        if join != False and not code:
            return render_template("home.html", error="Silahkan Input Kode Room", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    name = session.get("name")
    room = session.get("room")

    if not name or not room or room not in rooms:
        return redirect(url_for("home"))

    messages = rooms[room]["messages"]
    return render_template("room.html", name=name, code=room, messages=messages)

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return

    if room not in rooms:
        leave_room(room)
        return

    join_room(room)

    # Tambahkan nama ke daftar pengguna online di room
    if "users" not in rooms[room]:
        rooms[room]["users"] = []

    if name not in rooms[room]["users"]:
        rooms[room]["users"].append(name)

    rooms[room]["members"] += 1
    send({"name": name, "message": "Telah Memasuki Ruangan"}, to=room)
    emit("update_users", rooms[room]["users"], to=room)

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    if room in rooms and name in rooms[room]["users"]:
        rooms[room]["users"].remove(name)
        rooms[room]["members"] -= 1
        send({"name": name, "message": "Telah Meninggalkan Ruangan"}, to=room)
        emit("update_users", rooms[room]["users"], to=room)

# if __name__ == "__main__":
#     socketio.run(app, host="0.0.0.0", port=5000)
if __name__ == "__main__":
    socketio.run(app, debug=True)