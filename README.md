# 🚀 CommuDAO Mining

## 📖 คำอธิบาย
โปรเจกต์นี้เป็นระบบ **Proof of Work (PoW) Mining** สำหรับ **Smart Contract `FieldsHook002.sol`**  
โดยใช้ **Python + Web3.py** ในการเชื่อมต่อและส่ง `submitPoW` เพื่อขุดบล็อกและรับรางวัล **Token Reward**  

✅ **รองรับ Multi-threading** เพื่อเพิ่มความเร็วในการขุด  
✅ **อ่านค่า Block และ Difficulty จาก Smart Contract**  
✅ **ตรวจสอบ Private Key และ Sign Transaction ก่อนส่งไปยัง Blockchain**  
✅ **บันทึกค่า nonce ล่าสุด เพื่อรองรับการทำงานต่อจากเดิม**  

---

## 🔧 **การติดตั้ง**
### **1️⃣ ติดตั้ง Python และไลบรารีที่จำเป็น**
ใช้ Python 3.8+ และติดตั้งไลบรารีที่จำเป็น
```bash
pip install -r requirements.txt
```
📌 **`requirements.txt` ควรมีไลบรารีดังนี้**
```
web3
requests
eth-abi
```

---

## ▶️ **วิธีใช้งาน**
### **1️⃣ เตรียมไฟล์ Wallet**
ต้องมีไฟล์ Wallet ที่เก็บ Private Key ของคุณ **(ในรูปแบบ JSON Encrypted Wallet)**  
> **ตัวอย่างโครงสร้างไฟล์ `wallet.json`**
```json
{
  "address": "0xYourAddress",
  "crypto": { ... },
  "id": "wallet-id",
  "version": 3
}
```
⚠️ **ห้ามใช้ Private Key ตรงๆ!** ให้ใช้ไฟล์ Wallet แทน

---

### **2️⃣ รันโปรแกรม**
สามารถตั้งค่าการขุดได้ตามต้องการ เช่น:
```bash
python main.py --wallet wallet.json --nft_index 1 --nft_id 1001 --threads 4
```
🔹 **อธิบาย Arguments:**  
- `--wallet wallet.json` → ระบุไฟล์ Wallet สำหรับ Sign Transaction  
- `--nft_index 1` → Index ของ NFT ที่ใช้ขุด  
- `--nft_id 1001` → ID ของ NFT ที่ใช้ขุด  
- `--threads 4` → ใช้ **4 Threads** ในการขุด (ค่าปกติคือ 1)  

📌 **หากไม่ระบุ `--threads` จะใช้ค่าเริ่มต้น = 1**

---

### **3️⃣ การแสดงผล**
เมื่อรันโปรแกรม จะเห็นข้อมูลประมาณนี้:
```bash
🚀 Starting Miner: 1001
🔄 Using 4 Threads

Current Block to Mine: 123456 | Difficulty: 5
Current hash rate: 1.32 MH/s
✅ Block Mined! Nonce: 425678, Hash: 0x123abc...
Time Taken: 8.50 seconds
Hash Rate: 1.50 MH/s

Waiting for Submit Solve...
Tx Hash: 0xabcdef123456789...
```

---

## ⚡ **หมายเหตุ**
- **ต้องมี NFT ที่ Stake ไว้** บน Smart Contract ก่อนจึงจะสามารถขุดได้  
- **ค่า Difficulty จะปรับอัตโนมัติทุกๆ 10 Blocks**  
- **ใช้ระบบ Multi-threading ในการขุด** แต่หาก `--threads` สูงเกินไป อาจทำให้ CPU ทำงานหนัก  

---

## 📝 **เครดิต**
พัฒนาโดย **Nicky99** 🦫  
```
