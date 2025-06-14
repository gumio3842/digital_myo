from flask import Flask, render_template, request, redirect, url_for, session
import openai
import os
import random
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

questions = [
    "당신의 이름을 알려주시겠어요?",
    "당신은 언제 태어나셨나요?",
    "당신이 어떤 일을 하시는지 알 수 있을까요? 활동 영역이나 장래 희망도 괜찮아요.",
    "평소에 자주 하는 말이 있으신가요?",
    "당신이 가장 중요하게 생각하는 가치는 무엇인가요?",
    "당신이 가장 소중하게 여기는 것은 무엇인가요?",
    "당신이 가장 행복한 순간은 언제인가요?",
    "마지막으로, 당신을 한 단어로 표현하면 어떤 사람인가요?"
]

fields = ["name", "birth", "job", "quote", "value", "precious", "happy", "word"]

@app.route('/', methods=['GET'])
def index():
    session.clear()
    session['step'] = 0
    return render_template('index.html')

@app.route('/question', methods=['GET', 'POST'])
def question():
    step = session.get('step', 0)
    if request.method == 'POST':
        answer = request.form.get('answer')
        if step < len(fields):
            session[fields[step]] = answer
            session['step'] = step + 1
            step += 1

    if step >= len(fields):
        return redirect(url_for('style'))

    return render_template('question.html', question=questions[step])

@app.route('/style', methods=['GET', 'POST'])
def style():
    if request.method == 'POST':
        selected_style = request.form.get('style')
        session['style'] = selected_style
        return redirect(url_for('color'))
    return render_template('style.html')

@app.route('/color', methods=['GET', 'POST'])
def color():
    if request.method == 'POST':
        session['color'] = request.form.get('color')
        session['shape'] = request.form.get('shape')
        return redirect(url_for('result'))
    return render_template('color.html')

@app.route('/ai_color', methods=['POST'])
def ai_color():
    data = {field: session[field] for field in fields}
    style = session['style']
    prompt = f"다음 사람의 묘비명에 어울리는 색상을 추천해줘. 결과는 HEX 색상 코드 한 줄만 출력해줘. (예: #FFAA33)\n{data}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 색상 추천 AI입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=20,
        temperature=0.7,
    )
    color = response.choices[0].message.content.strip()
    return color

def build_prompt(data, style):
    intro = (
        f"직업이나 장래희망: {data['job']}\n"
        f"평소 자주 하는 말: {data['quote']}\n"
        f"가장 중요하게 생각하는 가치: {data['value']}\n"
        f"가장 소중하게 여기는 것: {data['precious']}\n"
        f"가장 행복한 순간: {data['happy']}\n"
        f"한 단어로 표현한 자기소개: {data['word']}\n"
    )
    if style == "normal":
        instruction = "위 정보를 바탕으로 평범한 묘비명을 한글로 한 문장으로 작성해줘."
    elif style == "spicy":
        instruction = "위 정보를 바탕으로 매우 풍자적이고 까는 느낌만 가득한 묘비명을 한글로 한 문장으로 작성해줘. 멋있게 보일 필요 없어. 상대가 화나게 해도 돼."
    elif style == "heroic":
        instruction = "위 정보를 바탕으로 위대한 영웅의 묘비명처럼 장엄하고 웅장한 어조로 한글로 한 문장으로 작성해줘."
    else:
        instruction = "위 정보를 바탕으로 평범한 감성적인 묘비명을 한글로 한 문장으로 작성해줘."
    return intro + "\n" + instruction

@app.route('/result')
def result():
    data = {field: session[field] for field in fields}
    style = session['style']
    if style == 'random':
        style = random.choice(['normal', 'spicy', 'heroic'])
    prompt = build_prompt(data, style)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 창의적인 묘비명 작성 AI입니다. 주어진 정보들을 통해 정보 입력자의 인생을 예상하고, 그걸 기반으로 사후 묘비명을 적어야 합니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.7,
    )
    epitaph = response.choices[0].message.content.strip()
    color = session.get('color', '#808080')
    shape = session.get('shape', 'tombstone.png')
    return render_template('result.html', data=data, epitaph=epitaph, color=color, shape=shape)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
