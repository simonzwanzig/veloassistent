import os
import openrouteservice
import folium
from folium import Element
import json


# ==========================
# KONFIGURATION
# ==========================

ORS_API_KEY = os.getenv("ORS_API_KEY")

# ==========================
# ROUTING (OpenRouteService)
# ==========================

def find_bike_route(start_name, end_name):
    client = openrouteservice.Client(key=ORS_API_KEY)

    start = client.pelias_search(start_name)["features"][0]["geometry"]["coordinates"]
    end = client.pelias_search(end_name)["features"][0]["geometry"]["coordinates"]

    route = client.directions(
        coordinates=[start, end],
        profile="cycling-regular",
        format="geojson",
        elevation=True
    )

    feature = route["features"][0]
    coords = feature["geometry"]["coordinates"]
    summary = feature["properties"]["summary"]
    ascent = feature["properties"]["ascent"]
    descent = feature["properties"]["descent"]

    print(f"✓ Distanz: {summary['distance']/1000:.2f} km")
    print(f"✓ Dauer: {summary['duration']/60:.1f} min")
    print(f"✓ Aufstieg: {ascent:.0f} m | Abstieg: {descent:.0f} m")

    return (
        coords,
        start,
        end,
        summary["distance"],
        summary["duration"],
        ascent,
        descent
    )


# ==========================
# KARTE (Folium)
# ==========================

def create_map(route, start, end, dist, dur, asc, desc):

    # lon,lat → lat,lon
    route_latlon = [(p[1], p[0]) for p in route]

    m = folium.Map(location=[start[1], start[0]], zoom_start=13)

    folium.PolyLine(
    route_latlon,
    weight=6,
    color="blue"
    ).add_to(m)

    folium.Marker(
        [start[1], start[0]],
        popup="Start",
        icon=folium.Icon(color="green", icon="bicycle", prefix="fa")
    ).add_to(m)

    folium.Marker(
        [end[1], end[0]],
        popup="Ziel",
        icon=folium.Icon(color="red", icon="flag", prefix="fa")
    ).add_to(m)

    # POI-Layer (leer!)

    poi_layers = [
        "💧 Trinkwasser",
        "🚻 Toiletten",
        "☕ Café",
        "🚲 Fahrradladen",
        "🥐 Bäckerei",
        "💨 Luftpumpe",
        "🏠 Hostel",
        "🛏️ Schutzhütte",
        "⛺ Campingplatz",
        "🛒 Supermarkt",
        "🏧 Bank",
        "🧺 Waschsalon",
        "💧 Friedhof",
        "🛠️ Repairstation",
        "🅿️ Fahrradständer",
        "🚉 Bahnhof"
    ]

    poi_groups = {}
    for name in poi_layers:
        fg = folium.FeatureGroup(name=name, show=False)
        fg.add_to(m)
        poi_groups[name] = fg

    # Info-Box
    info = f"""
    <div style="
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 9999;
        background: white;
        padding: 10px;
        border: 2px solid grey;
        font-size: 14px;">
        <b>Distanz:</b> {dist/1000:.2f} km<br>
        <b>Dauer:</b> {dur/60:.1f} min<br>
        <b>Aufstieg:</b> {asc:.0f} m<br>
        <b>Abstieg:</b> {desc:.0f} m
    </div>
    """
    m.get_root().html.add_child(folium.Element(info))
    m.get_root().html.add_child(
    Element(f"<script>const ROUTE_DATA = {json.dumps(route_latlon)};</script>")
    )
    m.get_root().html.add_child(
        Element('<script src="/static/pois.js"></script>')
    )
    form = """
    <form method="POST"
    style="
    position:fixed;
    top:10px;
    left:10px;
    z-index:20000;
    background:white;
    padding:10px;
    border:2px solid grey;
    box-shadow:2px 2px 6px rgba(0,0,0,0.3);
    ">
    <b>🚲 Route berechnen</b><br><br>

    Start:<br>
    <input id="start" name="start" placeholder="Aachen"><br><br>

    Ziel:<br>
    <input id="end" name="end" placeholder="Maastricht"><br><br>

    <button type="button" onclick="swap()">↔ Tauschen</button>
    <button type="submit">Route berechnen</button>
    </form>

    <script>
    function swap() {
    const s = document.getElementById("start");
    const e = document.getElementById("end");
    const tmp = s.value;
    s.value = e.value;
    e.value = tmp;
    }
    </script>
    """

    folium.LayerControl(collapsed=False).add_to(m)

    m.get_root().html.add_child(folium.Element(form))

    m.save("route.html")