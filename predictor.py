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


def comprehensive_odds_search(row, horse_name, debug=True):
    """
    Comprehensive odds extraction with detailed logging
    """
    if debug:
        print(f"\n=== DEBUGGING ODDS FOR: {horse_name} ===")
    
    # Get all text content to see what's available
    all_text = row.get_text(" ", strip=True)
    if debug:
        print(f"Full row text: {all_text}")
    
    # Method 1: Check all elements with potential odds patterns
    all_elements = row.find_all(['span', 'div', 'td', 'a'])
    odds_candidates = []
    
    for elem in all_elements:
        text = elem.get_text(strip=True)
        classes = elem.get('class', [])
        elem_id = elem.get('id', '')
        
        # Look for common odds patterns
        odds_patterns = [
            r'^\d+/\d+$',          # 3/1, 5/2
            r'^\d+-\d+$',          # 5-2
            r'^\d+\.\d+$',         # 2.50
            r'^evens?$',           # evens
            r'^fav$',              # fav
            r'^\d+/\d+F$',         # 3/1F (favorite)
            r'^\d+\.\d+F$',        # 2.50F
        ]
        
        for pattern in odds_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                odds_candidates.append({
                    'text': text,
                    'classes': classes,
                    'id': elem_id,
                    'tag': elem.name,
                    'pattern': pattern
                })
                if debug:
                    print(f"ODDS CANDIDATE: '{text}' | Classes: {classes} | ID: {elem_id} | Tag: {elem.name}")
    
    # Method 2: Look for elements with odds-related class names
    odds_class_patterns = [
        'bkprice', 'odds', 'price', 'bk-price', 'bookmaker-price', 
        'betting-odds', 'runner-odds', 'decimal', 'fractional',
        'best-odds', 'current-odds', 'live-odds'
    ]
    
    for pattern in odds_class_patterns:
        elements = row.find_all(class_=re.compile(pattern, re.I))
        for elem in elements:
            text = elem.get_text(strip=True)
            if text:
                odds_candidates.append({
                    'text': text,
                    'classes': elem.get('class', []),
                    'id': elem.get('id', ''),
                    'tag': elem.name,
                    'method': f'class_pattern_{pattern}'
                })
                if debug:
                    print(f"CLASS MATCH ({pattern}): '{text}' | Classes: {elem.get('class', [])}")
    
    # Method 3: Look for data attributes
    data_attrs = ['data-odds', 'data-price', 'data-bk-price', 'data-decimal', 'data-fractional']
    for attr in data_attrs:
        elements = row.find_all(attrs={attr: True})
        for elem in elements:
            value = elem.get(attr)
            if value:
                odds_candidates.append({
                    'text': value,
                    'classes': elem.get('class', []),
                    'id': elem.get('id', ''),
                    'tag': elem.name,
                    'method': f'data_attr_{attr}'
                })
                if debug:
                    print(f"DATA ATTR ({attr}): '{value}'")
    
    # Method 4: Look for specific IDs that might contain odds
    id_patterns = ['odds', 'price', 'bk']
    for pattern in id_patterns:
        elements = row.find_all(id=re.compile(pattern, re.I))
        for elem in elements:
            text = elem.get_text(strip=True)
            if text:
                odds_candidates.append({
                    'text': text,
                    'classes': elem.get('class', []),
                    'id': elem.get('id', ''),
                    'tag': elem.name,
                    'method': f'id_pattern_{pattern}'
                })
                if debug:
                    print(f"ID MATCH ({pattern}): '{text}' | ID: {elem.get('id', '')}")
    
    if debug:
        print(f"Total odds candidates found: {len(odds_candidates)}")
        if not odds_candidates:
            print("❌ NO ODDS CANDIDATES FOUND")
            print("Dumping all spans and divs:")
            for elem in row.find_all(['span', 'div']):
                text = elem.get_text(strip=True)
                if text and len(text) < 30:  # Only short text likely to be odds
                    print(f"  {elem.name}: '{text}' | Classes: {elem.get('class', [])} | ID: {elem.get('id', '')}")
    
    # Return the best candidate
    if odds_candidates:
        # Prefer candidates that match common odds patterns
        pattern_matches = [c for c in odds_candidates if 'pattern' in c]
        if pattern_matches:
            return pattern_matches[0]['text']
        else:
            return odds_candidates[0]['text']
    
    return "N/A"


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


