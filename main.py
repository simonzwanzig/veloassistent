import os
import openrouteservice
import folium
from folium import Element
import json
import requests
import hashlib
from dotenv import load_dotenv

# ==========================
# KONFIGURATION
# ==========================
load_dotenv() 
ORS_API_KEY = os.getenv("ORS_API_KEY")
client = openrouteservice.Client(key=ORS_API_KEY)

# ==========================
# POI Mapping (zentral)
# ==========================
POI_MAPPING = {
    "water": {
        "label": "💧 Trinkwasser",
        "tag": ("amenity", "drinking_water"),
        "emoji": "💧"
    },
    "toilets": {
        "label": "🚻 Toiletten",
        "tag": ("amenity", "toilets"),
        "emoji": "🚻"
    },
    "cafe": {
        "label": "☕ Café",
        "tag": ("amenity", "cafe"),
        "emoji": "☕"
    },
    "bike_shop": {
        "label": "🚲 Fahrradladen",
        "tag": ("shop", "bicycle"),
        "emoji": "🚲"
    },
    "bakery": {
        "label": "🥐 Bäckerei",
        "tag": ("shop", "bakery"),
        "emoji": "🥐"
    },
    "air": {
        "label": "💨 Luftpumpe",
        "tag": ("amenity", "compressed_air"),
        "emoji": "💨"
    },
    "hostel": {
        "label": "🏠 Hostel",
        "tag": ("tourism", "hostel"),
        "emoji": "🏠"
    },
    "hut": {
        "label": "🛏️ Unterstand",
        "tag": ("amenity", "shelter"),
        "emoji": "🛏️"
    },
    "camping": {
        "label": "⛺ Campingplatz",
        "tag": ("tourism", "camp_site"),
        "emoji": "⛺"
    },
    "supermarket": {
        "label": "🛒 Supermarkt",
        "tag": ("shop", "supermarket"),
        "emoji": "🛒"
    },
    "atm": {
        "label": "🏧 Bank",
        "tag": ("amenity", "atm"),
        "emoji": "🏧"
    },
    "laundry": {
        "label": "🧺 Waschsalon",
        "tag": ("shop", "laundry"),
        "emoji": "🧺"
    },
    "graveyard": {
        "label": "💧 Friedhof",
        "tag": ("landuse", "cemetery"),
        "emoji": "💧"
    },
    "repair": {
        "label": "🛠️ Repairstation",
        "tag": ("amenity", "bicycle_repair_station"),
        "emoji": "🛠️"
    },
    "parking": {
        "label": "🅿️ Fahrradständer",
        "tag": ("amenity", "bicycle_parking"),
        "emoji": "🅿️"
    },
    "station": {
        "label": "🚉 Bahnhof",
        "tag": ("railway", "station"),
        "emoji": "🚉"
    }
}
# ==========================
# POI Backend State
# ==========================
LAST_ROUTE = None
POI_CACHE = {}

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter"
]

# ==========================
# ROUTING (OpenRouteService)
# ==========================

