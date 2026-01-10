document.addEventListener("DOMContentLoaded", function () {

    // Leaflet-Map von Folium finden
    const map = Object.values(window).find(v => v instanceof L.Map);
    if (!map) {
        console.error("Leaflet map not found");
        return;
    }

    // Route kommt aus Python
    const route = ROUTE_DATA;

    const loadedLayers = {};

    function overpassQueryAlongRoute(route, radius, tag, value) {

        const points = route
            .filter((_, i) => i % 10 === 0) // ca. alle ~200 m
            .map(p =>
                `node(around:${radius},${p[0]},${p[1]})["${tag}"="${value}"];`
            )
            .join("\n");

        return `
[out:json][timeout:45];
(
${points}
);
out body;
        `;
    }

    map.on("overlayadd", function (e) {

        const name = e.name;
        if (loadedLayers[name]) return;
        loadedLayers[name] = true;

        let tag = null;
        let value = null;

        if (name === "💧 Trinkwasser") { tag = "amenity"; value = "drinking_water"; }
        if (name === "🚻 Toiletten") { tag = "amenity"; value = "toilets"; }
        if (name === "☕ Café") { tag = "amenity"; value = "cafe"; }
        if (name === "🚲 Fahrradladen") { tag = "shop"; value = "bicycle"; }
        if (name === "🥐 Bäckerei") { tag = "shop"; value = "bakery"; }
        if (name === "💨 Luftpumpe") { tag = "amenity"; value = "compressed_air"; }
        if (name === "🏠 Hostel") { tag = "tourism"; value = "hostel"; }
        if (name === "🛏️ Schutzhütte") { tag = "tourism"; value = "wilderness_hut"; }
        if (name === "🏕️ Campingplatz") { tag = "tourism"; value = "camp_site"; }
        if (name === "🛒 Supermarkt") { tag = "shop"; value = "supermarket"; }
        if (name === "🏧 Bank") { tag = "amenity"; value = "atm"; }
        if (name === "🧺 Waschsalon") { tag = "shop"; value = "laundry"; }
        if (name === "💧 Friedhof") { tag = "amenity"; value = "graveyard"; }
        if (name === "🛠️ Repairstation") { tag = "amenity"; value = "bicycle_repair_station"; }
        if (name === "🅿️ Fahrradständer") { tag = "amenity"; value = "bicycle_parking"; }
        if (name === "🚉 Bahnhof") { tag = "railway"; value = "station"; }

        if (!tag) return;

        fetch("https://overpass-api.de/api/interpreter", {
            method: "POST",
            headers: { "Content-Type": "text/plain" },
            body: overpassQueryAlongRoute(route, 250, tag, value)
        })
        .then(r => r.json())
        .then(data => {
            data.elements.forEach(el => {
                if (!el.lat || !el.lon) return;

                L.marker([el.lat, el.lon], {
                    icon: L.divIcon({
                        html: `<div style="font-size:20px">${name.split(" ")[0]}</div>`,
                        className: "",
                        iconSize: [24, 24]
                    })
                })
                .addTo(e.layer)
                .bindPopup(`<b>${name}</b>`);
            });
        })
        .catch(err => console.error("Overpass error:", err));
    });
});
