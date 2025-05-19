from flask import Flask, render_template, request, jsonify
import random
import requests
import base64
from io import BytesIO
from PIL import Image
from deep_translator import GoogleTranslator

app = Flask(__name__)
import csv
from collections import Counter
related_words = {
    "黒髪": ["ロング", "赤目", "和風", "陰キャ", "学ラン"],
    "金髪": ["ツインテール", "ハーフ", "明るい", "王族", "アイドル"],
    "メガネ": ["秀才", "図書館", "冷静", "科学者"],
    "獣耳": ["ケモミミ", "しっぽ", "野生児", "ハンター"],
    "炎": ["火山", "熱血", "赤", "ドラゴン"]
}


# 選択内容をCSVに保存
def save_character_to_csv(character):
    with open("character_stats.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([character["race"], character["job"], character["personality"], character["skill"]])

@app.route("/stats")
def stats():
    stats_counter = Counter()
    try:
        with open("character_stats.csv", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                stats_counter.update(row)
    except FileNotFoundError:
        return jsonify({"labels": [], "counts": []})

    labels = list(stats_counter.keys())
    counts = list(stats_counter.values())
    return jsonify({"labels": labels, "counts": counts})

# キャラ設定リスト
races = ["エルフ", "ドワーフ", "人間", "魔族", "獣人"]
jobs = ["剣士", "魔法使い", "僧侶", "盗賊", "召喚士"]
personalities = ["冷静", "熱血", "優しい", "無口", "陽気"]
skills = ["炎の剣", "回復魔法", "ステルス", "時間停止", "召喚術"]

# 翻訳してプロンプト生成
def translate_to_english(text):
    return GoogleTranslator(source='ja', target='en').translate(text)

def create_prompt(character):
    race = translate_to_english(character["race"])
    job = translate_to_english(character["job"])
    personality = translate_to_english(character["personality"])
    skill = translate_to_english(character["skill"])
    description = translate_to_english(character.get("description", ""))
    return f"An anime-style {race} {job}, {personality}, using {skill}, fantasy background. {description}"


@app.route("/")
def index():
    character = {
        "race": random.choice(races),
        "job": random.choice(jobs),
        "personality": random.choice(personalities),
        "skill": random.choice(skills)
    }
    return render_template("index.html", character=character)


@app.route("/generate", methods=["POST"])
def generate():
    character = {
        "race": request.form["race"],
        "job": request.form["job"],
        "personality": request.form["personality"],
        "skill": request.form["skill"]
    }
    prompt = create_prompt(character)

    # 正しいColabのURLをここに貼る
    url = "https://6a88-34-16-185-196.ngrok-free.app/generate"  # ← 実行後に出たURLに差し替え

    try:
        response = requests.post(url, json={"prompt": prompt})
        response.raise_for_status()  # 400/500 エラー時に例外化

        img_data = response.json()["image"]
        image = Image.open(BytesIO(base64.b64decode(img_data)))
        image_path = "static/generated.png"
        image.save(image_path)
        save_character_to_csv(character)

        return render_template("result.html", character=character, image_path=image_path)
    except requests.exceptions.RequestException as e:
        return f"リクエストエラーが発生しました: {e}"
    except Exception as e:
        return f"画像処理中にエラーが発生しました: {e}"
    
    return render_template("result.html", character=character, image_path=image_path)
@app.route("/custom")
def custom_form():
    return render_template("custom.html")

@app.route("/custom_generate", methods=["POST"])
def custom_generate():
    character = {
        "race": request.form["race"],
        "job": request.form["job"],
        "personality": request.form["personality"],
        "skill": request.form["skill"]
    }
    prompt = create_prompt(character)

    # Stable Diffusionに送信（既存と同様）
    url = "https://6a88-34-16-185-196.ngrok-free.app/generate"
    response = requests.post(url, json={"prompt": prompt})
    img_data = response.json()["image"]

    # base64デコードして保存
    image = Image.open(BytesIO(base64.b64decode(img_data)))
    image_path = "static/generated.png"
    image.save(image_path)

    return render_template("result.html", character=character, image_path=image_path)

@app.route("/hybrid")
def hybrid_form():
    return render_template("hybrid.html")


@app.route("/hybrid_generate", methods=["POST"])
def hybrid_generate():
    # プリセット + 自由入力を合成
    def merge(preset, custom):
        return custom if custom.strip() else preset

    character = {
        "race": merge(request.form["race_preset"], request.form["race_custom"]),
        "job": merge(request.form["job_preset"], request.form["job_custom"]),
        "personality": merge(request.form["personality_preset"], request.form["personality_custom"]),
        "skill": request.form["skill"]
    }

    prompt = create_prompt(character)

    # 画像生成APIに送信
    url = "https://6a88-34-16-185-196.ngrok-free.app/generate"  # ←実際のURLに置き換え
    response = requests.post(url, json={"prompt": prompt})
    img_data = response.json()["image"]

    # 画像保存処理
    image = Image.open(BytesIO(base64.b64decode(img_data)))
    image_path = "static/generated.png"
    image.save(image_path)

    return render_template("result.html", character=character, image_path=image_path)

@app.route("/related")
def related():
    query = request.args.get("q", "")
    suggestions = related_words.get(query, [])
    return jsonify({"suggestions": suggestions})

if __name__ == "__main__":
    app.run(debug=True)