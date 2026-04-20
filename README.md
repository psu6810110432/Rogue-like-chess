# ♟️ ROGUELIKE CHESS — Enter the Dark Battlefield

> เกมหมากรุกที่ผสมผสานกลิ่นอายความเป็น Roguelike เข้าไปอย่างลงตัว ด้วย concept All or nothing 

> พัฒนาด้วย Python + Kivy

---

## 👥 ทีมพัฒนา

| รหัสนักศึกษา | ชื่อ-นามสกุล | หน้าที่รับผิดชอบ |
|---|---|---|
| 6810110220 | นายพรหมธาดา คูนิอาจ | Setup Base Chess, เขียนระบบและออกแบบแผนที่, UX/UI, Sound Effect, Testing, ระบบ Event และระบบ AI |
| 6810110432 | นายอิศม์อนีติ เพ็งแจ่ม | เขียนระบบ Logic เกม, ระบบการ Crash, ระบบเผ่าพันธุ์, ระบบไอเทม และวาด Art ของเกมและ ปรับสมดุลเกม (Balance) |

---

## 🎮 เกมนี้คืออะไร?

**ROGUELIKE CHESS** ไม่ใช่แค่เกมกระดานธรรมดา แต่คือเกมหมากรุกที่ถูกยกระดับด้วยการเพิ่ม **ระบบเผ่าพันธุ์ (Tribes)**, **สภาพแวดล้อม (Maps)**, **ระบบไอเทม (Items)** และเปลี่ยนการกินหมากแบบเดิมๆ ให้กลายเป็นการต่อสู้ที่ต้องใช้ค่าสถานะจริงในการตัดสินผลลัพธ์ **(Crash System)**

---

## ✨ ฟีเจอร์

- 🗺️ **4 Strategic Battlefields** — เลือกสนามรบได้ 4 ธีมที่แตกต่างกัน ได้แก่ *Classic, Enchanted Forest, Desert Ruins* และ *Frozen Tundra*
- ⚔️ **Divine Order & Dark Abyss (Tribes)** — เลือกเล่นจาก 4 เผ่าพันธุ์ที่มีเอกลักษณ์เฉพาะตัว: *Medieval Knights, Ayothaya, Demon* และ *Heaven*
- 💥 **Combat & Crash System** — การกินหมากคือ "การปะทะ" ต้องคำนวณผลลัพธ์ระหว่างผู้โจมตี (Attacker) และผู้ตั้งรับ (Defender) ว่าใครจะเป็นผู้รอดชีวิต
- 🎒 **Rogue Inventory & Items** — ระบบสุ่มดรอปไอเทมเมื่อคุณชนะการปะทะ เพิ่มความได้เปรียบและพลิกแพลงสถานการณ์
- 🤖 **Intelligent AI** — ระบบสมองกลที่รองรับทั้งโหมดสุ่มเดิน (Random Move) และโหมดเน้นการไล่ล่ากินหมาก (Priority Capture)

---

## 🚀 วิธีติดตั้งและรันโปรแกรม

**ความต้องการของระบบ:** `Python 3.12.10`

```bash
# 1. สร้าง Virtual Environment
python -m venv venv

# 2. เปิดใช้งาน (Activate) Virtual Environment
# สำหรับ Windows:
venv\Scripts\activate
# สำหรับ Linux/Mac:
source venv/bin/activate

# 3. ติดตั้งไลบรารีที่จำเป็น
pip install kivy pytest

# 4. เริ่มเข้าสู่สมรภูมิ!
python main.py

ROGUELIKE-CHESS/
├── logic/           # ระบบกระดาน (Board), หมาก (Pieces), Crash Logic, Item Logic และ AI Logic
├── screens/         # ส่วนการแสดงผลและ UI ทั้งหมดโดยใช้ Kivy
├── tests/           # รวมไฟล์ทดสอบระบบอัตโนมัติ (Automated Testing) ทั้งหมด
└── main.py          # จุดเริ่มต้นการรันโปรแกรม
