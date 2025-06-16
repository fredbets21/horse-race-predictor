import time
import re
from bs4 import BeautifulSoup
import requests
import streamlit as st

def extract_win_percent_from_jockey_tooltip(hpop0_html):
    soup = BeautifulSoup(hpop0_html, "html.parser")
    text = soup.get_text(" ", strip=True)
    match = re.search(r'\d+\s+wins\s+in\s+\d+\s+runs\s*\((\d{1,3})%\)', text)
    return int(match.group(1)) if match else 0

def launch_browser_get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        time.sleep(1)  # mimic human behavior
        return response.text
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {e}")
    finally:
        session.close()

def parse_racecard(html):
    soup = BeautifulSoup(html, "html.parser")
    horse_rows = soup.find_all("div", class_="runner-line")
    horses = []

    for row in horse_rows:
        try:
            horse = {}

            # Horse name
            name_tag = row.find("a", class_="runner")
            horse["name"] = name_tag.get_text(strip=True)

            # Form
            form_tag = row.find("div", class_="form")
            horse["form"] = form_tag.text.strip() if form_tag else ""

            # CD win
            horse["cd_win"] = 1 if row.select_one("span.cdwin") else 0

            # Rating
            rating_tag = row.find("span", string=re.compile("Rated"))
            horse["rating"] = int(rating_tag.text.strip().replace("Rated", "").strip()) if rating_tag else 0

            # Trainer
            trainer_tag = row.find("a", href=re.compile("/trainer/"))
            horse["trainer"] = trainer_tag.get_text(strip=True) if trainer_tag else "Unknown"
            horse["trainer_win_pct"] = 0  # Optional: Can be implemented later

            # Jockey
            jockey_tag = row.find("a", href=re.compile("/jockey/"))
            jockey_name = jockey_tag.get_text(strip=True) if jockey_tag else "Unknown"
            jockey_data = jockey_tag.get("data-hpop0", "") if jockey_tag else ""
            horse["jockey"] = jockey_name
            horse["jockey_win_pct"] = extract_win_percent_from_jockey_tooltip(jockey_data)

            # Odds
            odds_tag = row.find("span", class_="bkprice")
            horse["odds"] = odds_tag.get_text(strip=True) if odds_tag else "N/A"

            horses.append(horse)

        except Exception as e:
            st.warning(f"⚠️ Skipping a horse due to error: {e}")
            continue

    return horses

def score_horse(h):
    score = 0
    score += h["form"].count("1") * 5
    score += h["form"].count("2") * 3
    score += h["form"].count("3") * 2
    score += h["cd_win"] * 3
    score += h["rating"] / 10
    score += h["jockey_win_pct"] * 0.25
    return score

# === STREAMLIT UI ===
st.set_page_config(page_title="Horse Race Predictor", layout="wide")
st.title("🏇 Horse Race Predictor")
st.markdown("Enter an IrishRacing.com **racecard URL** to predict the finishing order based on form, rating, CD wins, jockey win % and show the odds.")

url = st.text_input("🔗 Paste IrishRacing racecard URL (e.g., https://www.irishracing.com/card?race=...):")

if url:
    with st.spinner("🔍 Scraping race data..."):
        try:
            html = launch_browser_get_html(url)
            horses = parse_racecard(html)

            if not horses:
                st.error("❌ No horses found. Please check the URL.")
            else:
                for horse in horses:
                    horse["score"] = score_horse(horse)

                ranked = sorted(horses, key=lambda x: x["score"], reverse=True)

                st.success(f"✅ Prediction complete. {len(ranked)} horses found.")
                st.subheader("🏁 Predicted Finishing Order:")

                for i, h in enumerate(ranked, 1):
                    st.markdown(f"""
                    ### {i}. {h['name']}
                    - **Score**: {h['score']:.1f}
                    - **Form**: `{h['form']}`
                    - **Course/Distance Win**: {'✅' if h['cd_win'] else '❌'}
                    - **Rating**: {h['rating']}
                    - **Jockey**: {h['jockey']} ({h['jockey_win_pct']}%)
                    - **Odds**: `{h['odds']}`
                    """)

                st.markdown(f"---\n## 🥇 Most Likely Winner: **{ranked[0]['name']}**")

        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")

