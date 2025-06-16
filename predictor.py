import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def extract_win_percent_from_jockey_tooltip(hpop0_html):
    soup = BeautifulSoup(hpop0_html, "html.parser")
    text = soup.get_text(" ", strip=True)
    match = re.search(r'\d+\s+wins\s+in\s+\d+\s+runs\s*\((\d{1,3})%\)', text)
    return int(match.group(1)) if match else 0


def from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

def launch_browser_get_html(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # These two lines are needed for Streamlit Cloud:
    chrome_options.binary_location = "/usr/bin/google-chrome"
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    driver.get(url)
    driver.implicitly_wait(5)
    html = driver.page_source
    driver.quit()
    return html



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
            horse["trainer_win_pct"] = 0  # Not available

            # Jockey
            jockey_tag = row.find("a", href=re.compile("/jockey/"))
            jockey_name = jockey_tag.get_text(strip=True) if jockey_tag else "Unknown"
            jockey_data = jockey_tag.get("data-hpop0", "") if jockey_tag else ""
            horse["jockey"] = jockey_name
            horse["jockey_win_pct"] = extract_win_percent_from_jockey_tooltip(jockey_data)

            # Odds (display only)
            odds_tag = row.find("span", class_="bkprice")
            horse["odds"] = odds_tag.get_text(strip=True) if odds_tag else "N/A"

            horses.append(horse)

        except Exception as e:
            print(f"⚠️ Skipping horse due to error: {e}")
            continue

    return horses


def score_horse(h):
    score = 0

    # Form scoring
    score += h["form"].count("1") * 5
    score += h["form"].count("2") * 3
    score += h["form"].count("3") * 2

    # CD win
    score += h["cd_win"] * 3

    # Rating
    score += h["rating"] / 10

    # Jockey (light weight)
    score += h["jockey_win_pct"] * 0.25

    return score


def main():
    url = input("🔗 Enter IrishRacing racecard URL: ").strip()
    html = launch_browser_get_html(url)
    horses = parse_racecard(html)

    if not horses:
        print("❌ No horses found.")
        return

    for horse in horses:
        horse["score"] = score_horse(horse)

    ranked = sorted(horses, key=lambda x: x["score"], reverse=True)

    print("\n🏇 Predicted Order:")
    for i, h in enumerate(ranked, 1):
        print(f"{i}. {h['name']} - Score: {h['score']:.1f} | "
              f"Form: {h['form']} | CD Win: {'Yes' if h['cd_win'] else 'No'} | "
              f"Rating: {h['rating']} | Jockey: {h['jockey']} ({h['jockey_win_pct']}%) | "
              f"Odds: {h['odds']}")

    print(f"\n🥇 Most Likely Winner: {ranked[0]['name']}")


if __name__ == "__main__":
    main()



























