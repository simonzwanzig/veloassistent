document.addEventListener("DOMContentLoaded", function () { 
    // ==========================
    // Overpass Fallback Server
    // ==========================
    const OVERPASS_SERVERS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter"
    ];

    // ==========================
    // POI Cache
    // ==========================
    const poiCache = {};

    // ==========================    
    // POI Namen anzeigen
    // ==========================

    function getPoiName(tags, fallback) {
        return (
            tags.name ||
            tags.brand ||
            fallback
        );
    }

    function poiPopup(icon, name, tags) {
        let addr = "";
        if (tags["addr:street"]) {
            addr = `<br>${tags["addr:street"]} ${tags["addr:housenumber"] || ""}`;
        }
        return `${icon} <b>${name}</b>${addr}`;
    }
    // ==========================
    // Leaflet-Map von Folium finden
    // ==========================
    const map = Object.values(window).find(v => v instanceof L.Map);
    if (!map) {
        console.error("Leaflet map not found");
        return;
    }

    // ==========================
    // Progress UI
    // ==========================
    const progressStyle = document.createElement("style");
    progressStyle.innerHTML = `
    .poi-progress {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 260px;
        background: white;
        border-radius: 14px;
        padding: 14px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.25);
        z-index: 40000;
        font-family: system-ui, sans-serif;
        font-size: 13px;
    }
    .poi-progress-title {
        margin-bottom: 8px;
        text-align: center;
    }
    .poi-progress-bar {
        width: 100%;
        height: 10px;
        background: #eee;
        border-radius: 8px;
        overflow: hidden;
    }
    .poi-progress-fill {
        height: 100%;
        width: 0%;
        background: #4a90e2;
        transition: width 0.2s ease;
    }
    `;
    document.head.appendChild(progressStyle);

    let progressBox = null;

    function showProgress(title) {
        progressBox = document.createElement("div");
        progressBox.className = "poi-progress";
        progressBox.innerHTML = `
            <div class="poi-progress-title">${title}</div>
            <div class="poi-progress-bar">
                <div class="poi-progress-fill" id="poi-progress-fill"></div>
            </div>
        `;
        document.body.appendChild(progressBox);
    }

    function updateProgress(percent) {
        const fill = document.getElementById("poi-progress-fill");
        if (fill) fill.style.width = percent + "%";
    }

    function hideProgress() {
        if (progressBox) progressBox.remove();
        progressBox = null;
    }
    const route = ROUTE_DATA;

    const loadedLayers = {};
    
    // ==========================
    // Overpass mit Fallback
    // ==========================
    async function fetchOverpassWithFallback(query) {

        for (const url of OVERPASS_SERVERS) {
            try {
                const controller = new AbortController();
                const timeout = setTimeout(() => controller.abort(), 15000);

                const res = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "text/plain" },
                    body: query,
                    signal: controller.signal
                });

                clearTimeout(timeout);

                if (!res.ok) throw new Error(res.status);

                return await res.json();
            }
            catch (err) {
                console.warn("Overpass failed:", url, err.message);
            }
        }

        throw new Error("Alle Overpass-Server fehlgeschlagen");
    }
    // ==========================
    // CSS: weiße Emoji-Stecknadel
    // ==========================
    const style = document.createElement("style");
    style.innerHTML = `
    .emoji-pin {
        background: none;
        border: none;
    }

    .emoji-pin .pin {
        position: relative;
        width: 28px;
        height: 40px;
    }

    .emoji-pin .pin-circle {
        width: 28px;
        height: 28px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px; 
        line-height: 1;
    }

    .emoji-pin .pin-tip {
        position: absolute;
        left: 50%;
        top: 26px;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 10px solid white;
    }
    `;
    document.head.appendChild(style);

    // ==========================
    // Emoji-Pin Icon
    // ==========================
    function emojiPin(emoji) {
        return L.divIcon({
            className: "emoji-pin",
            html: `
                <div class="pin">
                    <div class="pin-circle">${emoji}</div>
                    <div class="pin-tip"></div>
                </div>
            `,
            iconSize: [28, 40],
            iconAnchor: [14, 40],
            popupAnchor: [0, -34]
        });
    }

    // ==========================
    // Overpass-Query entlang Route
    // ==========================
    function overpassQueryAlongRoute(route, radius, tag, value) {

        const points = route.filter((_, i) => i % 30 === 0);

        return {
            total: points.length,
            query: `
    [out:json][timeout:45];
    (
    ${points.map(p =>
        `node(around:${radius},${p[0]},${p[1]})["${tag}"="${value}"];`
    ).join("\n")}
    );
    out body 200;
            `
        };
    }    

    // ==========================
    // POIs laden beim Aktivieren eines Layers
    // ==========================
    map.on("overlayadd", function (e) {

        const name = e.name;
        const cacheKey = name + JSON.stringify(route);

        // ==========================
        // Cache vorhanden → sofort anzeigen
        // ==========================
        if (poiCache[cacheKey]) {
            poiCache[cacheKey].forEach(m => m.addTo(e.layer));
            return;
        }

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

        // ==========================
        // Overpass laden + Progress
        // ==========================
        const q = overpassQueryAlongRoute(route, 250, tag, value);

        showProgress(`${name} werden geladen …`);

        fetchOverpassWithFallback(q.query)
        .then(data => {

            const markers = [];
            const total = data.elements.length || 1;
            let done = 0;

            data.elements.forEach(el => {
                if (!el.lat || !el.lon) return;

                const tags = el.tags || {};
                const poiName = getPoiName(tags, name.slice(2));

                const marker = L.marker(
                    [el.lat, el.lon],
                    { icon: emojiPin(name.split(" ")[0]) }
                )
                .bindTooltip(poiName)
                .bindPopup(poiPopup(
                    name.split(" ")[0],
                    poiName,
                    tags
                ));

                marker.addTo(e.layer);
                markers.push(marker);

                done++;
                updateProgress(Math.round(done / total * 100));
            });

            poiCache[cacheKey] = markers;

            setTimeout(hideProgress, 300);
        })
        .catch(err => {
            hideProgress();
            console.error("Overpass error:", err);
        });
    });
});