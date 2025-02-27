# 📌 CommuDAO Mining - SHA256 PoW Miner

## 📖 คำอธิบาย
CommuDAO Mining เป็นโปรแกรมขุด SHA256 Proof-of-Work (PoW) ที่ใช้ **Python** และ **Web3.py** เพื่อขุด Block และส่งผลลัพธ์ไปยัง Smart Contract บน Blockchain

---

## ⚙️ **ความต้องการของระบบ**
### ✅ **ติดตั้ง Python และไลบรารีที่จำเป็น**
ต้องใช้ **Python 3.8+** และไลบรารีดังต่อไปนี้:

```bash
pip install web3 eth-abi argparse asyncio
```

---

## 🚀 **วิธีใช้งาน**

### ✅ **1. เตรียม Wallet (ไฟล์ JSON)**
ต้องใช้ไฟล์ **Keystore JSON** ของ Ethereum Wallet เพื่อส่ง Transaction ไปยัง Blockchain

> **ตัวอย่างไฟล์ wallet.json**
```json
{
    "address": "your_wallet_address",
    "crypto": {...},
    "id": "unique_id",
    "version": 3
}
```

---

### ✅ **2. รันโปรแกรมขุด**
ให้ระบุไฟล์ Wallet, NFT Index, NFT ID และจำนวน Threads ที่ใช้ขุด

```bash
python main.py --wallet wallet.json --nft_index 1 --nft_id 1001 --threads 4
```

#### 🛠 **อธิบาย Parameter**
| Argument        | คำอธิบาย |
|----------------|----------|
| `--wallet`     | ไฟล์ Wallet JSON ที่ใช้ลงชื่อ Transaction |
| `--nft_index`  | หมายเลข Index ของ NFT ที่ใช้ขุด |
| `--nft_id`     | หมายเลข ID ของ NFT |
| `--threads`    | จำนวน Threads ที่ใช้ในการขุด (ค่าเริ่มต้น: 1) |
| `--gas_price`  | Gas Price ที่ใช้ส่ง Transaction (Gwei) (ค่าเริ่มต้น: ใช้ RPC ค่า Default) |

---

### ✅ **3. การแสดงผลใน Console**

เมื่อเริ่มขุด โปรแกรมจะแสดงข้อมูลดังนี้:
```plaintext
🚀 Starting Miner: NFT ID 1001
🔄 Using 4 Threads
⛏️ Current Block: 500 | Difficulty: 3
⚡Thread 0 Hash rate: 250.5 H/s
⚡Thread 1 Hash rate: 260.3 H/s
📤 Submitting Transaction...
✅ Tx Hash: 0x123abc456...
🛠️ Confirmations: 1/3
✅ Transaction Confirmed with 3 Confirmations!
🔄 New Block Detected: 501! Restarting mining...
```

---

## 🔧 **การแก้ไขปัญหา**

| ปัญหา | วิธีแก้ไข |
|--------|----------|
| **`Transaction Failed: already known`** | Transaction ถูกส่งซ้ำ ให้รอ Confirmations ให้ครบ |
| **`RPC Error: -32000 gas required exceeds allowance`** | เพิ่มค่า Gas Limit หรือใช้ `--gas_price` กำหนดค่า Gas |
| **`Invalid Wallet Password`** | ตรวจสอบรหัสผ่านของไฟล์ Keystore JSON |

---

## 📜 **License**
MIT License - สามารถใช้ได้ฟรีและแก้ไขโค้ดได้ตามต้องการ 🚀

