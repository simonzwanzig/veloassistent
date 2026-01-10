from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, send_file, make_response
from main import find_bike_route, create_map

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    start = request.form.get("start", "Aachen")
    end = request.form.get("end", "Maastricht")

    route, s, e, d, t, a, de = find_bike_route(start, end)
    create_map(route, s, e, d, t, a, de, start, end)

    return send_file("route.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(debug=True)