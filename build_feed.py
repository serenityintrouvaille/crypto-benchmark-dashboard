import os
import time
import json
import feedparser
import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configuration & Source Registry
# ----------------------------------------------------
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDqBuA3ET7chtS2Q3E0LgTfLXg793sAXVc")
client = genai.Client(api_key=API_KEY)

# PRD: Initial MVP Sources (Tier 1, 2)
SOURCES = [
    {"name": "CoinDesk", "url": "https://coindesk.com/feed", "tier": 2},
    {"name": "The Block", "url": "https://theblockresearch.com/feed", "tier": 2},
    {"name": "Decrypt", "url": "https://decrypt.co/feed", "tier": 2},
    {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss", "tier": 2},
    {"name": "The Defiant", "url": "https://thedefiant.io/feed", "tier": 2},
    {"name": "Blockworks", "url": "https://blockworks.co/feed", "tier": 2},
    {"name": "Pantera Capital", "url": "https://panteracapital.com/feed/", "tier": 1},
    {"name": "a16z Crypto", "url": "https://a16zcrypto.com/feed/", "tier": 1},
    {"name": "Ethereum Blog", "url": "https://blog.ethereum.org/feed.xml", "tier": 1},
    {"name": "DeFi Llama", "url": "https://defillama.com/feed", "tier": 3}
]

# Output file path for the frontend
OUTPUT_JSON_PATH = "public/feed.json"

DAYS_TO_LOOK_BACK = 7

# ----------------------------------------------------
# 2. Ingestion
# ----------------------------------------------------
def fetch_articles():
    print("Fetching articles from sources...")
    articles = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=DAYS_TO_LOOK_BACK)
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})
    
    for source in SOURCES:
        try:
            print(f"  Fetching: {source['name']}")
            res = session.get(source["url"], timeout=10)
            feed = feedparser.parse(res.content)
            
            count = 0
            for entry in feed.entries:
                if count >= 35: # Increased to ensure 20-30 final outputs
                    break
                    
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed), timezone.utc)
                
                # Default to now if parsing completely fails, just to send it to LLM
                if not pub_date:
                    pub_date = datetime.now(timezone.utc)
                    
                if pub_date < cutoff_date:
                    continue
                    
                title = entry.get("title", "")
                summary = entry.get("summary", "").replace("<[^>]+>", "")
                link = entry.get("link", "#")
                
                articles.append({
                    "title": title,
                    "summary": summary[:800], # truncate early
                    "link": link,
                    "source_name": source["name"],
                    "source_tier": source["tier"],
                    "pub_date": pub_date.isoformat()
                })
                count += 1
        except Exception as e:
            print(f"  Failed {source['name']}: {e}")
            
    print(f"Total articles fetched: {len(articles)}")
    return articles

# ----------------------------------------------------
# 3. LLM Processing
# ----------------------------------------------------
def process_article_via_llm(article):
    """
    Uses Gemini to determine if an article is about a crypto product/service 
    and extracts the structured PRD fields.
    """
    sys_prompt = """
    당신은 Web3 프로덕트 리서처입니다.
    주어진 뉴스 기사/블로그 요약을 읽고, 웹3 서비스, 제품, 비즈니스, 크립토 시장, 토큰, 투자, 생태계 뉴스 등과 관련된 모든 글을 최대한 긍정적으로 판단하여 데이터를 만드세요.
    거의 모든 크립토/웹3 관련 내용이면 "is_product_news": true 로 처리하세요. (이 거름망을 통과해야 대시보드에 전시되므로 절대 까다롭게 굴지 마세요)
    
    JSON 형식으로 응답해야 합니다. JSON 스키마는 다음과 같습니다:
    {
       "is_product_news": boolean,
       "product_name": "프로젝트/서비스의 이름 (예: Uniswap, Pump.fun)",
       "category": "분류 태그 (예: Wallet, DeFi, Infrastructure, Consumer App, Payments, L2 중 택1 혹은 직접 작성)",
       "event_type": "이벤트 유형 (Launch, Funding, Update, Partnership, Mainnet 중 택1)",
       "one_line_summary": "이 제품/뉴스가 어떤 내용인지에 대한 국문 요약문",
       "why_it_matters": "이 제품/뉴스가 왜 중요한지, 어떤 차별점이 있는지, 업계 생태계에 미칠 영향이나 기술적/비즈니스적 의의를 아주 상세하고 깊이 있게 3~4문장 이상의 긴 단락 수준으로 국문 작성 (최대한 길고 구체적이며 충실하게 정보를 채울 것)"
    }
    """
    
    user_prompt = f"제목: {article['title']}\n요약: {article['summary']}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        err_msg = str(e).encode('ascii', 'ignore').decode('ascii')
        safe_title = article['title'][:30].encode('ascii', 'ignore').decode('ascii')
        print(f"LLM Error on {safe_title}: {err_msg}")
        return {"is_product_news": False}