def find_bike_route(start_name, end_name, bike_type="standard"):

    profiles = {
        "standard": "cycling-regular",
        "road": "cycling-road",
        "mtb": "cycling-mountain",
        "ebike": "cycling-electric"
    }

    profile = profiles.get(bike_type, "cycling-regular")

    start = client.pelias_search(start_name)["features"][0]["geometry"]["coordinates"]
    end = client.pelias_search(end_name)["features"][0]["geometry"]["coordinates"]

    route = client.directions(
        coordinates=[start, end],
        profile=profile,
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
    global LAST_ROUTE
    LAST_ROUTE = [(p[1], p[0]) for p in coords]
    
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

def create_map(route, start, end, dist, dur, asc, desc, start_name, end_name, bike_type):

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
    
    # Grundlegende CSS
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
   
    # Box oben links für Eingabe
    ui_css = """
    <style>
    .ui-box {
        width: fit-content;
        max-width: none;
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
    .ui-box .primary-btn {
        width: 180px;
        display: block;
        margin-top: 14px;
        padding: 8px 10px;
        border-radius: 10px;
        border: none;
        background: #4a90e2;
        color: white;
        font-weight: 600;
        font-size: 13px;
        cursor: pointer;
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
    .ui-box select {
        width: 180px;
        padding: 6px 8px;
        border-radius: 8px;
        border: 1px solid #ddd;
        font-size: 13px;
        background: white;
    }

    .ui-box select:focus {
        outline: none;
        border-color: #4a90e2;
    }

    .leaflet-top.leaflet-left {
        pointer-events: none;
        width: auto !important;
    }


    .leaflet-top.leaflet-left .ui-box {
        pointer-events: auto;
    }

    .leaflet-control {
        background: transparent !important;
        box-shadow: none !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: auto !important;
    }

    .leaflet-control.leaflet-bar {
        min-width: 0 !important;
        width: auto !important;
    }
    .leaflet-control-layers {
        background: white !important;
        border-radius: 14px !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
        border: none !important;
        backdrop-filter: none !important;
        padding: 14px 16px !important;

        margin: 0 !important;
    }
    .leaflet-control-layers {
        padding: 14px !important;
        border-radius: 14px !important;
    }
    .leaflet-top.leaflet-right {
        top: 15px !important;
        right: 15px !important;
    }
    .leaflet-control-layers label {
        display: block;
        margin-bottom: 6px;
    }

    .leaflet-control-layers-overlays {
        max-height: none !important;
        overflow: visible !important;
    }
        </style>
    """
    m.get_root().html.add_child(folium.Element(ui_css))

    # Tausch-Button CSS
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

    # Autocomplete CSS
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

    # Markierungen Start / Ziel
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

    # POI-Layer (nur für UI)
    poi_layers = [
        "💧 Trinkwasser",
        "🚻 Toiletten",
        "☕ Café",
        "🚲 Fahrradladen",
        "🥐 Bäckerei",
        "💨 Luftpumpe",
        "🏠 Hostel",
        "🛏️ Unterstand",
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

    bike_labels = {
        "standard": "🚴 Standardrad",
        "road": "🏎️ Rennrad",
        "mtb": "🚵 MTB",
        "ebike": "⚡ E-Bike"
    }
    
    # Info-Box unten links
    info = f"""
    <div class="ui-box ui-fixed" style="bottom:20px; left:20px; z-index:9999;">
        <b>Fahrrad:</b> {bike_labels.get(bike_type, "🚴 Standardrad")}<br>
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
    
    # Eingabe-Formular
    form = f"""
    <form method="POST"
    class="ui-box ui-fixed"
    style="top:15px; left:15px; z-index:20000;">

    <h3>🚲 Route berechnen</h3>

    <label>Start</label><br>
    <div class="input-wrap">
        <input id="start" name="start" value="{start_name}"
               autocomplete="off" placeholder="Aachen">
        <div id="start-suggestions" class="suggestions"></div>
    </div>

    <div style="
        display:flex;
        justify-content:center;
        margin:10px 0;
    ">
        <button type="button" class="swap-btn" onclick="swap()">↕</button>
    </div>

    <label>Ziel</label><br>
    <div class="input-wrap">
        <input id="end" name="end" value="{end_name}"
               autocomplete="off" placeholder="Passau">
        <div id="end-suggestions" class="suggestions"></div>
    </div><br>

    <label>Fahrradtyp</label><br>
    <select name="bike_type" style="width:180px; margin-bottom:12px;">
        <option value="standard">🚴 Standardrad</option>
        <option value="road">🏎️ Rennrad</option>
        <option value="mtb">🚵 MTB</option>
        <option value="ebike">⚡ E-Bike</option>
    </select>

    <button type="submit" class="primary-btn">
        Route berechnen
    </button>
    </form>
    """
    m.get_root().html.add_child(Element(form))
    m.get_root().html.add_child(
        Element('<script src="/static/autocomplete.js"></script>')
    )
    folium.LayerControl(
        collapsed=False,
        hideSingleBase=True
    ).add_to(m)

    m.save("route.html")

# ==========================
# POIs serverseitig entlang Route
# ==========================
def get_pois_along_route(poi_type):

    if poi_type not in POI_MAPPING or not LAST_ROUTE:
        return []

    tag, value = POI_MAPPING[poi_type]["tag"]

    cache_key = hashlib.md5(
        (poi_type + json.dumps(LAST_ROUTE)).encode()
    ).hexdigest()

    if cache_key in POI_CACHE:
        return POI_CACHE[cache_key]

    # Route sampeln (alle ~500 m)
    points = LAST_ROUTE[::30]

    query = f"""
[out:json][timeout:60];
(
{chr(10).join(
    f'node(around:250,{lat},{lon})["{tag}"="{value}"];'
    for lat, lon in points
)}
);
out body 100;
    """

    for url in OVERPASS_SERVERS:
        try:
            r = requests.post(url, data=query, timeout=60)
            r.raise_for_status()
            data = r.json()

            pois = []
            for el in data.get("elements", []):
                if "lat" not in el:
                    continue
                tags = el.get("tags", {})
                pois.append({
                    "lat": el["lat"],
                    "lon": el["lon"],
                    "name": tags.get("name") or tags.get("brand"),
                    "street": tags.get("addr:street"),
                    "housenumber": tags.get("addr:housenumber"),
                    "city": tags.get("addr:city")
                })
            POI_CACHE[cache_key] = pois
            return pois

        except Exception as e:
            print("Overpass failed:", url, e)

    return []