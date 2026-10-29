"""Build the offline study & mock-exam web app for 553127-168 Health Media Development."""
from pathlib import Path
import re, json, html, hashlib, shutil

ROOT = Path(__file__).resolve().parent

META = {
    '08': {
        'shortTitle': 'คาบ 8–9: การสร้างแดชบอร์ดนำเสนอข้อมูลสุขภาพ (Data Studio / Looker Studio)',
        'instructor': 'อ.ดร.ภก.วรวุฒิ อ่อนเอี่ยม, ผศ.ดร.ภก.สรวง รุ่งประกายพรรณ',
        'partLabel': 'ตอนที่ 1: การสร้างแดชบอร์ดนำเสนอข้อมูลสุขภาพ (16 ข้อ)',
        'sourceDefault': 'สไลด์ Data visualization.pdf (198 หน้า) + ไฟล์ประกอบDashboard (Excel 4 ไฟล์) + คลิปสอนคาบ 8–9 (CLO1, CLO3, CLO4)',
        'expectedCount': 40
    },
    '10': {
        'shortTitle': 'คาบ 10: การสร้างสื่อสุขภาพแบบภาพเคลื่อนไหว 2 มิติ (1) ด้วย Animaker',
        'instructor': 'อ.ดร.ภก.วรวุฒิ อ่อนเอี่ยม, ผศ.ดร.ภก.สรวง รุ่งประกายพรรณ',
        'partLabel': 'ตอนที่ 2: การสร้างสื่อสุขภาพแบบภาพเคลื่อนไหว 2 มิติ (1) (8 ข้อ)',
        'sourceDefault': 'สไลด์ animaker69.pdf (94 หน้า) + คลิปสอนคาบ 10 (CLO1, CLO3, CLO4)',
        'expectedCount': 30
    },
    '11': {
        'shortTitle': 'คาบ 11: การสร้างสื่อสุขภาพแบบภาพเคลื่อนไหว 2 มิติ (2) ด้วย Synfig Studio',
        'instructor': 'อ.ดร.ภก.วรวุฒิ อ่อนเอี่ยม, ผศ.ดร.ภก.สรวง รุ่งประกายพรรณ',
        'partLabel': 'ตอนที่ 3: การสร้างสื่อสุขภาพแบบภาพเคลื่อนไหว 2 มิติ (2) (8 ข้อ)',
        'sourceDefault': 'สไลด์ synfig69.pdf (112 หน้า) + ไฟล์ปฏิบัติการ Synfig file (handMove, talk, bone) + คลิปสอนคาบ 11 (CLO1, CLO3, CLO4)',
        'expectedCount': 30
    },
    '12': {
        'shortTitle': 'คาบ 12–13: การเผยแพร่สื่อสุขภาพผ่านอินเทอร์เน็ตด้วย WordPress.org',
        'instructor': 'อ.ดร.ภก.วรวุฒิ อ่อนเอี่ยม, ผศ.ดร.ภก.สรวง รุ่งประกายพรรณ',
        'partLabel': 'ตอนที่ 4: การเผยแพร่สื่อสุขภาพผ่านทางเครือข่ายอินเทอร์เน็ต (16 ข้อ)',
        'sourceDefault': 'สไลด์ wordpress_org.pdf (166 หน้า) + คลิปสอนคาบ 12–13 (CLO1, CLO2, CLO3, CLO4)',
        'expectedCount': 40
    },
}

def format_math(s: str) -> str:
    s = re.sub(r'\$\$(.+?)\$\$', lambda m: f'<strong>{m.group(1)}</strong>', s)
    s = re.sub(r'\\text\{([^}]*)\}', r'\1', s)
    s = s.replace(r'\longrightarrow', '→').replace(r'\rightarrow', '→')
    s = s.replace(r'\ge', '≥').replace(r'\le', '≤')
    s = s.replace('1024^3', '1024³').replace('1000^3', '1000³')
    s = s.replace('$', '')
    return s