# ----------------------------------------------------
# 4. Deduplication & Scoring
# ----------------------------------------------------
def compile_trending_feed(raw_articles):
    print("Processing articles through AI ... This may take a few minutes.")
    products_map = {}
    
    for i, art in enumerate(raw_articles):
        # Throttle slightly to respect free tier rate limits (15 RPM limits might apply on some free tiers, though 2.5-flash is usually 15 RPM. Wait, actually Flash is 15 RPM for free tier - let's add a short sleep just in case, or rely on fast processing)
        # Actually Google AI Studio free tier for gemini-1.5-flash is 15 RPM. 
        # If we have 50 articles, it could easily hit limits if we do 1 per second.
        # We'll sleep 4s to be safe between calls.
        
        if i % 10 == 0:
            print(f"Processed {i}/{len(raw_articles)}")
            
        llm_data = process_article_via_llm(art)
        
        if not llm_data.get("is_product_news", False):
            continue
            
        p_name = llm_data.get("product_name", "Web3 Trend").strip().upper()
        if p_name == "UNKNOWN" or len(p_name) < 2:
            p_name = "CRYPTO TREND"
            
        # Deduplication Strategy: Group by capitalized product name
        if p_name not in products_map:
            products_map[p_name] = {
                "id": str(int(time.time() * 1000)) + "_" + p_name.replace(" ", ""),
                "name": llm_data.get("product_name"),
                "category": llm_data.get("category", "General"),
                "event_type": llm_data.get("event_type", "Update"),
                "one_line_summary": llm_data.get("one_line_summary", ""),
                "why_it_matters": llm_data.get("why_it_matters", ""),
                "detected_date": art["pub_date"],
                "source_links": [{"name": art["source_name"], "url": art["link"]}],
                "official_link": art["link"] if art["source_tier"] == 1 else None,
                "tier_1_count": 1 if art["source_tier"] == 1 else 0,
                "tier_2_count": 1 if art["source_tier"] == 2 else 0,
                "tags": [llm_data.get("category", "Crypto")]
            }
        else:
            # Add to sources
            existing = products_map[p_name]
            # Avoid exact duplicate links
            if not any(sl["url"] == art["link"] for sl in existing["source_links"]):
                existing["source_links"].append({"name": art["source_name"], "url": art["link"]})
                
            if art["source_tier"] == 1:
                existing["tier_1_count"] += 1
                existing["official_link"] = art["link"] # override with official
            elif art["source_tier"] == 2:
                existing["tier_2_count"] += 1

        # Sleep to avoid 429 Too Many Requests (10 RPM limit on free tier -> 6.5s sleep)
        time.sleep(6.5)

    # Calculate Trending Score
    print("Calculating Trending Scores...")
    results = []
    
    # Base datetime for recency
    now = datetime.now(timezone.utc)
    
    for p_name, data in products_map.items():
        score = 0
        
        # 1. Recency Score (max 35)
        # We parse the isoformat string back to a datetime object
        try:
            pub_date = date_parser.parse(data["detected_date"])
            days_ago = (now - pub_date).days
            recency_score = max(0, 35 - (days_ago * 5))
            score += recency_score
        except:
            score += 10
            
        # 2. Multi-source score (max 25)
        source_count = len(data["source_links"])
        score += min(25, source_count * 5)
        
        # 3. Official Source Existence (max 20)
        if data["tier_1_count"] > 0:
            score += 20
            
        # 4. Event Intensity (max 10)
        evt = data["event_type"].lower()
        if "launch" in evt or "funding" in evt or "mainnet" in evt:
            score += 10
        elif "update" in evt:
            score += 5
            
        # 5. New Entity Bonus (max 10) - Assumed 10 for all newly detected in MVP
        score += 10
        
        data["trending_score"] = score
        data["source_count"] = source_count
        results.append(data)
        
    # Sort by trending score descending
    results = sorted(results, key=lambda x: x["trending_score"], reverse=True)
    return results

def generate_daily_briefing(top_items):
    print("Generating Daily Briefing...")
    if not top_items:
        return "새로운 제품 소식이 없습니다."

    # Send top 10 to LLM for a newsletter-style curation intro
    context = ""
    for i, item in enumerate(top_items[:10]):
        context += f"{i+1}. {item['name']} ({item['event_type']}): {item['one_line_summary']}\n"
        
    sys_prompt = """
    당신은 최고급 뉴스레터 에디터입니다.
    오늘의 트렌딩 크립토 제품 톱 10개 목록을 보고, "오늘의 큐레이션 타임라인"이라는 컨셉으로 최상단에 노출될 
    아주 매력적이고 전문적인 뉴스레터 형식의 개요(Briefing)를 2~3문단으로 작성하세요. 
    오늘 시장에서 어떤 테마가 주요하게 떠올랐는지, 특별히 주목해야 할 흐름이 무엇인지 짚어주세요.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=f"목록:\n{context}",
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                temperature=0.7
            )
        )
        return response.text.replace("```markdown", "").replace("```", "").strip()
    except Exception as e:
        print("Failed to generate briefing:", e)
        return "오늘은 다양한 웹3 프로덕트 및 파트너십 소식이 업데이트되었습니다."

# ----------------------------------------------------
# 5. Main Execution
# ----------------------------------------------------
def main():
    print("=== Crypto Product Radar: Feed Builder Started ===")
    
    # 1. Fetch
    raw_articles = fetch_articles()
    
    # 2. Process
    processed_feed = compile_trending_feed(raw_articles)
    
    # 3. Briefing Gen
    briefing = generate_daily_briefing(processed_feed)
    
    # 4. Save Payload
    payload = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "item_count": len(processed_feed),
        "daily_briefing": briefing,
        "data": processed_feed
    }
    
    if len(processed_feed) == 0:
        print("No items processed (likely due to API rate limits). Skipping feed.json replacement to preserve old data.")
        return
        
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    print(f"=== Process Complete. Saved {len(processed_feed)} curated products to {OUTPUT_JSON_PATH} ===")

if __name__ == "__main__":
    main()
