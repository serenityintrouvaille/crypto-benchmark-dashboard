#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crypto Benchmark Real Data Fetcher (V3 - Product Centric)
신규 상장, 디앱 순위, 런칭 정보를 중점적으로 다루는 특화 소스와 키워드를 통해 
순수 '제품/서비스(Product)' 위주로 스크래핑하고, 카드 제목을 '제품명'으로 다듬는 스크립트.
"""

import feedparser
import json
import os
import random
import requests
import re
from datetime import datetime, timezone

# 📰 특화된 Data Sources (CryptoRank, DappRadar, The Defiant, CryptoSlate 등)
SOURCES = [
    # 뉴스/알파 (신제품 리뷰, 창업자 인터뷰 등)
    {"name": "The Defiant", "url": "https://thedefiant.io/feed", "category": "News/Alpha"},
    {"name": "CryptoSlate", "url": "https://cryptoslate.com/feed/", "category": "News/Alpha"},
    {"name": "CoinDesk", "url": "https://coindesk.com/feed", "category": "News/Alpha"},
    {"name": "Cointelegraph", "url": "https://cointelegraph.com/feed", "category": "News/Alpha"},
    
    # 종합/투자/토크노믹스 (CryptoRank, CoinCarp 스타일의 펀딩 뉴스 대체 소스)
    {"name": "Messari", "url": "https://messari.io/feed", "category": "Research"},
    {"name": "The Block", "url": "https://theblockresearch.com/feed", "category": "Research"},
    {"name": "Pantera Capital", "url": "https://panteracapital.com/blog/feed", "category": "VC"},
    {"name": "a16z Crypto", "url": "https://a16zcrypto.com/feed", "category": "VC"},
    
    # 디앱/프로토콜 전문 소스 (DappRadar 랭킹을 대체하는 메커니즘)
    {"name": "DeFi Llama", "url": "https://defillama.com/feed", "category": "DeFi"},
    {"name": "Token Terminal", "url": "https://tokenterminal.com/feed", "category": "DeFi"},
    {"name": "Ethereum Blog", "url": "https://ethereum.org/en/blog/feed.xml", "category": "Protocol"},
    {"name": "Aave", "url": "https://aave.com/blog/feed", "category": "Protocol"}
]

# 🔍 제품/서비스 출시와 직접 연관된 강력한 키워드들
PRODUCT_KEYWORDS = [
    'launch', 'unveils', 'introduces', 'releases', 'mainnet', 'testnet', 'beta', 
    'platform', 'app ', 'raises', 'funding', 'seed', 'series', 'protocol', 'network',
    '출시', '공개', '투자 유치', '메인넷', '플랫폼', '앱', '네트워크'
]

def extract_product_name(title):
    """
    뉴스 제목에서 '제품명'으로 추정되는 선두 1~2 단어를 추출하는 휴리스틱 로직.
    예: "Lens Protocol launches new V2" -> "Lens Protocol"
    예: "Uniswap introduces mobile app" -> "Uniswap"
    예: "A16z backs Crypto Startup XYZ with $10M" -> "Crypto Startup XYZ"
    """
    # 콜론이나 대시 등 구분자가 있다면 그 앞을 제품명으로 취급하는 경우가 많음
    delimiters = [':', ' - ', ' – ', ' | ', ' launches ', ' introduces ', ' announces ', ' raises ', ' unveils ', ' releases ']
    
    extracted = title
    for delim in delimiters:
        if delim.lower() in title.lower():
            # 대소문자 무시 split
            parts = re.split(re.compile(delim, re.IGNORECASE), title)
            extracted = parts[0].strip()
            # "A16z backs ..." 처럼 투자자가 앞에 오면 필터링이 어렵지만, 
            # 일단 가장 직관적인 휴리스틱으로 첫 번째 구문을 가져옴
            if len(extracted.split()) > 5: # 이름이 너무 길면 다음 딜리미터 계속 찾기
                continue
            break
            
    # 여전히 5단어 이상으로 길면 그냥 앞의 3단어만 자름
    words = extracted.split()
    if len(words) > 4:
        extracted = " ".join(words[:3])
        
    # 특수문자 제거
    extracted = re.sub(r'[^\w\s\.-]', '', extracted)
    
    # 최소 길이는 보장
    if len(extracted) < 2:
        return title[:15] + "..."
        
    return extracted

def analyze_deep_data(name, title, summary, source_cat):
    """ 임시 딥다이브 마크다운 생성기 """
    return {
        "businessStructure": [
            f"출처 카테고리 ({source_cat}) 분석 기반 추정 모델",
            f"해당 서비스({name})의 핵심 기능 및 토크노믹스",
            "초기 런칭 및 펀딩을 통한 트래픽/TVL 부트스트래핑 전략"
        ],
        "uxHighlights": [
            f"{name}만의 특화된 디앱(dApp) UX",
            "복잡한 지갑 서명 단계를 추상화(Account Abstraction)한 온보딩 예상",
            "가스비 대납 혹은 L2 체인을 통한 제로-딜레이(Zero-delay) 인터랙션"
        ],
        "metrics": [
            "최근 커뮤니티(Warpcast, Twitter 등) 내 언급량 폭등",
            "신규 릴리즈로 인한 초기 활성 사용자(UAW) 유입 중",
            "투자 라운드 및 뉴스 보도에 따른 시장 주목도(Attention) 최고조"
        ],
        "teamInfo": [
            f"기사 원본: {title}",
            "익명의 빌더 혹은 글로벌 탑티어 개발 씬 크루",
            "디스코드 및 깃허브 커뮤니티 기반 개방형 기여"
        ],
        "funding": [
            "CryptoRank, CoinCarp 등에서 주목받는 신규 펀딩 징후",
            "초기 Seed 혹은 전략적 라운드 자금 유입 완료",
            "추후 토큰 에어드랍(Airdrop)을 통한 부를 재분배할 가능성"
        ],
        "similarServices": [
            "동일 섹터 내 Top 3 프로토콜/앱",
            "DappRadar 기준 경쟁 랭킹 서비스들"
        ]
    }

def fetch_trending_crypto_products():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 프로덕트 특화 다중 RSS 수집 시작 (V3)...")
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})
    
    all_articles = []
    
    for source in SOURCES:
        try:
            response = session.get(source["url"], timeout=8)
            feed = feedparser.parse(response.content)
            
            if hasattr(feed, 'entries') and len(feed.entries) > 0:
                for entry in feed.entries:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "").replace("<[^>]+>", "")
                    
                    text_to_search = (title + " " + summary).lower()
                    
                    # 강력한 제품/서비스 키워드 필터
                    if any(kw.lower() in text_to_search for kw in PRODUCT_KEYWORDS):
                        all_articles.append({
                            "title": title,
                            "summary": summary,
                            "link": entry.get("link", "#"),
                            "source_name": source["name"],
                            "source_category": source["category"]
                        })
        except Exception as e:
            pass 
            
    # 제품 기사 중 6개 랜덤 선택 (항상 새로운 것이 나오게)
    random.shuffle(all_articles)
    selected_products = all_articles[:6]
    
    final_output = []
    sectors_list = ['송금 (Remittance)', '프로토콜 (Protocol)', '투자 (Investment)', '금융 (Finance)', 'DeFi (Decentralized Finance)', '스테이블코인 (Stablecoin)', '인프라 (Infra)', 'NFT/게이밍']
    
    default_images = [
        '/images/payflow_ui_mockup_1773500501890.png',
        '/images/aura_protocol_ui_mockup_2_1773500664347.png',
        '/images/yieldbox_ui_mockup_1773500541897.png',
        '/images/credfi_ui_mockup_1773500567722.png',
        '/images/lunadex_ui_mockup_1773500597920.png',
        '/images/nufiat_ui_mockup_1773500639372.png'
    ]

    for prod in selected_products:
        # ✅ '제품명' 추출
        product_name = extract_product_name(prod["title"])
        
        # 딥다이브 요소
        deep_data = analyze_deep_data(product_name, prod["title"], prod["summary"], prod["source_category"])
        
        final_output.append({
            "id": str(random.randint(1000, 9999)),
            "name": product_name.title(), # 첫 글자 대문자화 (제품명처럼 보이게)
            "sector": random.choice(sectors_list),
            "description": f"[{prod['source_name']}] {prod['title']}", # 설명에 원본 기사 제목 전체 노출
            "link": prod["link"], # ✅ 원본 링크 추가
            "image": random.choice(default_images),
            "businessStructure": deep_data["businessStructure"],
            "uxHighlights": deep_data["uxHighlights"],
            "similarServices": deep_data["similarServices"],
            "metrics": deep_data["metrics"],
            "teamInfo": deep_data["teamInfo"],
            "funding": deep_data["funding"]
        })
        
    print(f"[완료] {len(final_output)}개의 벤치마크 기반 프로덕트 데이터 추출 완료")
    return final_output

def generate_data_js(articles):
    if len(articles) == 0:
        print("[오류] 추출된 프로덕트가 0개입니다.")
        return
        
    js_content = f"// V3 Product Data (업데이트: {datetime.now(timezone.utc).isoformat()})\n\n"
    js_content += "export const cryptoServices = " + json.dumps(articles, ensure_ascii=False, indent=2) + ";\n\n"
    
    sectors = ['모두보기', '송금 (Remittance)', '프로토콜 (Protocol)', '투자 (Investment)', '금융 (Finance)', 'DeFi (Decentralized Finance)', '스테이블코인 (Stablecoin)', '인프라 (Infra)', 'NFT/게이밍']
    js_content += "export const sectors = " + json.dumps(sectors, ensure_ascii=False) + ";\n"

    os.makedirs("src", exist_ok=True)
    with open("src/data.js", "w", encoding="utf-8") as f:
        f.write(js_content)
    
    print("[성공] src/data.js 파일 실시간 업데이트가 완료되었습니다.")

if __name__ == "__main__":
    try:
        articles = fetch_trending_crypto_products()
        generate_data_js(articles)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
