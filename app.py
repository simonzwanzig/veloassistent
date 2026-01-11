from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, send_file, jsonify
from main import find_bike_route, create_map, get_pois_along_route

app = Flask(__name__)

# ==========================
# Hauptseite
# ==========================
@app.route("/", methods=["GET", "POST"])
def index():
    start = request.form.get("start", "Aachen")
    end = request.form.get("end", "Maastricht")
    bike_type = request.form.get("bike_type", "standard")

    route, s, e, d, t, a, de = find_bike_route(start, end, bike_type)
    create_map(route, s, e, d, t, a, de, start, end, bike_type)

    response = send_file("route.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ==========================
# POI API
# ==========================
@app.route("/pois")
def pois():
    poi_type = request.args.get("type")

    if not poi_type:
        return jsonify({"error": "missing type"}), 400

    pois = get_pois_along_route(poi_type)

    return jsonify({
        "type": poi_type,
        "count": len(pois),
        "pois": pois
    })


if __name__ == "__main__":
    app.run(debug=True)
