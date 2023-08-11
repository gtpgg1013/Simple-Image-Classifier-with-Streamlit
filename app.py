# app.py
import streamlit as st
from PIL import Image
import requests
import io
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide")  # 화면 전체 너비를 사용하도록 설정

st.write("# Image Classification")

page = st.sidebar.selectbox("Choose a page", ["Upload", "View Results"])

if page == "Upload":
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image.', use_column_width=True)
        st.write("")
        st.write("Classifying...")
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        res = requests.post("http://localhost:8000/upload/", files=files)
        if res.ok:
            # 결과를 데이터프레임으로 변환
            df = pd.DataFrame([res.json()])
            df.columns = df.columns.astype(str)  # 컬럼 이름을 문자열로 변환

            st.dataframe(df.to_records(index=False))
        else:
            st.write("Classification failed.")

# app.py

if page == "View Results":
    # 결과의 총 개수 가져오기
    res = requests.get("http://localhost:8000/results/count")
    total_count = res.json()["count"]

    if total_count > 0:  # 결과가 있는지 확인
        # 페이지 번호 선택
        page_number = st.selectbox("Page number", list(range(1, (total_count - 1) // 20 + 2)))

        # 선택된 페이지의 결과 가져오기
        res = requests.get(f"http://localhost:8000/results/view/{page_number}")
        results = res.json()

        if "error" in results:  # 에러 메시지가 있는지 확인
            st.write(results["error"])  # 에러 메시지 출력
        else:
            df = pd.DataFrame(results, columns=["ID", "Filename", "Label", "Name"], )
            df.columns = df.columns.astype(str)  # 컬럼 이름을 문자열로 변환

            # 결과 출력
            st.dataframe(df.to_records(index=False))
    else:
        st.write("No results found.")  # 결과가 없을 때 메시지 출력




