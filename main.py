import openrouteservice
import folium
import os

# ===================== API KEY =====================
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjRlYmE4MmQyY2YzMzRiM2Q4ZTMzODhhNTIzOTkzNmRjIiwiaCI6Im11cm11cjY0In0="
client = openrouteservice.Client(key=ORS_API_KEY)


# ===================== GEOCODING =====================
def geocode_place(name: str):
    result = client.pelias_search(text=name)
    if not result["features"]:
        raise ValueError(f"Ort nicht gefunden: {name}")

    feature = result["features"][0]
    coords = feature["geometry"]["coordinates"]  # (lon, lat)
    label = feature["properties"].get("label", name)

    return coords, label


# ===================== FAHRRAD ROUTING =====================
def find_bike_route(
    start_name: str,
    end_name: str,
    bike_type: str = "regular",
    avoid_highways: bool = True,
    avoid_steep_hills: bool = False
):
    profile_map = {
        "regular": "cycling-regular",
        "road": "cycling-road",
        "mtb": "cycling-mountain",
        "ebike": "cycling-electric"
    }

    profile = profile_map.get(bike_type, "cycling-regular")

    start_coords, start_label = geocode_place(start_name)
    end_coords, end_label = geocode_place(end_name)

    print("Start:", start_label)
    print("Ziel :", end_label)
    print("Profil:", profile)

    avoid = []
    if avoid_highways:
        avoid.append("highways")
    if avoid_steep_hills:
        avoid.append("steep_hills")

    routes = client.directions(
        coordinates=[start_coords, end_coords],
        profile=profile,
        format="geojson",
        options={
            "avoid_features": avoid
        }
    )

    feature = routes["features"][0]
    geometry = feature["geometry"]["coordinates"]

    segments = feature["properties"]["segments"]
    distance = sum(seg["distance"] for seg in segments)
    duration = sum(seg["duration"] for seg in segments)

    print(f"✓ Länge: {distance / 1000:.2f} km")
    print(f"✓ Dauer: {duration / 60:.1f} Minuten")

    return geometry, start_coords, end_coords, distance, duration


# ===================== KARTE =====================
def create_map(route, start, end, distance, duration, filename="route.html"):
    m = folium.Map(location=[start[1], start[0]], zoom_start=13)

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

    folium.PolyLine(
        [(lat, lon) for lon, lat in route],
        weight=6,
        color="blue"
    ).add_to(m)

    folium.map.Marker(
        [start[1], start[0]],
        icon=folium.DivIcon(
            html=f"""
            <div style="font-size: 14px; background: white; padding: 6px;
                        border-radius: 6px; border: 1px solid gray;">
            🚴 {distance/1000:.2f} km<br>
            ⏱️ {duration/60:.1f} min
            </div>
            """
        )
    ).add_to(m)

    m.save(filename)
    print(f"✓ Karte gespeichert: {os.path.abspath(filename)}")


# ===================== AUTOMATISCHER START =====================
if __name__ == "__main__":
    print("=" * 60)
    print(" OpenRouteService Fahrrad-Routenplaner")
    print("=" * 60)

    start = input("Startpunkt (Enter = Karlsruher Schloss): ").strip()
    if not start:
        start = "Karlsruher Schloss"

    end = input("Zielpunkt (Enter = Hbf Karlsruhe): ").strip()
    if not end:
        end = "Hauptbahnhof Karlsruhe"

    print("\nFahrradtyp:")
    print("[1] Normal")
    print("[2] Rennrad")
    print("[3] Mountainbike")
    print("[4] E-Bike")

    choice = input("Wählen (1–4, Enter = Normal): ").strip()
    bike_type = {
        "1": "regular",
        "2": "road",
        "3": "mtb",
        "4": "ebike"
    }.get(choice, "regular")

    avoid_highways = input("Hauptstraßen meiden? (j/n, Enter = ja): ").strip().lower()
    avoid_highways = avoid_highways != "n"

    avoid_hills = input("Starke Steigungen meiden? (j/n, Enter = nein): ").strip().lower()
    avoid_hills = avoid_hills == "j"

    print("\nBerechne Route...\n")

    route, start_coords, end_coords, dist, dur = find_bike_route(
        start_name=start,
        end_name=end,
        bike_type=bike_type,
        avoid_highways=avoid_highways,
        avoid_steep_hills=avoid_hills
    )

    create_map(route, start_coords, end_coords, dist, dur)
