# Der Veloassistent

Ein webbasierter Fahrradrouten-Planer mit **OpenRouteService** und **Folium**  
Die Anwendung berechnet Fahrradrouten zwischen zwei Orten und zeigt **relevante POIs entlang der Strecke** wie z.B. Supermärkte, Reperaturstationen, Trinkwasser und Schlafplätze

---

## Features

- 🚴 Fahrradrouting mit OpenRouteService
- 🗺️ Interaktive Karte (Folium)
- 🧭 Start- & Zielsuche mit Autocomplete
- 📏 Anzeige von:
  - Distanz
  - Dauer
  - Höhenmeter (Auf- & Abstieg)
- 🧩 POI-Layer entlang der Route:
  - 💧 Trinkwasser
  - 🚻 Toiletten
  - ☕ Café
  - 🏠 Hostel
  - 🚲 Fahrradladen
  - 🥐 Bäckerei
  - 💨 Luftpumpe
  - 🏠 Hostel
  - 🛏️ Schutzhütte
  - 🏕️ Campingplatz
  - 🛒 Supermarkt
  - 🏧 Bank
  - 🧺 Waschsalon
  - 💧 Friedhof
  - 🛠️ Repairstation
  - 🅿️ Fahrradständer
  - 🚉 Bahnhof
- 📍 POIs werden **nur bei aktivem Layer** geladen (Overpass API)
- 🎨 Modernes UI
- 🖥️ Lokaler Flask-Server

## Im Hintergrund

- **Python 3.9+**
- **Flask**
- **Folium / Leaflet**
- **OpenRouteService API**
- **Overpass API (OpenStreetMap)**
- **JavaScript (Fetch, Leaflet)**
- **HTML / CSS**

## Projektstruktur
```
veloassistant/
├── app.py               Flask Server
├── main.py              Routing + Kartenerstellung
├── route.html           Generierte Karte (automatisch)
├── requirements.txt
├── .env
├── static/
│ ├── pois.js            POIs via Overpass API
│ └── autocomplete.js    Autocomplete für Start & Ziel
└── README.md
```
## Voraussetzungen

### OpenRouteService API-Key
1. Registrieren bei  
   https://openrouteservice.org/
2. API-Key erstellen
3. `.env` Datei anlegen:

```env
ORS_API_KEY=DEIN_API_KEY_HIER
```
## Installation

**Repository klonen**
```
git clone https://github.com/simonzwanzig/veloassistent.git
cd veloassistent
```
**Abhängigkeiten installieren**
```
pip install -r requirements.txt
```

## Starten
```
python app.py
```
**Danach im Browser öffnen:**

http://127.0.0.1:5000
