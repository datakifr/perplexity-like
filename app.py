import streamlit as st
import requests
import json
import time
import threading
import csv
import os

# ----------------------------------------------------
# CONFIGURATION: file paths for CSV/TXT data
# ----------------------------------------------------
COUNTRIES_CSV = "countries.csv"
LANGUAGES_CSV = "languages.csv"
GOOGLE_DOMAINS_TXT = "google_domains.txt"
DEVICES_TXT = "devices.txt"

# ----------------------------------------------------
# DATA LOADING FUNCTIONS
# ----------------------------------------------------
def load_csv_data(csv_path):
    """
    Reads a CSV file with 'code' and 'name' columns.
    Returns a list of dictionaries, e.g.:
    [ {'code': 'us', 'name': 'United States'}, ... ].
    """
    items = []
    if not os.path.exists(csv_path):
        return items
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'code' in row and 'name' in row:
                items.append({
                    'code': row['code'].strip(),
                    'name': row['name'].strip()
                })
    return items

def load_list_from_txt(file_path):
    """
    Reads a .txt file, one value per line.
    Returns a list of strings.
    """
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

# Wrapper functions to load specific data
def get_countries():
    return load_csv_data(COUNTRIES_CSV)

def get_languages():
    return load_csv_data(LANGUAGES_CSV)

def get_google_domains():
    return load_list_from_txt(GOOGLE_DOMAINS_TXT)

def get_devices():
    return load_list_from_txt(DEVICES_TXT)

# ----------------------------------------------------
# SECRETS (configured in Streamlit)
# ----------------------------------------------------
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]
AUTH_TOKEN = st.secrets["AUTH_TOKEN"]

st.set_page_config(page_title="Perplexity-Like Search", page_icon="🔍", layout="wide")
st.title("Perplexity-Like Search")

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Options")
    st.subheader("Settings")
    
    # Model selection
    model_options = {
        "Auto (Let System Decide)": "auto",
        "GPT4o (Standard)": "gpt-4o",
        "GPT4o-mini (Cost-Effective)": "gpt-4o-mini",
        "o1 (Advanced Reasoning)": "o1-preview",
        "o1-mini (Advanced Reasoning, Cost-Effective)": "o1-mini"
    }
    selected_model_label = st.selectbox("Select model", list(model_options.keys()), index=0)
    model = model_options[selected_model_label]
    model_selection_type = "auto" if model == "auto" else "manual"

    st.markdown("---")
    
    # Country selection (CSV file with code and name)
    countries_data = get_countries()
    selected_country = st.selectbox(
        "Country",
        countries_data,
        format_func=lambda item: f"{item['name']} - {item['code']}"
    )
    country_code = selected_country['code'] if selected_country else None

    # Language selection (CSV file with code and name)
    languages_data = get_languages()
    selected_language = st.selectbox(
        "Language",
        languages_data,
        format_func=lambda item: f"{item['name']} - {item['code']}"
    )
    language_code = selected_language['code'] if selected_language else None

    # Google Domain selection (TXT file)
    domain = st.selectbox("Google Domain", get_google_domains())

    # Device selection (TXT file)
    device = st.selectbox("Device", get_devices())

    # Numeric input
    num = st.number_input("Num (choose a number)", min_value=1, value=10)

    st.markdown("---")
    st.write("🔍 **Perplexity-Like Search** v1.0")

# Main query input
query = st.text_input("Enter your query:", placeholder="E.g., What is the best workflow automation software?")

def perform_request(payload, headers):
    """
    Sends a POST request to the N8N webhook endpoint with the given payload.
    """
    return requests.post(N8N_WEBHOOK_URL, json=payload, headers=headers)

if st.button("Search"):
    if query:
        headers = {
            "Authorization": f"{AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        # Only codes (country, language) will be sent to the webhook
        payload = {
            "query": query,
            "model": model,
            "model_selection_type": model_selection_type,
            "domain": domain,
            "country": country_code,
            "language": language_code,
            "device": device,
            "num": num
        }

        status_placeholder = st.empty()
        progress_placeholder = st.empty()

        response_data = {"resp": None}

        def request_thread():
            r = perform_request(payload, headers)
            response_data["resp"] = r

        t = threading.Thread(target=request_thread)
        t.start()

        # Example loading messages displayed in rotation
        loading_messages = [
            "Connecting to knowledge base... (Hope the neuron WiFi is working 🤖)",
            "Analyzing your query... (Using a very serious magnifying glass 🔍)",
            "Gathering relevant information... (Or at least, whatever isn’t pure imagination 🤯)",
            "Building the best answer... (With bricks of knowledge and a sprinkle of magic ✨)",
            "Consulting the AI oracle... (It said, 'Don’t believe everything on the internet' 👀)",
            "Loading... (If this takes too long, blame LLM-Latency ⚛️)",
            "Thinking... (One moment while I consult my robotic crystal ball 🔮)",
            "Crunching data... (And probably overthinking it 🤔)",
            "Fetching knowledge... (Hope it’s not stuck in traffic 🚗💨)",
            "Compiling the perfect answer... (Or at least a pretty decent one 😅)"
        ]

        i = 0
        while t.is_alive():
            status_placeholder.markdown(f"**{loading_messages[i % len(loading_messages)]}**")
            progress_placeholder.progress((i % 100) / 100)
            time.sleep(3)
            i += 1

        t.join()
        status_placeholder.empty()
        progress_placeholder.empty()

        if response_data["resp"] is not None:
            response = response_data["resp"]
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        data = data[0]

                    sources = data.get("sources", [])
                    if sources:
                        st.subheader("📚 Sources")
                        sources_html = """
                        <style>
                        .source-box {
                            background-color: #f8faff;
                            padding: 15px;
                            border-radius: 10px;
                            margin-bottom: 20px;
                        }
                        .source-item {
                            font-size: 16px;
                            margin-bottom: 5px;
                        }
                        </style>
                        <div class='source-box'>
                        """
                        for source in sources:
                            title = source.get("title", "Source")
                            link = source.get("link", "#")
                            sources_html += f"<p class='source-item'>✅ <a href='{link}' target='_blank'>{title}</a></p>"
                        sources_html += "</div>"
                        st.markdown(sources_html, unsafe_allow_html=True)

                    response_text = data.get("response", "No response available")
                    st.subheader("📃 Search Results")
                    st.markdown(response_text)

                except json.JSONDecodeError:
                    st.error("Unable to decode JSON response.")
                    st.text(response.text)
            else:
                st.error(f"Error {response.status_code}: Unable to fetch data.")
        else:
            st.error("No response received from the thread.")
    else:
        st.warning("Please enter a query before searching.")
