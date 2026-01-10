import os
import openrouteservice
import folium
from folium import Element
import json
from dotenv import load_dotenv

# ==========================
# KONFIGURATION
# ==========================
load_dotenv() 
ORS_API_KEY = os.getenv("ORS_API_KEY")
client = openrouteservice.Client(key=ORS_API_KEY)
# ==========================
# ROUTING (OpenRouteService)
# ==========================

def find_bike_route(start_name, end_name):


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

def create_map(route, start, end, dist, dur, asc, desc, start_name, end_name):

    # lon,lat → lat,lon
    route_latlon = [(p[1], p[0]) for p in route]

    m = folium.Map(
    location=[start[1], start[0]],
    zoom_start=13,
    zoom_control=False   # ← + / - weg
    )

    m.get_root().html.add_child(
    Element(f"""
    <script>
        document.addEventListener("DOMContentLoaded", () => {{
            document.body.dataset.orsKey = "{ORS_API_KEY}";
        }});
    </script>
    """)
    )

    base_css = """
    <style>
    html, body {
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
    }

    .leaflet-container {
        width: 100%;
        height: 100%;
    }
    </style>
    """
    m.get_root().html.add_child(Element(base_css))
    ui_css = """
    <style>

    .ui-box {
        background: white;
        border-radius: 14px;
        padding: 14px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 14px;
        color: #222;
    }
    .ui-fixed {
        position: fixed;
    }
    .ui-box h3 {
        margin: 0 0 10px 0;
        font-size: 15px;
    }

    .ui-box input {
        width: 180px;
        padding: 6px 8px;
        border-radius: 8px;
        border: 1px solid #ddd;
        font-size: 13px;
    }

    .ui-box input:focus {
        outline: none;
        border-color: #4a90e2;
    }

    .ui-box button {
        margin-top: 6px;
        padding: 6px 10px;
        border-radius: 8px;
        border: none;
        background: #4a90e2;
        color: white;
        cursor: pointer;
        font-size: 13px;
    }

    .ui-box button.secondary {
        background: #eee;
        color: #333;
    }

    .ui-box button:hover {
        opacity: 0.9;
    }
    .ui-box {
        backdrop-filter: blur(6px);
    }
    </style>
    """
    m.get_root().html.add_child(folium.Element(ui_css))
    swap_css = """
    <style>
    .swap-btn {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        border: none;
        background: #f0f0f0;
        color: #4a90e2;
        font-size: 18px;
        cursor: pointer;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }
    .swap-btn:hover {
        background: #e0e0e0;
    }
    </style>
    """
    m.get_root().html.add_child(Element(swap_css))
    autocomplete_css = """
    <style>
    .suggestions {
        position: absolute;
        top: 100%;
        left: 0;
        width: 100%;

        background: white;
        border-radius: 10px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.15);
        margin-top: 4px;
        z-index: 30000;
        overflow: hidden;
    }
    .suggestion {
        padding: 6px 10px;
        cursor: pointer;
        font-size: 13px;
    }
    .suggestion:hover {
        background: #f0f0f0;
    }
    .input-wrap {
    position: relative;
    width: 180px;
    }
    </style>
    """
    m.get_root().html.add_child(Element(autocomplete_css))

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
    <div class="ui-box ui-fixed" style="bottom:20px; left:20px; z-index:9999;">
        <b>Distanz:</b> {dist/1000:.2f} km<br>
        <b>Dauer:</b> {dur/60:.1f} min<br>
        <b>Aufstieg:</b> {asc:.0f} m<br>
        <b>Abstieg:</b> {desc:.0f} m
    </div>
    """
    m.get_root().html.add_child(Element(info))

    m.get_root().html.add_child(
    Element(f"<script>const ROUTE_DATA = {json.dumps(route_latlon)};</script>")
    )
    m.get_root().html.add_child(
        Element('<script src="/static/pois.js"></script>')
    )
    form = f"""
    <form method="POST"
      class="ui-box ui-fixed"
      style="top:15px; left:15px; z-index:20000; display:inline-block;">

    <h3>🚲 Route berechnen</h3>

    <label>Start</label><br>
    <div class="input-wrap">
        <input id="start" name="start" value="{start_name}"
               autocomplete="off" placeholder="Aachen">
        <div id="start-suggestions" class="suggestions"></div>
    </div>

    <div style="text-align:center; margin:8px 0;">
        <button type="button" class="swap-btn" onclick="swap()">↕</button>
    </div>

    <label>Ziel</label><br>
    <div class="input-wrap">
        <input id="end" name="end" value="{end_name}"
               autocomplete="off" placeholder="Passau">
        <div id="end-suggestions" class="suggestions"></div>
    </div><br>

    <button type="submit">Route berechnen</button>
    </form>
    """
    m.get_root().html.add_child(Element(form))
    m.get_root().html.add_child(
        Element('<script src="/static/autocomplete.js"></script>')
    )
    folium.LayerControl(collapsed=False).add_to(m)


    m.save("route.html")