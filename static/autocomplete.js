// Funktion zum Aktivieren der Autovervollständigung
function enableAutocomplete(inputId, boxId) {
    const input = document.getElementById(inputId);
    const box = document.getElementById(boxId);
    const ORS_API_KEY = document.body.dataset.orsKey;

    let timeout = null;
        
    input.addEventListener("input", () => {
        clearTimeout(timeout);
        const q = input.value;

        if (q.length < 3) {
            box.innerHTML = "";
            return;
        }

        timeout = setTimeout(async () => {
            const url =
                "https://api.openrouteservice.org/geocode/autocomplete"
                + "?text=" + encodeURIComponent(q)
                + "&api_key=" + ORS_API_KEY
                + "&size=5";

            const res = await fetch(url);
            const data = await res.json();

            box.innerHTML = "";

            data.features.forEach(f => {
                const div = document.createElement("div");
                div.className = "suggestion";
                div.textContent = f.properties.label;
                div.onclick = () => {
                    input.value = f.properties.label;
                    box.innerHTML = "";
                };
                box.appendChild(div);
            });
        }, 300);
    });
}

// Initialisieren
document.addEventListener("DOMContentLoaded", () => {
    enableAutocomplete("start", "start-suggestions");
    enableAutocomplete("end", "end-suggestions");
});

// Funktion zum Vertauschen der Start- und Endpunkte
function swap() {
    const s = document.getElementById("start");
    const e = document.getElementById("end");
    [s.value, e.value] = [e.value, s.value];
}
