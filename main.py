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
        elevation=True,
        options={
            "avoid_features": avoid
        }
    )

    feature = routes["features"][0]
    geometry = feature["geometry"]["coordinates"]
    segments = feature["properties"]["segments"]

    distance = sum(seg["distance"] for seg in segments)
    duration = sum(seg["duration"] for seg in segments)
    ascent = sum(seg.get("ascent", 0) for seg in segments)
    descent = sum(seg.get("descent", 0) for seg in segments)

    print(f"✓ Länge: {distance/1000:.2f} km")
    print(f"✓ Dauer: {duration/60:.1f} Minuten")
    print(f"✓ Höhenmeter: +{ascent:.0f} m / -{descent:.0f} m")

    return geometry, start_coords, end_coords, distance, duration, ascent, descent


# ===================== KARTE MIT LEGENDE =====================
def create_map(route, start, end, distance, duration, ascent, descent, filename="route.html"):
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

    # ✅ KORREKT: funktioniert mit Höhenwerten
    folium.PolyLine(
        [(p[1], p[0]) for p in route],
        weight=6,
        color="blue"
    ).add_to(m)

    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        z-index: 9999;
        background: white;
        padding: 12px 14px;
        border-radius: 10px;
        box-shadow: 0 0 12px rgba(0,0,0,0.3);
        font-size: 14px;
        line-height: 1.4;
    ">
        <b>🚴 Fahrradrouten-Info</b><br><br>
        📏 Strecke: <b>{distance/1000:.2f} km</b><br>
        ⏱️ Dauer: <b>{duration/60:.1f} min</b><br>
        ⛰️ Aufstieg: <b>{ascent:.0f} m</b><br>
        ⬇️ Abstieg: <b>{descent:.0f} m</b>
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))
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

    route, start_coords, end_coords, dist, dur, asc, desc = find_bike_route(
        start_name=start,
        end_name=end,
        bike_type=bike_type,
        avoid_highways=avoid_highways,
        avoid_steep_hills=avoid_hills
    )

    create_map(route, start_coords, end_coords, dist, dur, asc, desc)