def parse_racecard(html, debug_mode=False):
    soup = BeautifulSoup(html, "html.parser")
    
    # Try different possible selectors for horse rows
    possible_selectors = [
        "div.runner-line",
        "tr.runner",
        "div.runner",
        ".horse-row",
        ".runner-row",
        "tbody tr",
        "[class*='runner']",
        "[class*='horse']"
    ]
    
    horse_rows = []
    for selector in possible_selectors:
        try:
            rows = soup.select(selector)
            if rows:
                print(f"✅ Found {len(rows)} rows using selector: {selector}")
                horse_rows = rows
                break
        except:
            continue
    
    if not horse_rows:
        print("❌ No horse rows found with any selector")
        # Let's see what's actually in the HTML
        print("Available div classes:")
        divs = soup.find_all('div', class_=True)
        for div in divs[:20]:  # First 20 divs
            classes = ' '.join(div.get('class', []))
            if classes:
                print(f"  div.{classes}")
        return []
    
    horses = []
    debug_count = 0

    for row in horse_rows:
        try:
            horse = {}

            # Horse name - try multiple selectors
            name_selectors = ["a.runner", ".horse-name", ".runner-name", "a[href*='horse']"]
            name_tag = None
            for selector in name_selectors:
                name_tag = row.select_one(selector)
                if name_tag:
                    break
            
            horse["name"] = name_tag.get_text(strip=True) if name_tag else f"Horse_{len(horses)+1}"

            # Form
            form_tag = row.find("div", class_="form")
            if not form_tag:
                form_tag = row.find(class_=re.compile("form", re.I))
            horse["form"] = form_tag.text.strip() if form_tag else ""

            # CD win
            horse["cd_win"] = 1 if row.select_one("span.cdwin") else 0

            # Rating
            rating_tag = row.find("span", string=re.compile("Rated"))
            horse["rating"] = int(rating_tag.text.strip().replace("Rated", "").strip()) if rating_tag else 0

            # Trainer
            trainer_tag = row.find("a", href=re.compile("/trainer/"))
            horse["trainer"] = trainer_tag.get_text(strip=True) if trainer_tag else "Unknown"
            horse["trainer_win_pct"] = 0

            # Jockey
            jockey_tag = row.find("a", href=re.compile("/jockey/"))
            jockey_name = jockey_tag.get_text(strip=True) if jockey_tag else "Unknown"
            jockey_data = jockey_tag.get("data-hpop0", "") if jockey_tag else ""
            horse["jockey"] = jockey_name
            horse["jockey_win_pct"] = extract_win_percent_from_jockey_tooltip(jockey_data)

            # Odds - comprehensive search with debug for first few horses
            debug_this_horse = debug_mode and debug_count < 3
            horse["odds"] = comprehensive_odds_search(row, horse["name"], debug_this_horse)
            if debug_this_horse:
                debug_count += 1

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


def save_debug_html(html, filename="debug_racecard.html"):
    """Save HTML to file for manual inspection"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Debug HTML saved to {filename}")


def main():
    url = input("🔗 Enter IrishRacing racecard URL: ").strip()
    
    # Always enable debug mode for troubleshooting
    debug_mode = True
    
    print("🔍 Fetching HTML...")
    html = launch_browser_get_html(url)
    
    print("💾 Saving debug HTML...")
    save_debug_html(html)
    
    print("🔍 Parsing racecard...")
    horses = parse_racecard(html, debug_mode)

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
    
    # Show odds extraction summary
    odds_found = sum(1 for h in horses if h['odds'] != 'N/A')
    print(f"\n📊 Odds found for {odds_found}/{len(horses)} horses")
    
    if odds_found == 0:
        print("\n🚨 NO ODDS FOUND FOR ANY HORSES!")
        print("Check the debug output above and the saved HTML file.")


if __name__ == "__main__":
    main()
