# app.py
import streamlit as st
import requests
import time
from datetime import datetime

API_URL = "http://127.0.0.1:8000/chat"
SESSION_ID = "default"

st.set_page_config(page_title="Weather Chatbot", page_icon="☁️")
st.title("Weather Chatbot")
st.write("Ask about the weather in any city! Your chat will be remembered during this session.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Main chat container (this will hold all messages)
chat_container = st.container()

# Input form at the bottom
with st.container():
    with st.form(key="chat_form", clear_on_submit=True):
        cols = st.columns([6, 1])
        with cols[0]:
            user_input = st.text_input("Type your message here:", key="input_text", label_visibility="collapsed")
        with cols[1]:
            submit_button = st.form_submit_button("➤")

# Handle submission
if submit_button and user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Show "thinking" message
    with chat_container:
        with st.chat_message("assistant"):
            st.write("Thinking...")
    
    # Call FastAPI
    try:
        response = requests.post(
            API_URL,
            params={"session_id": SESSION_ID, "use_context": "true"},
            json={"message": user_input},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        bot_reply = data.get("response", "Sorry, I couldn't get a response.")

        # Add weather details if available
        weather = data.get("weather_data")
        forecast = data.get("forecast_data")

        if weather:
            temp = weather['temperature']
            temp_min = weather.get('temp_min', temp)
            temp_max = weather.get('temp_max', temp)
            sunrise = weather.get('sunrise', 'N/A')
            sunset = weather.get('sunset', 'N/A')

            bot_reply += (
                f"\n\n**Current Weather:**\n"
                f"• City: {weather['city']}, {weather['country']}\n"
                f"• Temperature: {weather['temperature']}°C (Feels like {weather['feels_like']}°C)\n"
                f"• Condition: {weather['description'].title()} {'☀️' if 'clear' in weather['description'].lower() else '☁️' if 'cloud' in weather['description'].lower() else '🌧️' if 'rain' in weather['description'].lower() else '❄️'}\n"
                f"• Humidity: {weather['humidity']}%\n"
                f"• Wind: {weather['wind_speed']} m/s\n"
                f"• Temp Range: {temp_min}°C - {temp_max}°C\n"
                f".Sunrise: {sunrise} | Sunset:{sunset}"
                f".temp_min: {temp_min}°C | temp_max: {temp_max}°C\n"
            )

        if forecast:
            bot_reply += "\n\n**Forecast:**\n"
            for day in forecast["forecasts"][:5]:
                date_obj = datetime.strptime(day["date"], "%Y-%m-%d")
                pretty_date = date_obj.strftime("%b %d, %a")  # Apr 10, Thu

                sunrise = day.get("sunrise", "N/A")
                sunset = day.get("sunset", "N/A")

                bot_reply += (
                    f"• **{pretty_date}** → {day['temp_min']}°C - {day['temp_max']}°C, {day['description']}\n"
                    f"  ↳ Sunrise {sunrise} | Sunset {sunset}\n"
                ) 
    except Exception as e:
        bot_reply = f"Error: Could not connect to the server. {str(e)}"

    # Replace the "thinking" message with real reply
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    # Force rerun to update UI
    st.rerun()

# Display all messages in the chat container
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

# Auto-scroll to bottom after every update
st.markdown("""
<script>
    const chatContainer = window.parent.document.querySelector('.main');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
</script>
""", unsafe_allow_html=True)