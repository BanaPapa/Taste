import requests
import pandas as pd
import openpyxl
import streamlit as st
from openpyxl.styles import Alignment
from io import BytesIO

# 서버에 요청을 보내고 데이터 수집
def fetch_page_data(region, page):
    url = "https://im.diningcode.com/API/isearch/"
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ko-KR,ko;q=0.5',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.diningcode.com',
        'Referer': 'https://www.diningcode.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    data = {
        'query': region,
        'addr': '',
        'keyword': '',
        'order': 'r_score',
        'distance': '',
        'rn_search_flag': 'on',
        'search_type': 'poi_search',
        'lat': '37.487463640486666',
        'lng': '127.12048655383519',
        'rect': '',
        's_type': '',
        'token': '',
        'mode': 'poi',
        'dc_flag': '1',
        'page': str(page),
        'size': '20',
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("result_data", {}).get("poi_section", {}).get("list", [])
    else:
        st.error(f"Error fetching page {page}: {response.status_code}")
        return []

# 데이터 처리 및 엑셀 저장
def process_data(data):
    important_fields = {
        "nm": "맛집 이름",
        "road_addr": "도로명 주소",
        "phone": "전화번호",
        "category": "카테고리",
        "score": "점수",
        "user_score": "사용자 평점",
        "favorites_cnt": "즐겨찾기 수",
        "review_cnt": "리뷰 수"
    }
    filtered_data = [{important_fields[key]: restaurant.get(key, "") for key in important_fields} for restaurant in data]
    df = pd.DataFrame(filtered_data)
    df = df.sort_values(by=["점수", "리뷰 수"], ascending=[False, False])
    df.insert(0, "번호", range(1, len(df) + 1))
    return df

# 엑셀 파일 생성
def generate_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="맛집 정보")
        wb = writer.book
        ws = writer.sheets["맛집 정보"]

        # 열 너비 자동 조정
        column_widths = {
            "A": 5, "B": 30, "C": 60, "D": 30, "E": 30, "F": 10, "G": 10, "H": 10, "I": 10
        }
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width

        # 텍스트 가운데 정렬
        center_aligned_columns = ["A", "F", "G", "H", "I"]
        center_alignment = Alignment(horizontal="center")
        for col_letter in center_aligned_columns:
            for cell in ws[col_letter]:
                cell.alignment = center_alignment

    output.seek(0)
    return output

# Streamlit UI 구성
st.title("맛집 검색 데이터 다운로드")
region = st.text_input("지역명을 입력하세요:", "")

if st.button("데이터 검색"):
    if not region:
        st.warning("지역명을 입력해주세요!")
    else:
        all_restaurants = []
        for page in range(1, 6):  # 1페이지부터 5페이지까지
            restaurants = fetch_page_data(region, page)
            if restaurants:
                all_restaurants.extend(restaurants)
            else:
                st.warning(f"No data found on page {page}")

        if all_restaurants:
            df = process_data(all_restaurants)
            
            # 화면에 검색 결과 표시
            st.subheader(f"{region} 지역 검색 결과")
            st.dataframe(df)  # Streamlit 데이터프레임 표시
            
            # 엑셀 다운로드 버튼
            excel_data = generate_excel(df)
            st.download_button(
                label="엑셀 파일 다운로드",
                data=excel_data,
                file_name=f"diningcode_{region}_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("해당 지역에서 데이터를 찾을 수 없습니다.")
