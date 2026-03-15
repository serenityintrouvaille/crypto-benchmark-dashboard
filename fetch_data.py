#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crypto Benchmark Real Data Fetcher (V4 - Real-Time Pipeline)
이 스크립트는 Vercel Serverless Function(api/refresh.py)의 핵심 로직을 그대로 
재사용하여 매일 9시 GitHub Actions에서도 정적으로 data.js를 업데이트하도록 합니다.
"""

import sys
import os
import json
from datetime import datetime, timezone

# api 폴더 내의 refresh.py 모듈을 임포트합니다.
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))
from refresh import get_live_crypto_products

def generate_data_js(articles):
    if len(articles) == 0:
        print("[오류] 일주일 내 추출된 프로덕트가 0개입니다.")
        return
        
    js_content = f"// V4 Product Data (업데이트: {datetime.now(timezone.utc).isoformat()})\n\n"
    js_content += "export const cryptoServices = " + json.dumps(articles, ensure_ascii=False, indent=2) + ";\n\n"
    
    sectors = ['모두보기', '송금 (Remittance)', '프로토콜 (Protocol)', '투자 (Investment)', '금융 (Finance)', 'DeFi (Decentralized Finance)', '스테이블코인 (Stablecoin)', '인프라 (Infra)', 'NFT/게이밍', '모듈러 체인 (Modular)']
    js_content += "export const sectors = " + json.dumps(sectors, ensure_ascii=False) + ";\n"

    os.makedirs("src", exist_ok=True)
    with open("src/data.js", "w", encoding="utf-8") as f:
        f.write(js_content)
    
    print(f"[성공] src/data.js 파일 실시간 업데이트 완료. ({len(articles)}개 항목)")

if __name__ == "__main__":
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] GitHub Actions 배치 수집 시작...")
        articles = get_live_crypto_products()
        generate_data_js(articles)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