def inline(s: str) -> str:
    s = html.escape(s)
    s = format_math(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    return s

def markdown(s: str) -> str:
    out, lines, i = [], s.splitlines(), 0
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()
        if not line:
            i += 1
            continue
        if line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append('<pre class="codeblock">' + '\n'.join(code_lines) + '</pre>')
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = lines[i].strip().strip('|').split('|')
                if not all(re.fullmatch(r'\s*:?-+:?\s*', c) for c in cells):
                    tag = 'th' if not rows else 'td'
                    rows.append('<tr>' + ''.join(f'<{tag}>{inline(c.strip())}</{tag}>' for c in cells) + '</tr>')
                i += 1
            out.append('<div class="table-wrap"><table>' + ''.join(rows) + '</table></div>')
            continue
        if line.startswith('>'):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                cleaned = lines[i].strip().lstrip('>').strip()
                i += 1
                if re.match(r'^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]$', cleaned):
                    continue
                bq_lines.append(inline(cleaned))
            out.append('<blockquote>' + '<br>'.join(bq_lines) + '</blockquote>')
            continue
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            out.append(f'<h{len(m[1])}>{inline(m[2])}</h{len(m[1])}>')
        elif re.fullmatch(r'[-*_]{3,}', line):
            out.append('<hr>')
        elif re.match(r'^[-*]\s+', line):
            out.append('<p class="bullet">• ' + inline(line[2:]) + '</p>')
        elif re.match(r'^\d+[.)]\s+', line):
            out.append('<p class="bullet">' + inline(line) + '</p>')
        else:
            out.append('<p>' + inline(line) + '</p>')
        i += 1
    return '\n'.join(out)

def clean_plain(s: str) -> str:
    s = format_math(s)
    s = re.sub(r'`([^`]+)`', r'\1', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', s)
    return s.strip()

chapters = []
manifest = []

for f in sorted(ROOT.glob('บท*.md')):
    text = f.read_text(encoding='utf-8-sig')
    chap_id = re.search(r'บท(\d+)', f.name)[1]
    meta = META[chap_id]

    summary_part, exam_part = re.split(r'^## แนวข้อสอบจำลอง.*$', text, maxsplit=1, flags=re.M)
    summary_part = summary_part.strip()

    if '## ส่วนที่ 1' in summary_part:
        _, sec1_body = summary_part.split('## ส่วนที่ 1', 1)
        sec1_body = '## ส่วนที่ 1' + sec1_body
    else:
        sec1_body = summary_part

    q_headers = list(re.finditer(r'^### ข้อที่\s+(\d+)\s*(⭐+)?\s*$', exam_part, flags=re.M))
    qs = []
    for ix, m in enumerate(q_headers):
        qnum = int(m.group(1))
        stars = len(m.group(2)) if m.group(2) else 2
        block = exam_part[m.end():q_headers[ix + 1].start() if ix + 1 < len(q_headers) else len(exam_part)].strip()

        det_split = re.split(r'<details>\s*<summary>.*?</summary>', block, maxsplit=1, flags=re.S)
        assert len(det_split) == 2, f'Missing <details> in {f.name} Q{qnum}'
        q_and_opts = det_split[0].strip()
        exp_raw = det_split[1].replace('</details>', '').strip()

        opt_parts = re.split(r'(?:^|\n)-\s*([กขคง])\.\s*', q_and_opts)
        assert len(opt_parts) == 9, (f.name, qnum, len(opt_parts), opt_parts)
        assert opt_parts[1::2] == list('กขคง'), (f.name, qnum)

        q_text = clean_plain(opt_parts[0])
        choices = [clean_plain(c) for c in opt_parts[2::2]]

        ans_match = re.search(r'\*\*คำตอบที่ถูกต้อง:\s*([กขคง])\.\*\*', exp_raw)
        assert ans_match, f'Missing answer key in {f.name} Q{qnum}'
        a_idx = 'กขคง'.index(ans_match.group(1))

        exp_lines = []
        for eline in exp_raw.splitlines():
            eline = eline.strip()
            if not eline or eline.startswith('**คำตอบที่ถูกต้อง:'):
                continue
            eline = re.sub(r'^-\s*', '• ', eline)
            exp_lines.append(clean_plain(eline))
        exp_text = ' | '.join(exp_lines)

        qs.append(dict(
            q=q_text,
            c=choices,
            a=a_idx,
            e=exp_text,
            stars=stars,
            source=meta['sourceDefault'],
            topicId=chap_id,
            topicTitle=meta['shortTitle'],
            partLabel=meta['partLabel']
        ))

    assert len(qs) == meta['expectedCount'], f'{f.name} has {len(qs)} questions instead of {meta["expectedCount"]}'
    title = summary_part.splitlines()[0].lstrip('# ').strip()
    chapters.append(dict(
        id=chap_id,
        title=title,
        shortTitle=meta['shortTitle'],
        instructor=meta['instructor'],
        partLabel=meta['partLabel'],
        summary=markdown(summary_part),
        checklistHtml=markdown(sec1_body),
        bodyHtml=markdown(sec1_body),
        questions=qs,
        filename=f.name
    ))
    manifest.append(dict(
        file=f.name,
        sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
        total=len(qs),
        stars_3=sum(1 for q in qs if q['stars'] == 3),
        stars_2=sum(1 for q in qs if q['stars'] == 2),
        stars_1=sum(1 for q in qs if q['stars'] == 1),
    ))

# Build the 48-question Full Final Exam Simulation matching messageImage_1792597623562.jpg (48 points, 4 Parts: 16 + 8 + 8 + 16)
def pick_curated(chap_id, indices, part_label):
    ch = next(c for c in chapters if c['id'] == chap_id)
    out = []
    for idx in indices:
        q_copy = dict(ch['questions'][idx])
        q_copy['partLabel'] = part_label
        out.append(q_copy)
    return out

exam48_questions = (
    pick_curated('08', [0, 1, 2, 3, 5, 8, 9, 12, 13, 17, 19, 20, 22, 23, 24, 33], 'ตอนที่ 1: การสร้างแดชบอร์ดนำเสนอข้อมูลสุขภาพ (16 ข้อ)') +
    pick_curated('10', [2, 6, 7, 9, 10, 13, 15, 22], 'ตอนที่ 2: การสร้างสื่อสุขภาพแบบภาพเคลื่อนไหว 2 มิติ (1) (8 ข้อ)') +
    pick_curated('11', [0, 2, 3, 4, 9, 15, 18, 27], 'ตอนที่ 3: การสร้างสื่อสุขภาพแบบภาพเคลื่อนไหว 2 มิติ (2) (8 ข้อ)') +
    pick_curated('12', [1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 15, 18, 19, 24, 25, 28], 'ตอนที่ 4: การเผยแพร่สื่อสุขภาพผ่านทางเครือข่ายอินเทอร์เน็ต (16 ข้อ)')
)
assert len(exam48_questions) == 48, len(exam48_questions)

exam48_summary_md = """# จำลองสอบปลายภาคจริง 48 ข้อ 48 คะแนน (ตามโครงสร้างใบปะหน้าข้อสอบ `messageImage_1792597623562.jpg`)

> **รหัสวิชา:** `553127-168 การพัฒนาสื่อสุขภาพ (HEALTH MEDIA DEVELOPMENT)` — วท.บ. (สุขภาพดิจิทัล) ชั้นปีที่ 2  
> **วันและเวลาสอบจริง:** วันที่ 31/10/2026 (31 ตุลาคม 2569) เวลา **14.15 – 15.45 น.** (เวลาสอบ 1.5 ชั่วโมง / 90 นาที)  
> **รูปแบบข้อสอบ:** ข้อสอบปรนัย 4 ตัวเลือก จำนวน 14 หน้า **คะแนนเต็ม 48 คะแนน (48 ข้อ) แบ่งออกเป็น 4 ตอน (16 + 8 + 8 + 16 คะแนน)**

---

## โครงสร้างข้อสอบปลายภาคทั้ง 4 ตอน และโพยสรุปจุดเน้นก่อนเข้าห้องสอบ ⭐⭐⭐

| ตอนที่ | หัวข้อตามใบปะหน้าข้อสอบ | คะแนน | บทเรียนและสื่ออ้างอิง | ประเด็นเก็งข้อสอบที่ต้องจำให้แม่น (⭐⭐⭐) |
| :---: | :--- | :---: | :--- | :--- |
| **ตอนที่ 1** | **การสร้างแดชบอร์ดนำเสนอข้อมูลสุขภาพ** | **16 คะแนน** (16 ข้อ · ข้อ 1–16) | **คาบที่ 8–9** (`Data visualization.pdf` 198 หน้า + `ไฟล์ประกอบDashboard`) | - ความหมายของ **Data Visualization** vs **Dashboard** และประโยชน์จากงานวิจัย 4 ข้อ<br>- เปรียบเทียบ **Google Data Studio (Looker Studio)** vs **Power BI** (แชร์ต้องเสียเงิน) vs **Tableau** (เหมาะกับข้อมูลใหญ่/ซับซ้อน)<br>- การเลือกใช้ **Google Sheets (Dynamic)** vs **MS Excel (Static)**, การกด **Authorize** ครั้งแรก, **Freeform Layout** vs **Responsive Layout**<br>- ความแตกต่างของ **Dimension (สีเขียว `ABC`/ปฏิทิน/ลูกโลก)** vs **Metric (สีน้ำเงิน `123`, ค่าเริ่มต้นคือ `Sum`, ปรับค่าเฉลี่ย `AVG` ที่ `Aggregation`)**<br>- การตั้งค่า **Scorecard + Filter**, **Pie Chart + Optional metrics + Add Group + Drill Down**, **Google Maps (`Location`, `Size`, `Color metric`)**, **Bar Chart + Breakdown Dimension**, **Time Series (รูปแบบวันที่ `2026-01` / `2026-01-01`, ข้อควรระวัง `Comparison date range` กับ `Breakdown Dimension`, `Trendline`, `Reference Line`)**<br>- ตัวควบคุม **Controls 6 ชนิด** (`Drop-down list`, `Input box` กับ `Equals/Contains/Starts with`, `Slider`, `Dimension control`, `Date range control`, `Button`), การกด **Reconnect** เมื่อเพิ่มคอลัมน์ใน Sheet<br>- การทำ **Blend Data (สูงสุด 5 ตาราง)** และ **Join Operators 5 แบบ** (`Inner, Left Outer, Right Outer, Full Outer, Cross Join`) + กรณีศึกษาเชื่อม 3 ตาราง (`ข้อมูลบุคลากร` ⋈ `การเบิกจ่ายยา` ⋈ `รายชื่อยาในคลัง` ด้วย `รหัสพนักงาน` และ `รหัสยา`), การซ่อนเมนู (`Theme and layout -> Layout -> Navigation type = Hidden`) และการแชร์ 5 วิธี |
| **ตอนที่ 2** | **การสร้างสื่อสุขภาพแบบภาพเคลื่อนไหว 2 มิติ (1)** | **8 คะแนน** (8 ข้อ · ข้อ 17–24) | **คาบที่ 10** (`animaker69.pdf` 94 หน้า — **Animaker**) | - ตัวอย่างเว็บแอนิเมชัน 6 แห่ง (`Animaker, Animatron, Biteable, Vyond, Powtoon, Renderforest`), ระดับสมาชิกและพื้นที่อัปโหลดฟรี **`2 GB`**<br>- การสร้างโปรเจกต์ (`Create from Scratch`), สัดส่วนวิดีโอ (`16:9`, `1:1`, `9:16`), การจัดการสีพื้นหลัง (`Gradient -> Direction`), การเปลี่ยนโทนสีรูปฉากหลัง (`Change Color`), การสร้างฉากหลังด้วย AI (`Generate BG using AI`: `Prompt + Color + Visual Style`)<br>- การใส่ Animation ให้ข้อความ (`Enter` และ `Exit`), การสร้างตัวละคร (`Create your own character`), การตั้งค่าท่าทาง (`Action`), อารมณ์ (`Expression`), และการเคลื่อนที่พร้อมเปลี่ยนท่าทางต่อเนื่องด้วย **`ActionPlus` (กด `+` -> ลากตำแหน่ง -> กด `Apply`, แก้ไขด้วย `Edit Action` / `Replace`)**<br>- การใส่เสียงพากย์ **`Add a voice over` 3 วิธี** (`Record Voiceover`, `Text to Speech`, `Upload Voiceover`), การลดเสียงเพลงเมื่อทับเสียงพูดด้วย **`Advanced Edit` (ดึงเส้นตรงลงด้านล่าง)**, การใช้ `Property + Smart move`, มุมกล้อง `Camera Timeline` (`Static` vs `Dynamic Camera`), `Transition effect`<br>- ข้อจำกัดสำคัญของ Free user: กด **`Publish -> Download Video` ได้ไม่เกิน `2 นาที`** แต่กด **`Share` (ลิงก์/อีเมล) สร้างวิดีโอความยาวได้ `ไม่จำกัด`** |
| **ตอนที่ 3** | **การสร้างสื่อสุขภาพแบบภาพเคลื่อนไหว 2 มิติ (2)** | **8 คะแนน** (8 ข้อ · ข้อ 25–32) | **คาบที่ 11** (`synfig69.pdf` 112 หน้า + `Synfig file` — **Synfig Studio**) | - คุณสมบัติของ **Synfig Studio (v1.4.5)**: Freeware/Open-source รองรับ Linux, Mac OSX, Windows ใช้หลักการ Vector & Bitmap และใช้ทรัพยากรเครื่องต่ำ<br>- การจัดการเลเยอร์และค่า **`Z Depth` (ค่าน้อยอยู่บนสุด, ค่ามากอยู่ล่างสุด)**, การย้ายรูปสี่เหลี่ยมต้องคลิกขวาเลือก **`Group Layer`** ก่อนลากจุดสีเขียว<br>- หน้าที่ของ **จุดควบคุม 7 สี**: **เขียว** (ย้ายตำแหน่ง), **น้ำเงิน** (หมุน), **ส้ม** (ย่อ/ขยายคงสัดส่วน), **เหลืองบน** (แกน X), **เหลืองขวา** (แกน Y), **แดง** (ปรับเอียง Skew), **เทา** (ย้ายจุดหมุน Pivot point)<br>- การเปิดโหมด **`Turn on animate editing mode`**, ความเร็วเฟรม (เฟรมมาก=ช้า, เฟรมน้อย=เร็ว), **รูปแบบการเคลื่อนที่ 5 แบบ**: `Clamped` (สีส้ม-หยุดตรงจุด แนะนำ), `TCB` (สีเขียว-มีข้อเสีย **Overshoot**), `Constant` (สีแดง-สลับทันที เหมาะกับตากะพริบ/ปากพูด), `Ease In/Out` (สีน้ำเงิน), `Linear` (สีเหลือง-แข็งทื่อเหมือนหุ่นยนต์)<br>- ไฟล์โปรเจกต์ **`.sifz`** และการ Render 3 แบบ: `.avi` (`Target = Auto`), `.gif` (`Target = gif`), `.png` (`Target = png` + `Render current frame only`), การกลับด้านภาพซ้าย-ขวา (ใส่เครื่องหมาย `-` หน้าค่า Scale แกน X แล้ว **กด Enter 2 ครั้ง**)<br>- ความแตกต่างของ **`Waypoint`** vs **`Keyframe` (จดจำสถานะของทุกเลเยอร์)**, การทำปากพูดด้วย **`Group Layers into Switch` (`Active Layer Name`)**, การสร้างกระดูก **`Skeleton` (`Parent bone` ที่แกนกลาง -> `Child bone` ลำตัว/หัว/แขน ส่วนขาแยกจาก `Parent bone` แกนกลางโดยตรง -> ผูกด้วย `Link to Bone`)**, และการทำเดินวนลูปด้วย **`Time Loop` (ลบ Waypoint ของ `Offset` แล้วตั้ง `Duration = 31f`)** |
| **ตอนที่ 4** | **การเผยแพร่สื่อสุขภาพผ่านทางเครือข่ายอินเทอร์เน็ต** | **16 คะแนน** (16 ข้อ · ข้อ 33–48) | **คาบที่ 12–13** (`wordpress_org.pdf` 166 หน้า — **WordPress.org**) | - สถิติอินเทอร์เน็ตและเว็บไซต์: 75% ตัดสินความน่าเชื่อถือจากเว็บดีไซน์, สัดส่วนเข้าเว็บผ่าน **มือถือ `50.38%`** (หมวดสุขภาพค้นผ่านมือถือ 68%), **53% ออกจากเว็บมือถือที่โหลดเกิน `3 วินาที`**, องค์ประกอบสร้างเว็บ 3 ส่วน (`ตัวเว็บไซต์ + Web Hosting + Domain Name`), วิธีสร้างเว็บ 3 วิธี<br>- ส่วนแบ่งตลาด CMS (W3Techs): **WordPress อันดับ 1 (`43.3%` ของเว็บทั้งหมด / `60.7%` ของ CMS)**, รองลงมาคือ **Joomla (`1.4%`)** และ **Drupal (`0.8%` แต่เป็นนิยมในเว็บใหญ่ Top 10,000 ถึง `6–7%`)**, แนวคิด **Responsive Design**<br>- ข้อจำกัดของ Free Hosting, สเปก AwardSpace ฟรี (`1 GiB = 1024³ bytes` vs `1 GB = 1000³ bytes`), **กฎการตั้งชื่อ Domain Name 3 ข้อ** (อังกฤษ/ตัวเลข/ขีดกลาง `-` เท่านั้น ห้ามเว้นวรรค), `.com` vs `.th` (ต้องใช้เอกสาร) vs Free Subdomain<br>- ประวัติ WordPress (`27/05/2003`, ภาษา **`PHP` + ฐานข้อมูล `MySQL`/`MariaDB`**), ตารางเปรียบเทียบ **`WordPress.org` (ติดตั้งเอง อิสระเต็มที่ ไม่มีโฆษณา)** vs **`WordPress.com` (ครบวงจรแต่ฟรีมีโฆษณาและจำกัดการปรับแต่ง)**<br>- การติดตั้งผ่าน `Zacky App Installer`, URL หน้าบ้าน vs หลังบ้าน (`http://ชื่อเว็บ/wp-admin/`), ตั้งเวลา `UTC+7` ที่ `Settings -> General`, การลง Theme และตั้งค่า `Site Identity` (`Logo, Site Title, Tagline, Site Icon 512×512 px`)<br>- ตารางเปรียบเทียบ **`Post` (ข่าว/บทความตามเวลา มี `Categories` & `Tags`)** vs **`Page` (เนื้อหาคงที่ Static ไม่มี Categories/Tags ต้องผูกกับ `Menu` จึงจะแสดง)**, การทำ **เมนูย่อย (คลิกซ้ายลากเยื้องไปทางขวา)**, การทำหน้าแรกด้วยบล็อก **`Query Loop` (กรอง `Filters -> Taxonomies -> Tags`)** + ตั้งค่า `Homepage Settings -> A static page`, การจัดการ **`Widgets`** และการลบ **`Plugins` 2 ขั้นตอน (`Deactivate` ➔ `Delete`)** |
"""

chapters.append(dict(
    id='exam48',
    title='จำลองสอบปลายภาคจริง 48 ข้อ (ตามใบปะหน้า 4 ตอน · 48 คะแนน)',
    shortTitle='ตอนที่ 1 (16) + ตอนที่ 2 (8) + ตอนที่ 3 (8) + ตอนที่ 4 (16)',
    instructor='ครบทั้ง 4 ตอนตามใบปะหน้าข้อสอบ',
    partLabel='ครบทั้ง 4 ตอนตามใบปะหน้า (48 คะแนน)',
    summary=markdown(exam48_summary_md),
    checklistHtml=markdown(exam48_summary_md),
    bodyHtml='',
    questions=exam48_questions,
    filename='messageImage_1792597623562.jpg'
))

template = (ROOT / 'template.html').read_text(encoding='utf-8')
payload = json.dumps(chapters, ensure_ascii=False).replace('</', '<\\/')
html_out = template.replace('/*__DATA__*/', payload)

(ROOT / 'index.html').write_text(html_out, encoding='utf-8')
(ROOT / 'build_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

how_to_open = """วิธีเปิดใช้งานเว็บสรุปเนื้อหาและจำลองข้อสอบปลายภาค (553127-168 การพัฒนาสื่อสุขภาพ - HEALTH MEDIA DEVELOPMENT)
========================================================================================================

1. ดับเบิลคลิกเปิดไฟล์ "index.html" ในโฟลเดอร์นี้ด้วยเว็บเบราว์เซอร์ใดก็ได้ (เช่น Google Chrome, Microsoft Edge, Safari, Firefox)
   - ทำงานแบบออฟไลน์ 100% เปิดอ่านและทำข้อสอบได้ทันทีโดยไม่ต้องใช้อินเทอร์เน็ต
2. โครงสร้างการใช้งานภายในเว็บ (ออกแบบตามความต้องการ: แยกข้อสอบตามบท และวางเนื้อหาไว้อ่านด้านบนข้อสอบจำลอง):
   - แถบเมนูด้านซ้ายแยกตามบทเรียนครบทั้ง 4 ตอนตามใบปะหน้าข้อสอบ (คาบที่ 8–9 Dashboard, คาบที่ 10 Animaker, คาบที่ 11 Synfig Studio, คาบที่ 12–13 WordPress.org) และ "🎯 จำลองสอบปลายภาคจริง (48 ข้อ 48 คะแนน ตามใบปะหน้า)"
   - ในแต่ละบทเรียน: ด้านบนสุดของหน้าจะแสดง "เนื้อหาสรุปฉบับสมบูรณ์ประจำบท" เพื่อให้อ่านทบทวนก่อนสอบ และเมื่อเลื่อนลงมาด้านล่างจะพบ "แบบจำลองข้อสอบประจำบท" ต่อเนื่องกันทันที
   - ภายในส่วนข้อสอบจำลอง ยังมีกล่องพับเก็บ "เปิดดูเนื้อหาสรุปประจำบทระหว่างทำข้อสอบ" เพื่อให้เปิดดูโพยเทียบขณะทำข้อสอบข้อท้ายๆ ได้สะดวก
   - มีป้ายดาว (⭐⭐⭐ ออกสอบเน้นย้ำ, ⭐⭐ มีโอกาสออกสูง, ⭐ เก็บตกครบเนื้อหา) และปุ่มกรองเฉพาะข้อสอบ ⭐⭐⭐
   - โหมดจำลองสอบปลายภาคจริง 48 ข้อ แบ่งเป็น 4 ตอนตรงตามใบปะหน้าข้อสอบจริง (ตอนที่ 1 แดชบอร์ดข้อมูลสุขภาพ 16 ข้อ, ตอนที่ 2 ภาพเคลื่อนไหว 2 มิติ (1) Animaker 8 ข้อ, ตอนที่ 3 ภาพเคลื่อนไหว 2 มิติ (2) Synfig Studio 8 ข้อ, ตอนที่ 4 การเผยแพร่สื่อสุขภาพผ่านอินเทอร์เน็ต WordPress.org 16 ข้อ) พร้อมปุ่มสุ่มชุดข้อสอบใหม่จากคลัง 140 ข้อได้ไม่จำกัดครั้ง
"""
(ROOT / 'วิธีเปิดเว็บ.txt').write_text(how_to_open, encoding='utf-8')

# Mirror into subfolder สรุปและแนวข้อสอบ for consistency with sibling course folders
SUB = ROOT / 'สรุปและแนวข้อสอบ'
SUB.mkdir(exist_ok=True)
for fname in ['index.html', 'template.html', 'build_site.py', 'build_manifest.json', 'PRODUCT.md', 'DESIGN.md', 'วิธีเปิดเว็บ.txt']:
    shutil.copy2(ROOT / fname, SUB / fname)
for md_file in ROOT.glob('บท*.md'):
    shutil.copy2(md_file, SUB / md_file.name)

print(f'Successfully built {len(chapters)-1} chapters ({sum(len(c["questions"]) for c in chapters if c["id"]!="exam48")} questions) + 48-question Full Exam Blueprint mode!')
