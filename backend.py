# backend.py
import json
from fastapi import FastAPI, UploadFile, File
from PIL import Image
import io
import torch
from torchvision import transforms, models
import sqlite3
import os
import requests

# JSON 파일 다운로드 및 로드
if not os.path.isfile('imagenet-simple-labels.json'):
    url = 'https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json'
    r = requests.get(url)
    with open('imagenet-simple-labels.json', 'w') as f:
        f.write(r.text)

with open('imagenet-simple-labels.json', 'r') as f:
    class_names = json.load(f)

# 이미지 전처리
def preprocess_image(image):
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    image = transform(image).unsqueeze(0)
    return image

# 이미지 분류
def classify_image(image):
    model = models.resnet50(pretrained=True)
    model.eval()
    output = model(image)
    _, predicted = torch.max(output, 1)
    return predicted.item()

# 라벨(숫자)를 라벨(이름)으로 변환
def label_to_name(label):
    return class_names[label]

# DB에 결과 저장
def save_to_db(filename, label):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, filename TEXT, label INTEGER, name TEXT)")
    name = label_to_name(label)
    c.execute("INSERT INTO results (filename, label, name) VALUES (?, ?, ?)", (filename, label, name))
    conn.commit()
    conn.close()

# DB에서 결과 가져오기
def get_results():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row  # 쿼리 결과를 딕셔너리로 반환하도록 설정
    c = conn.cursor()
    c.execute("SELECT * FROM results")
    results = [dict(row) for row in c.fetchall()]  # 각 행을 딕셔너리로 변환
    conn.close()
    return results

app = FastAPI()

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read()))
    image = preprocess_image(image)
    label = classify_image(image)
    save_to_db(file.filename, label)  # 이 부분이 변경되었습니다.
    return {"filename": file.filename, "label": label}

@app.get("/results")
def get_all_results():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, filename TEXT, label INTEGER, name TEXT)")
    c.execute("SELECT * FROM results")
    results = c.fetchall()
    conn.close()
    return results

@app.get("/results/view/{page}")
def get_results(page: int):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, filename TEXT, label INTEGER, name TEXT)")
    c.execute("SELECT COUNT(*) FROM results")
    total_results = c.fetchone()[0]
    if (page - 1) * 20 >= total_results:  # 페이지 번호가 유효한지 확인
        return {"error": "Invalid page number"}
    c.execute("SELECT * FROM results ORDER BY id LIMIT 20 OFFSET ?", ((page - 1) * 20,))
    results = c.fetchall()
    conn.close()
    return results

@app.get("/results/count")
def get_results_count():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, filename TEXT, label INTEGER, name TEXT)")
    c.execute("SELECT COUNT(*) FROM results")
    count = c.fetchone()[0]
    conn.close()
    return {"count": count}


