from flask import Flask, request, send_file, jsonify
import openai
from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta
import io
import json
import os

openai.api_key = os.environ["OPENAI_API_KEY"]

app = Flask(__name__)

from flask_cors import CORS
CORS(app)

def nlu_parse(text):
    prompt = f"""
你是一个专业日历解析助手。请将如下中文日历描述解析为标准json，字段如下：
{{
"summary": "事件标题",
"location": "地点",
"dtstart": "YYYY-MM-DD HH:MM",
"dtend": "YYYY-MM-DD HH:MM",
"alarms": [
    {{"trigger": "提前x分钟/小时/天", "desc": "提醒内容"}}
],
"rrule": "如FREQ=WEEKLY;UNTIL=YYYYMMDDT235959Z",
"note": "备注（如路程等）"
}}
只输出json，无任何解释，无代码块，无多余文本。

描述：{text}
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content
    return json.loads(content)

@app.route('/generate_ics', methods=['POST'])
def generate_ics():
    data = request.json
    text = data.get('text', '')
    try:
        event_data = nlu_parse(text)
        # --- 强健性校验 ---
        if "YYYY" in event_data["dtstart"] or "YYYY" in event_data["dtend"]:
            return jsonify({'error': '解析出的时间格式不对，请重试'}), 400
    except Exception as e:
        return jsonify({'error': '解析失败', 'detail': str(e)}), 400
    # ...后续正常逻辑...
mat_exc()}), 500


    cal = Calendar()
    event = Event()
    event.add('summary', event_data["summary"])
    event.add('dtstart', datetime.strptime(event_data["dtstart"], "%Y-%m-%d %H:%M"))
    event.add('dtend', datetime.strptime(event_data["dtend"], "%Y-%m-%d %H:%M"))
    if event_data.get("location"):
        event.add('location', event_data["location"])
    if event_data.get("rrule"):
        event.add('rrule', event_data["rrule"])
    if event_data.get("note"):
        event.add('description', event_data["note"])
    for alarm in event_data["alarms"]:
        trigger_str = alarm["trigger"]
        if "天" in trigger_str:
            value = int(trigger_str.replace("提前", "").replace("天", ""))
            trigger = timedelta(days=-value)
        elif "小时" in trigger_str:
            value = int(trigger_str.replace("提前", "").replace("小时", ""))
            trigger = timedelta(hours=-value)
        else:
            value = int(trigger_str.replace("提前", "").replace("分钟", ""))
            trigger = timedelta(minutes=-value)
        a = Alarm()
        a.add('action', 'DISPLAY')
        a.add('description', alarm.get("desc", event_data["summary"]+"提醒"))
        a.add('trigger', trigger)
        event.add_component(a)
    cal.add_component(event)

    ics_bytes = cal.to_ical()
    ics_file = io.BytesIO(ics_bytes)
    ics_file.seek(0)
    return send_file(
        ics_file,
        as_attachment=True,
        download_name='event.ics',
        mimetype='text/calendar'
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5678))
    app.run(host="0.0.0.0", port=port)
