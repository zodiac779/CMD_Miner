# 🚀 CommuDAO.xyz Mining Simulation

## ▶️ วิธีใช้งาน

### **1️⃣ ติดตั้งไลบรารีที่จำเป็น**
```bash
pip install -r requirements.txt
```

---

### **2️⃣ รันโปรแกรม**
สามารถตั้งค่าชื่อ **Miner** และจำนวน **Threads** ที่ใช้ขุดได้ เช่น:
```bash
python main.py --miner Capy --threads 4
```
🔹 **ตัวอย่าง:**  
- `--miner Capy` → ตั้งชื่อ Miner เป็น "Capy"  
- `--threads 4` → ใช้ 4 Threads ในการขุด  

📌 **ถ้าไม่ใส่ค่า จะใช้ค่าเริ่มต้น:**  
- **Miner Default:** `"Capy"`  
- **Threads Default:** `4`

---

### **3️⃣ การแสดงผล**
เมื่อรันโปรแกรม จะเห็นข้อมูลประมาณนี้:
```bash
🚀 Starting Miner: Capy
🔄 Using 4 Threads

Current Block to Mine: 123456 | Difficulty: 5
Current hash rate: 1.32 MH/s
✅ Block Mined! Nonce: 425678, Hash: 00000a12b34c...
Time Taken: 8.50 seconds
Hash Rate: 1.50 MH/s

Server Response: {"status": "accepted"}
Waiting for new block update...
```

---

## ⚡ **หมายเหตุ**
- โค้ดนี้เป็น **Simulation** ไม่ได้ขุดเหรียญ จริงๆ  
- ใช้ **Web3** ในการดึงข้อมูลบล็อกจาก Smart Contract  
- ใช้ **Multi-threading** เพื่อเพิ่มความเร็วในการขุด  

---

## 📝 **เครดิต**
พัฒนาโดย **Capy Dev Team** 🦫  
```
