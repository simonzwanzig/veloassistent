document.addEventListener("DOMContentLoaded", function () {

    // ==========================
    // Leaflet-Map finden
    // ==========================
    const map = Object.values(window).find(v => v instanceof L.Map);
    if (!map) {
        console.error("Leaflet map not found");
        return;
    }

    // ==========================
    // Client-Cache
    // ==========================
    const poiCache = {};

    // ==========================
    // Progress UI
    // ==========================
    const style = document.createElement("style");
    style.innerHTML = `
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
    document.head.appendChild(style);

    let progressBox = null;

    function showProgress(title) {
        progressBox = document.createElement("div");
        progressBox.className = "poi-progress";
        progressBox.innerHTML = `
            <div style="margin-bottom:8px;text-align:center">${title}</div>
            <div class="poi-progress-bar">
                <div class="poi-progress-fill" id="poi-progress-fill"></div>
            </div>
        `;
        document.body.appendChild(progressBox);
    }

    function updateProgress(p) {
        const el = document.getElementById("poi-progress-fill");
        if (el) el.style.width = p + "%";
    }

    function hideProgress() {
        if (progressBox) progressBox.remove();
        progressBox = null;
    }

    // ==========================
    // Emoji-Pin
    // ==========================
    function emojiPin(emoji) {
        return L.divIcon({
            className: "emoji-pin",
            html: `
                <div style="
                    width:28px;height:28px;
                    background:white;
                    border-radius:50%;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:16px">
                    ${emoji}
                </div>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 28]
        });
    }

    // ==========================
    // Layer → POI-Type Mapping
    // ==========================
    const LAYER_TO_TYPE = {
        "💧 Trinkwasser": "water",
        "🚻 Toiletten": "toilets",
        "☕ Café": "cafe",
        "🚲 Fahrradladen": "bike_shop",
        "🥐 Bäckerei": "bakery",
        "💨 Luftpumpe": "air",
        "🏠 Hostel": "hostel",
        "🛏️ Schutzhütte": "hut",
        "⛺ Campingplatz": "camping",
        "🛒 Supermarkt": "supermarket",
        "🏧 Bank": "atm",
        "🧺 Waschsalon": "laundry",
        "💧 Friedhof": "graveyard",
        "🛠️ Repairstation": "repair",
        "🅿️ Fahrradständer": "parking",
        "🚉 Bahnhof": "station"
    };

    // ==========================
    // POIs laden
    // ==========================
    map.on("overlayadd", function (e) {

        const type = LAYER_TO_TYPE[e.name];
        if (!type) return;

        // Cache → sofort anzeigen
        if (poiCache[type]) {
            poiCache[type].forEach(m => m.addTo(e.layer));
            return;
        }

        showProgress(`${e.name} werden geladen …`);

        fetch(`/pois?type=${type}`)
            .then(r => r.json())
            .then(data => {

                const markers = [];
                const total = data.pois.length || 1;
                let done = 0;

                data.pois.forEach(p => {
                    if (!p.lat || !p.lon) return;

                    let address = "";
                    if (p.street) {
                        address = `<br>${p.street} ${p.housenumber || ""}`;
                    }
                    if (p.city) {
                        address += `<br>${p.city}`;
                    }

                    const popup = `
                        ${e.name.split(" ")[0]} <b>${p.name || e.name.slice(2)}</b>
                        ${address}
                    `;

                    const m = L.marker(
                        [p.lat, p.lon],
                        { icon: emojiPin(e.name.split(" ")[0]) }
                    )
                    .bindTooltip(p.name || e.name.slice(2))
                    .bindPopup(popup);

                    // ✅ HIER war der Fehler
                    m.addTo(e.layer);
                    markers.push(m);

                    done++;
                    updateProgress(Math.round(done / total * 100));
                });

                poiCache[type] = markers;
                setTimeout(hideProgress, 300);
            })
            .catch(err => {
                hideProgress();
                console.error("POI error:", err);
            });
    });
});