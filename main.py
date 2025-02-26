# -*- coding: utf-8 -*-
import json
import time
import hashlib
import requests
import threading
import queue
import sys
import argparse
from web3 import Web3
import os

# ✅ โหลด argument จาก command line
parser = argparse.ArgumentParser(description="Bitcoin Mining Simulation")
parser.add_argument("--miner", type=str, default="Capy", help="ชื่อของ miner (default: Capy)")
parser.add_argument("--threads", type=int, default=4, help="จำนวน threads ที่ใช้ขุด (default: 4)")
args = parser.parse_args()

# ✅ แสดงข้อมูล Miner และจำนวน Threads ก่อนเริ่มขุด
print(f"\n🚀 Starting Miner: {args.miner}")
print(f"🔄 Using {args.threads} Threads\n")

# ✅ โหลด ABI จากไฟล์ (ตรวจสอบก่อนว่าไฟล์มีอยู่)
abi_file = "abi.json"
if os.path.exists(abi_file):
    with open(abi_file) as f:
        DaAbi = json.load(f)
else:
    raise FileNotFoundError(f"❌ ไม่พบไฟล์ {abi_file}! โปรดตรวจสอบและลองใหม่")

# ✅ ตั้งค่า Web3 client ด้วย RPC URL ที่กำหนดไว้
w3 = Web3(Web3.HTTPProvider("https://rpc-l1.inan.in.th"))

# ✅ กำหนด address ของ smart contract
contract_address = '0x5087e30Ce9307D1e087400B367C2eb1c6804f090'
contract = w3.eth.contract(address=contract_address, abi=DaAbi)

# ✅ ตัวแปร global สำหรับเก็บ current block ล่าสุด
latest_block = None
progress_file = "currentblock.json"

# ✅ ใช้ queue เก็บ nonce ที่สำเร็จ
result_queue = queue.Queue()

# ✅ ฟังก์ชันช่วยแปลง hash rate ให้ดูอ่านง่ายขึ้น
def format_hash_rate(rate):
    if rate >= 1e6:
        return f"{rate / 1e6:.2f} MH/s"
    elif rate >= 1e3:
        return f"{rate / 1e3:.2f} kH/s"
    else:
        return f"{rate:.2f} H/s"

# ✅ ฟังก์ชันบันทึก block number และ nonce ลงไฟล์ JSON
def save_current_progress(block_number, nonce):
    with open(progress_file, "w") as f:
        json.dump({"block_number": block_number, "nonce": nonce}, f)

# ✅ ฟังก์ชันโหลดค่า nonce ล่าสุดจากไฟล์ JSON
def load_last_nonce():
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r") as f:
                data = json.load(f)
                return data.get("block_number"), data.get("nonce", 0)
        except json.JSONDecodeError:
            pass  # ถ้าไฟล์เสียหาย ให้ขุดจาก nonce 0 ใหม่
    return None, 0  # ถ้าไม่มีไฟล์ ให้เริ่มใหม่จาก nonce 0

# ✅ ฟังก์ชันอัปเดต current block แบบ background
def update_current_block():
    global latest_block
    while True:
        try:
            latest_block = int(contract.functions.currentBlock().call())
        except Exception as e:
            print("Error updating current block:", e)
        time.sleep(1)  # ตรวจสอบทุกวินาที

# ✅ ฟังก์ชันสำหรับ Hash Worker (ขุดโดยใช้ Multi-threading)
def hash_worker(block_data, difficulty, start_nonce, step, block_number):
    target = "0" * difficulty
    nonce = start_nonce
    start_time = time.time()

    while True:
        # คำนวณ hash
        hash_val = hashlib.sha256((block_data + str(nonce)).encode()).hexdigest()
        if hash_val.startswith(target):
            elapsed_time = time.time() - start_time
            hash_rate = nonce / elapsed_time if elapsed_time > 0 else 0
            result_queue.put((nonce, hash_val))
            print(f"\n✅ Block Mined! Nonce: {nonce}, Hash: {hash_val}")
            print(f"Time Taken: {elapsed_time:.2f} seconds")
            print(f"Hash Rate: {format_hash_rate(hash_rate)}\n")
            return
        
        nonce += step  # ใช้ step เพื่อให้แต่ละ thread คำนวณ nonce ต่างกัน

        # ✅ ทุก ๆ **1,000,000 nonce** ให้เช็คว่ามี block ใหม่หรือยัง
        if nonce % 1_000_000 == 0:
            if latest_block is not None and latest_block != block_number:
                print(f"\n❌ Block {block_number} ถูกขุดไปแล้ว! (Last nonce: {nonce}) ยกเลิกการขุดและเริ่มรอบใหม่\n")
                return

            # บันทึกค่า nonce ลงไฟล์
            save_current_progress(block_number, nonce)

            # ✅ ล้างบรรทัดก่อนแสดงค่า Hash Rate
            sys.stdout.write("\033[K")
            print(f"Current hash rate: {format_hash_rate(nonce / (time.time() - start_time))}", end="\r", flush=True)

# ✅ ฟังก์ชันหลักสำหรับการขุด
def mine_block(block_data, difficulty, block_number, start_nonce=0):
    threads = []
    for i in range(args.threads):
        t = threading.Thread(target=hash_worker, args=(block_data, difficulty, start_nonce + i, args.threads, block_number))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # ดึงค่า nonce และ hash ที่ขุดสำเร็จจาก Queue
    if not result_queue.empty():
        return result_queue.get()
    return None, None

# ✅ ฟังก์ชันจำลองการขุด
def simulate_mining():
    while True:
        # อ่านข้อมูล block number และความยากจาก smart contract
        block_number = int(contract.functions.currentBlock().call())
        difficulty = int(contract.functions.currentDifficulty().call())

        # โหลด nonce ล่าสุดจากไฟล์ ถ้าเป็น block เดิมให้ใช้ค่า nonce ที่บันทึกไว้
        last_block, last_nonce = load_last_nonce()
        start_nonce = last_nonce if last_block == block_number else 0
        
        print(f"Current Block to Mine: {block_number} | Difficulty: {difficulty}")

        block_data = f"Block-{block_number}"
        nonce, hash_val = mine_block(block_data, difficulty, block_number, start_nonce)
        
        # ถ้า mining ถูกยกเลิกเพราะ block ถูกขุดไปแล้ว ให้วนลูปรอ block ใหม่
        if nonce is None:
            time.sleep(1)
            continue

        payload = {
            "miner": args.miner,  # ✅ ใช้ค่าชื่อ miner จาก arguments
            "blockNumber": block_number,
            "nonce": nonce,
            "hash": hash_val
        }

        try:
            response = requests.post("http://mining-hook-test.vercel.app/submit", json=payload)
            data = response.json()
            print("Server Response:", data)
        except Exception as e:
            print("Error Submitting Block:", e)

        # รอจนกว่า smart contract จะอัปเดท block number ใหม่
        print("Waiting for new block update...\n")
        while True:
            new_block_number = int(contract.functions.currentBlock().call())
            if new_block_number != block_number:
                print(f"New block detected: {new_block_number}. Restarting mining...\n")
                break
            time.sleep(1)

if __name__ == "__main__":
    # ✅ เริ่ม thread สำหรับอัปเดต current block แบบ background
    block_thread = threading.Thread(target=update_current_block, daemon=True)
    block_thread.start()
    
    simulate_mining()
