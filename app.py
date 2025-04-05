import streamlit as st
import time
import math
import folium
from streamlit_folium import st_folium
import base64

# Must be first Streamlit command
st.set_page_config(page_title="Smart Traffic Light Advisor", layout="centered")

st.title("🚗 Smart Traffic Light Advisor for Chandigarh")
st.write("Simulating car movement and upcoming signal prediction with ETA.")

# Dummy car route (lat, lon) — you can expand this
route = [
    (30.7412, 76.7824),  # Start near Sector 17
    (30.7400, 76.7800),
    (30.7385, 76.7780),
    (30.7370, 76.7760),
    (30.7360, 76.7750),  # Near Sector 22/23
]

# Dummy traffic light data
traffic_lights = [
    {
        "name": "Sector 17/22 Intersection",
        "location": (30.7390, 76.7780),
        "cycle": {"green": 30, "red": 30},
        "start_time": 0,
    },
    {
        "name": "Sector 22/23 Intersection",
        "location": (30.7360, 76.7750),
        "cycle": {"green": 40, "red": 20},
        "start_time": 15,
    }
]

# Simulated car speed (in km/h)
car_speed_kmph = st.slider("Select car speed (km/h)", 10, 60, 30)
car_speed_mps = car_speed_kmph * 1000 / 3600  # convert to m/s

# Initialize session state
if "position" not in st.session_state:
    st.session_state.position = 0
    st.session_state.start_time = time.time()

# Haversine distance function (in meters)
def haversine(coord1, coord2):
    R = 6371000  # Earth radius in m
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Get current car position
car_location = route[st.session_state.position]

# Map UI
m = folium.Map(location=car_location, zoom_start=15)
folium.Marker(car_location, tooltip="🚗 Your Car", icon=folium.Icon(color="blue")).add_to(m)

# Add traffic lights to map
for tl in traffic_lights:
    folium.Marker(tl["location"], tooltip=tl["name"], icon=folium.Icon(color="red")).add_to(m)

# Find nearest traffic light
def find_next_traffic_light():
    closest = None
    min_distance = float("inf")
    for tl in traffic_lights:
        dist = haversine(car_location, tl["location"])
        if dist < min_distance:
            min_distance = dist
            closest = tl
    return closest, min_distance

next_light, distance_to_light = find_next_traffic_light()
eta = distance_to_light / car_speed_mps

# Compute phase
def get_signal_phase(tl, now):
    total = tl["cycle"]["green"] + tl["cycle"]["red"]
    elapsed = (now - tl["start_time"]) % total
    if elapsed < tl["cycle"]["red"]:
        return "🔴 RED", tl["cycle"]["red"] - elapsed
    else:
        return "🟢 GREEN", total - elapsed

current_time = time.time() - st.session_state.start_time
phase, time_remaining = get_signal_phase(next_light, current_time)

# Speak helper
def speak(text):
    js_code = f'''
        <script>
        var msg = new SpeechSynthesisUtterance("{text}");
        window.speechSynthesis.speak(msg);
        </script>
    '''
    st.components.v1.html(js_code)

# Show info
st.markdown(f"### 📍 Current Location: `{car_location}`")
st.markdown(f"### 🚦 Next Signal: **{next_light['name']}**")
st.markdown(f"### 🧭 Distance: **{distance_to_light:.1f} meters**")
st.markdown(f"### ⏱ ETA: **{eta:.1f} seconds**")
st.markdown(f"### 💡 Signal Phase: **{phase} ({time_remaining:.0f}s left)**")

# Voice announcement
speak(f"Upcoming traffic light: {next_light['name']}. Signal is {phase.split()[1]}. {time_remaining:.0f} seconds remaining.")

# Show map
st_folium(m, width=700, height=500)

# Next button
if st.button("Next Step (Move Forward)"):
    if st.session_state.position < len(route) - 1:
        st.session_state.position += 1
    else:
        st.session_state.position = 0
