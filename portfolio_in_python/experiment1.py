from flask import Flask, request

app = Flask(__name__)

@app.route("/callback")
def spotify_callback():
    code = request.args.get("code")
    return f"Authorization code: {code}"
