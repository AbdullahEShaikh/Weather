import requests
import folium
import webbrowser
import time

# Define region (Eastern U.S.)
min_lat, max_lat = 35.0, 38.0
min_lon, max_lon = -83.0, -78.0
lat_step = 1.0
lon_step = 1.0

weather_map = folium.Map(location=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2], zoom_start=6)

# ----------- GRIDPOINT WEATHER DATA (NWS - Public Domain) -----------
for lat in range(int(min_lat * 10), int(max_lat * 10 + 1), int(lat_step * 10)):
    for lon in range(int(min_lon * 10), int(max_lon * 10 + 1), int(lon_step * 10)):
        lat_f = lat / 10.0
        lon_f = lon / 10.0

        try:
            point_url = f"https://api.weather.gov/points/{lat_f},{lon_f}"
            point_resp = requests.get(point_url, timeout=10)
            if point_resp.status_code != 200:
                continue
            point_data = point_resp.json()

            office = point_data["properties"]["gridId"]
            grid_x = point_data["properties"]["gridX"]
            grid_y = point_data["properties"]["gridY"]

            grid_url = f"https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}"
            grid_resp = requests.get(grid_url, timeout=10)
            grid_data = grid_resp.json()

            props = grid_data.get("properties", {})
            temperature = props.get("temperature", {}).get("values", [{}])[0].get("value", "N/A")
            cloud_cover = props.get("cloudAmount", {}).get("values", [{}])[0].get("value", "N/A")
            humidity = props.get("relativeHumidity", {}).get("values", [{}])[0].get("value", "N/A")

            popup = (
                f"<b>({lat_f}, {lon_f})</b><br>"
                f"🌡 Temp: {temperature} °F<br>"
                f"☁️ Clouds: {cloud_cover}%<br>"
                f"💧 Humidity: {humidity}%"
            )

            folium.Marker(
                location=[lat_f, lon_f],
                popup=folium.Popup(popup, max_width=300),
                icon=folium.Icon(color="blue", icon="cloud")
            ).add_to(weather_map)

            print(f"✔️ Added point ({lat_f}, {lon_f})")
            time.sleep(1.2)

        except Exception as e:
            print(f"⚠️ Error at ({lat_f}, {lon_f}): {e}")

# ----------- ALERT POLYGONS (NWS - Public Domain) -----------
try:
    alert_url = "https://api.weather.gov/alerts/active"
    alert_resp = requests.get(alert_url, timeout=15)
    alerts = alert_resp.json().get("features", [])

    for alert in alerts:
        props = alert.get("properties", {})
        geometry = alert.get("geometry")

        if geometry and geometry["type"] == "Polygon":
            coords = geometry["coordinates"][0]
            latlon_coords = [[lat, lon] for lon, lat in coords]

            alert_type = props.get("event", "Alert")
            severity = props.get("severity", "Unknown")
            area = props.get("areaDesc", "N/A")

            folium.Polygon(
                locations=latlon_coords,
                color="darkred" if severity == "Severe" else "orange",
                fill=True,
                fill_opacity=0.5,
                popup=folium.Popup(
                    f"<b>{alert_type}</b><br>Severity: {severity}<br>Area: {area}",
                    max_width=300
                )
            ).add_to(weather_map)

    print(f"✔️ {len(alerts)} alerts added")

except Exception as e:
    print(f"⚠️ Failed to fetch alerts: {e}")

# ----------- EXPORT HTML -----------
filename = "nws_commercial_weather_map.html"
weather_map.save(filename)
webbrowser.open(filename)
