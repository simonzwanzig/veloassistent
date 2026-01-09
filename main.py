import openrouteservice
from openrouteservice import convert
import folium

# ================== API KEY ==================
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjRlYmE4MmQyY2YzMzRiM2Q4ZTMzODhhNTIzOTkzNmRjIiwiaCI6Im11cm11cjY0In0="

client = openrouteservice.Client(key=ORS_API_KEY)

# ================== Geocoding ==================
def geocode_place(name):
    result = client.pelias_search(text=name)
    if not result["features"]:
        raise ValueError(f"Ort nicht gefunden: {name}")

    coords = result["features"][0]["geometry"]["coordinates"]
    address = result["features"][0]["properties"].get("label", name)

    # ORS: (lon, lat)
    return coords, address


# ================== Routing ==================
def find_route_ors(start_name, end_name, profile="driving-car"):
    print(f"Route: {start_name} → {end_name}")

    start_coords, start_addr = geocode_place(start_name)
    end_coords, end_addr = geocode_place(end_name)

    print("Start:", start_addr)
    print("Ziel :", end_addr)

    routes = client.directions(
        coordinates=[start_coords, end_coords],
        profile=profile,
        format="geojson"
    )

    route_geom = routes["features"][0]["geometry"]["coordinates"]
    summary = routes["features"][0]["properties"]["summary"]

    distance_km = summary["distance"] / 1000
    duration_min = summary["duration"] / 60

    print(f"✓ Länge: {distance_km:.2f} km")
    print(f"✓ Dauer: {duration_min:.1f} Minuten")

    return route_geom, start_coords, end_coords


# ================== Visualisierung ==================
def plot_route(route, start, end):
    m = folium.Map(location=[start[1], start[0]], zoom_start=13)

    folium.Marker(
        location=[start[1], start[0]],
        popup="Start",
        icon=folium.Icon(color="green")
    ).add_to(m)

    folium.Marker(
        location=[end[1], end[0]],
        popup="Ziel",
        icon=folium.Icon(color="red")
    ).add_to(m)

    folium.PolyLine(
        locations=[(lat, lon) for lon, lat in route],
        color="red",
        weight=6
    ).add_to(m)

    return m


# ================== MAIN ==================
if __name__ == "__main__":
    print("=" * 60)
    print("  OpenRouteService Routenplaner")
    print("=" * 60)

    start = input("Startpunkt (Enter = Karlsruher Schloss): ").strip()
    if not start:
        start = "Karlsruher Schloss"

    end = input("Zielpunkt (Enter = Hbf Karlsruhe): ").strip()
    if not end:
        end = "Hauptbahnhof Karlsruhe"

    print("[1] Auto  [2] Zu Fuß  [3] Fahrrad")
    choice = input("Verkehrsmittel (1–3, Enter = Auto): ").strip()

    profile_map = {
        "1": "driving-car",
        "2": "foot-walking",
        "3": "cycling-regular"
    }
    profile = profile_map.get(choice, "driving-car")

    route, start_coords, end_coords = find_route_ors(
        start, end, profile
    )

    map_ = plot_route(route, start_coords, end_coords)
    map_.save("route.html")

    print("\n✓ Karte gespeichert als route.html")
    print("✓ Im Browser öffnen")
