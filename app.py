from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, send_file, make_response
from main import find_bike_route, create_map

app = Flask(__name__)

#Flask request handler
@app.route("/", methods=["GET", "POST"])
def index():
    start = request.form.get("start", "Aachen")
    end = request.form.get("end", "Maastricht")

    bike_type = request.form.get("bike_type", "standard")

    route, s, e, d, t, a, de = find_bike_route(start, end, bike_type)
    create_map(route, s, e, d, t, a, de, start, end, bike_type)
    return send_file("route.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(debug=True)