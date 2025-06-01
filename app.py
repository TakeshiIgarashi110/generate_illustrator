from flask import Flask, render_template, request, jsonify
import random, csv, base64, requests
from io import BytesIO
from PIL import Image
from collections import Counter
from deep_translator import GoogleTranslator

app = Flask(__name__)

# Stability APIキー（実際のあなたのAPIキーに置き換えてください）
API_KEY = "sk-sVzqiXORQ9ZSrDdID62F7kxzkN32tk2BHJpWG9WR2lRUVyc5"

# 関連語辞書（サジェスト用）
related_words = {
    "黒髪": ["ロング", "赤目", "和風", "陰キャ", "学ラン"],
    "金髪": ["ツインテール", "ハーフ", "明るい", "王族", "アイドル"],
    "メガネ": ["秀才", "図書館", "冷静", "科学者"],
    "獣耳": ["ケモミミ", "しっぽ", "野生児", "ハンター"],
    "炎": ["火山", "熱血", "赤", "ドラゴン"]
}

# キャラ設定用プリセット
races = ["エルフ", "ドワーフ", "人間", "魔族", "獣人"]
jobs = ["剣士", "魔法使い", "僧侶", "盗賊", "召喚士"]
personalities = ["冷静", "熱血", "優しい", "無口", "陽気"]
skills = ["炎の剣", "回復魔法", "ステルス", "時間停止", "召喚術"]

# 翻訳
def translate_to_english(text):
    return GoogleTranslator(source='ja', target='en').translate(text)

# プロンプト生成
def create_prompt(character):
    race = translate_to_english(character["race"])
    job = translate_to_english(character["job"])
    personality = translate_to_english(character["personality"])
    skill = translate_to_english(character["skill"])
    description = translate_to_english(character.get("description", ""))
    return f"An anime-style {race} {job}, {personality}, using {skill}, fantasy background. {description}"

# 画像生成 (無料版対応)
def generate_image(prompt):
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "text_prompts": [
            {"text": prompt}
        ],
        "cfg_scale": 7,
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 30
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    image_base64 = result["artifacts"][0]["base64"]
    return image_base64

# キャラ情報保存
def save_character_to_csv(character):
    with open("character_stats.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([character["race"], character["job"], character["personality"], character["skill"]])

# メインページ
@app.route("/")
def index():
    character = {
        "race": random.choice(races),
        "job": random.choice(jobs),
        "personality": random.choice(personalities),
        "skill": random.choice(skills)
    }
    return render_template("index.html", character=character)

# 通常生成
@app.route("/generate", methods=["POST"])
def generate():
    character = {
        "race": request.form["race"],
        "job": request.form["job"],
        "personality": request.form["personality"],
        "skill": request.form["skill"]
    }
    prompt = create_prompt(character)

    try:
        img_b64 = generate_image(prompt)
        image = Image.open(BytesIO(base64.b64decode(img_b64)))
        image_path = "static/generated.png"
        image.save(image_path)

        save_character_to_csv(character)
        summary = get_summary_data()

        return render_template("result.html", character=character, image_path=image_path, summary=summary)
    except Exception as e:
        return f"エラーが発生しました: {e}"

# カスタムフォーム
@app.route("/custom")
def custom_form():
    return render_template("custom.html")

# カスタム生成
@app.route("/custom_generate", methods=["POST"])
def custom_generate():
    character = {
        "race": request.form["race"],
        "job": request.form["job"],
        "personality": request.form["personality"],
        "skill": request.form["skill"]
    }
    prompt = create_prompt(character)

    try:
        img_b64 = generate_image(prompt)
        image = Image.open(BytesIO(base64.b64decode(img_b64)))
        image_path = "static/generated.png"
        image.save(image_path)
        return render_template("result.html", character=character, image_path=image_path)
    except Exception as e:
        return f"カスタム生成中にエラーが発生: {e}"

# ハイブリッドフォーム
@app.route("/hybrid")
def hybrid_form():
    return render_template("hybrid.html")

# ハイブリッド生成
@app.route("/hybrid_generate", methods=["POST"])
def hybrid_generate():
    def merge(preset, custom):
        return custom if custom.strip() else preset

    character = {
        "race": merge(request.form["race_preset"], request.form["race_custom"]),
        "job": merge(request.form["job_preset"], request.form["job_custom"]),
        "personality": merge(request.form["personality_preset"], request.form["personality_custom"]),
        "skill": request.form["skill"]
    }

    prompt = create_prompt(character)

    try:
        img_b64 = generate_image(prompt)
        image = Image.open(BytesIO(base64.b64decode(img_b64)))
        image_path = "static/generated.png"
        image.save(image_path)
        return render_template("result.html", character=character, image_path=image_path)
    except Exception as e:
        return f"ハイブリッド生成中にエラーが発生: {e}"

# 関連語サジェスト
@app.route("/related")
def related():
    query = request.args.get("q", "")
    suggestions = related_words.get(query, [])
    return jsonify({"suggestions": suggestions})

# CSV集計
def get_summary_data():
    summary = {
        "race": Counter(),
        "job": Counter(),
        "personality": Counter(),
        "skill": Counter()
    }

    try:
        with open("character_stats.csv", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                summary["race"][row[0]] += 1
                summary["job"][row[1]] += 1
                summary["personality"][row[2]] += 1
                summary["skill"][row[3]] += 1
        return {
            key: sorted(counter.items(), key=lambda x: x[1], reverse=True)
            for key, counter in summary.items()
        }
    except FileNotFoundError:
        return {key: [] for key in summary}

# Flaskサーバー起動
if __name__ == "__main__":
    app.run(debug=True)
