import json
from rapidfuzz import process, fuzz

CUSTOMERS_FILE = "customers.json"

def run_test():
    try:
        with open(CUSTOMERS_FILE, 'r', encoding='utf-8') as f:
            customers = json.load(f)
    except FileNotFoundError:
        print(f"Error: {CUSTOMERS_FILE} not found.")
        return
    
    search_term = "schnei"
    search_lower = search_term.lower()
    
    choices = []
    for c in customers:
        choices.append(f"{c.get('vorname','')} {c.get('nachname','')} {c.get('street','')} {c.get('city','')}")
    
    # WRatio + NEW BOOST LOGIC
    raw_results = process.extract(search_term, choices, scorer=fuzz.WRatio, limit=50)
    
    scored_customers = []
    for text, score, idx in raw_results:
        customer = customers[idx]
        boosted_score = score
        
        vn = customer.get('vorname', '').lower()
        nn = customer.get('nachname', '').lower()
        org = customer.get('organization', '').lower()
        
        if nn.startswith(search_lower):
            boosted_score += 20
        elif vn.startswith(search_lower):
            boosted_score += 15
        elif org.startswith(search_lower):
            boosted_score += 10
            
        scored_customers.append((text, boosted_score))

    scored_customers.sort(key=lambda x: x[1], reverse=True)
    
    print(f"--- Top 10 Search Results for '{search_term}' with Prefix Boost ---")
    for i, (text, score) in enumerate(scored_customers[:10]):
        print(f"[{i}] {score:6.2f} | {text}")

    # Check relevance
    top_match = scored_customers[0][0].lower()
    if "schneider" in top_match:
        print("\n✅ SUCCESS: 'Schneider' is now at position 0 due to prefix boost.")
    else:
        print(f"\n❌ FAILURE: '{scored_customers[0][0]}' is still at top.")

if __name__ == "__main__":
    run_test()
