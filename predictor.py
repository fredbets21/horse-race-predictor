import time
import re
from bs4 import BeautifulSoup
import requests
import os


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
        
        # Add a small delay to mimic human behavior
        time.sleep(1)
        
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise
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
    main