import json
import urllib.request
import re
from pathlib import Path

# Lokacija izlazne datoteke (src/data/leaders.json)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_FILE = PROJECT_ROOT / "src" / "data" / "leaders.json"

# Kombinirani izvori podataka (GitHub dataset + OPTCG API)
SOURCES = [
    {
        "name": "Punk-Records GitHub Dataset",
        "url": "https://raw.githubusercontent.com/buhbbl/punk-records/main/english/index/cards_by_id.json"
    },
    {
        "name": "OPTCG API (Setovi)",
        "url": "https://optcgapi.com/api/allSetCards/"
    },
    {
        "name": "OPTCG API (Starter Deckovi)",
        "url": "https://optcgapi.com/api/allSTCards/"
    }
]

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode('utf-8'))

def extract_cards_list(raw_data):
    """Pretvara bilo koji format API odziva (listu ili rječnik) u jedinstvenu listu karata."""
    if isinstance(raw_data, list):
        return raw_data
    elif isinstance(raw_data, dict):
        if "results" in raw_data and isinstance(raw_data["results"], list):
            return raw_data["results"]
        elif "cards" in raw_data and isinstance(raw_data["cards"], list):
            return raw_data["cards"]
        elif "data" in raw_data and isinstance(raw_data["data"], list):
            return raw_data["data"]
        else:
            cards = []
            for k, v in raw_data.items():
                if isinstance(v, dict):
                    card_obj = dict(v)
                    if "id" not in card_obj and "card_number" not in card_obj:
                        card_obj["id"] = k
                    cards.append(card_obj)
            return cards
    return []

def main():
    all_cards = []
    
    print("Dohvaćam podatke s izvora...")
    for src in SOURCES:
        try:
            raw_data = fetch_json(src["url"])
            cards = extract_cards_list(raw_data)
            if cards:
                all_cards.extend(cards)
                print(f" -> Uspješno: {src['name']} ({len(cards)} karata loaded)")
        except Exception as e:
            print(f" -> Preskočeno ({src['name']}): {e}")

    if not all_cards:
        print("\nGreška: Niti jedan izvor nije vratio podatke.")
        return

    unique_leaders = []
    seen_codes = set()

    for card in all_cards:
        # Provjera je li karta Leader (provjeravamo polja rarity, category i card_type)
        rarity = str(card.get("rarity") or "").strip().upper()
        category = str(card.get("category") or card.get("card_type") or card.get("type") or "").strip().upper()
        
        is_leader = (rarity == "LEADER") or (category == "LEADER")
        
        if is_leader:
            raw_code = str(card.get("id") or card.get("card_number") or card.get("code") or card.get("card_id") or "")
            
            # Izvlačenje čiste šifre (npr. OP01-001, ST10-001, EB01-001) bez Alt-Art dodataka
            match = re.search(r'([A-Z0-9]+-\d{3,4})', raw_code)
            base_code = match.group(1) if match else raw_code.split('_')[0].split('-AA')[0]
            
            if base_code and base_code not in seen_codes:
                seen_codes.add(base_code)
                
                name = card.get("name") or card.get("card_name") or ""
                color_raw = card.get("colors") or card.get("color") or card.get("ext_color") or ""
                
                # Formatiranje boje (npr. ["Red", "Green"] -> "Red/Green")
                if isinstance(color_raw, list):
                    color = "/".join(str(c).capitalize() for c in color_raw)
                else:
                    color = str(color_raw).strip()
                
                if name and base_code:
                    unique_leaders.append({
                        "name": name,
                        "code": base_code,
                        "color": color
                    })

    # Sortiranje po šifri
    unique_leaders.sort(key=lambda x: x["code"])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(unique_leaders, f, indent=2, ensure_ascii=False)

    print(f"\nUspješno spremljeno {len(unique_leaders)} jedinstvenih Leadera u:\n{OUTPUT_FILE}")

if __name__ == "__main__":
    main()