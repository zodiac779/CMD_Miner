# -*- coding: utf-8 -*-
import json
import time
import hashlib
import asyncio
import threading
import queue
import sys
import argparse
import os
from web3 import Web3
from eth_abi import encode
from getpass import getpass

# ✅ โหลด argument จาก command line
parser = argparse.ArgumentParser(description="CommuDAO Mining")
parser.add_argument("--wallet", type=str, required=True, help="ไฟล์ wallet สำหรับ Submit Solve")
parser.add_argument("--nft_index", type=int, required=True, help="Row Index ของ NFT")
parser.add_argument("--nft_id", type=int, required=True, help="ID ของ NFT")
parser.add_argument("--threads", type=int, default=1, help="จำนวน threads ที่ใช้ขุด (default: 1)")
parser.add_argument("--gas_price", type=int, default=None, help="Gas Price ที่ใช้ในการส่ง Transaction (Gwei)")
args = parser.parse_args()

# ✅ แสดงข้อมูล Miner และจำนวน Threads ก่อนเริ่มขุด
print(f"\n🚀 Starting Miner: NFT ID {args.nft_id}")
print(f"🔄 Using {args.threads} Threads\n")

# ✅ โหลด ABI จากไฟล์
abi_file = "abi.json"
if os.path.exists(abi_file):
    with open(abi_file) as f:
        DaAbi = json.load(f)
else:
    raise FileNotFoundError(f"❌ ไม่พบไฟล์ {abi_file}! โปรดตรวจสอบและลองใหม่")

# ✅ ตั้งค่า Web3 client
w3 = Web3(Web3.HTTPProvider("https://rpc-l1.inan.in.th"))
contract_address = '0x8652549D215E3c4e30fe33faa717a566E4f6f00C'
contract = w3.eth.contract(address=contract_address, abi=DaAbi)

# ✅ ใช้ Event สำหรับหยุด Threads เมื่อขุดสำเร็จ
stop_event = threading.Event()
result_queue = queue.Queue()
console_lock = threading.Lock()

# ✅ ฟังก์ชันดึง Block ปัจจุบัน
def get_current_block():
    try:
        return int(contract.functions.currentBlock().call())
    except Exception as e:
        print(f"⚠️ RPC Error: {e}. Retrying...")
        time.sleep(1)
        return get_current_block()

# ✅ ฟังก์ชันช่วยแปลง hash rate ให้ดูอ่านง่ายขึ้น
def format_hash_rate(rate):
    if rate >= 1e6:
        return f"{rate / 1e6:.2f} MH/s"
    elif rate >= 1e3:
        return f"{rate / 1e3:.2f} kH/s"
    else:
        return f"{rate:.2f} H/s"

# ✅ ฟังก์ชันคำนวณ Hash โดยใช้ sha256
def sha256(block_number, nonce):
    data = encode(['uint256', 'uint256'], [block_number, nonce])
    return hashlib.sha256(data).hexdigest()

# ✅ ฟังก์ชันสำหรับ Hash Worker
def hash_worker(difficulty, start_nonce, step, block_number, thread_name):
    target = int(2 ** (256 - difficulty))

    nonce = start_nonce
    start_time = time.time()
    last_display_time = start_time

    while not stop_event.is_set():
        hash_val = sha256(block_number, nonce)
        hash_int = int(hash_val, 16)

        if hash_int < target:
            elapsed_time = time.time() - start_time
            result_queue.put((nonce, hash_val, elapsed_time))
            stop_event.set()
            return

        nonce += step

        # ✅ อัปเดต Hash Rate ทุก 1 วินาที
        current_time = time.time()
        if current_time - last_display_time > 1:
            with console_lock:
                sys.stdout.write("\033[K")
                print(f"⚡Thread {thread_name} Hash rate: {format_hash_rate((nonce - start_nonce) / (current_time - start_time))}", end="\r", flush=True)
            last_display_time = current_time

# ✅ ฟังก์ชันขุด Block
def mine_block(difficulty, block_number, start_nonce=0):
    threads = []
    stop_event.clear()
    
    for i in range(args.threads):
        thread_nonce_start = start_nonce + i
        t = threading.Thread(target=hash_worker, args=(difficulty, thread_nonce_start, args.threads, block_number, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=1)  # ✅ ป้องกันการรอ Thread นานเกินไป

    if not result_queue.empty():
        return result_queue.get()
    return None, None, None

# ✅ ฟังก์ชันส่ง Transaction
async def send_transaction(provider, signer, tx_data):
    tx_data['nonce'] = provider.eth.get_transaction_count(signer.address)

    if provider.eth.chain_id in [1, 5, 137, 8899]:
        priority_fee = provider.eth.max_priority_fee
        base_fee = provider.eth.gas_price
        tx_data['maxPriorityFeePerGas'] = priority_fee
        tx_data['maxFeePerGas'] = base_fee + priority_fee
    else:
        tx_data['gasPrice'] = provider.eth.gas_price

    try:
        signed_tx = signer.sign_transaction(tx_data)
        tx_hash = provider.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"✅ Tx Hash: 0x{tx_hash.hex()}")

        start_time = time.time()
        while True:
            await asyncio.sleep(1)
            try:
                tx_receipt = provider.eth.get_transaction_receipt(tx_hash)
                if tx_receipt:
                    confirmations = provider.eth.block_number - tx_receipt['blockNumber'] + 1
                    print(f"🛠️ Confirmations: {confirmations}/3", end="\r", flush=True)
                    if confirmations >= 1:
                        print(f"\n✅ Transaction Confirmed with {confirmations} Confirmations!")
                        break
            except:
                print(f"⏳ Waiting RPC receipt...", end="\r", flush=True)
                continue

            if time.time() - start_time > 60:
                print("\n🔄 Transaction stuck. Retrying...")
                return await send_transaction(provider, signer, tx_data)

        return tx_hash
    except Exception as e:
        print(f"❌ Transaction Failed: {e}")
        return None

# ✅ ฟังก์ชันจำลองการขุด
async def simulate_mining(signer, _index, _nftId):
    last_block_number = None

    while True:
        block_number = get_current_block()
        if block_number == last_block_number:
            await asyncio.sleep(1)
            continue

        last_block_number = block_number
        current_difficulty = int(contract.functions.currentDifficulty().call())
        miner_diff = max(1, int(current_difficulty - ((_nftId % 100000) // 100)))

        print(f"⛏️ Current Block: {block_number} | Difficulty: {miner_diff}")

        nonce, hash_val, elapsed_time = mine_block(miner_diff, block_number)
        if nonce is None:
            await asyncio.sleep(1)
            continue

        print(f"\n✅ Block Mined! Nonce: {nonce}, Hash: {hash_val}")
        print(f"Time Taken: {elapsed_time:.2f} seconds")
        print("⏳ Waiting for Submit Solve...\n")

        await send_transaction(w3, signer, contract.functions.submitPoW(_index, _nftId, nonce, f"0x{hash_val}").build_transaction({"from": signer.address}))

# ✅ อ่านไฟล์ Wallet และเริ่มการขุด
async def main():
    try:
        with open(args.wallet, 'r') as fd:
            json_data = json.load(fd)
        print(f'🔑 Wallet Address: 0x{json_data["address"]}')
        password = getpass('🔓 Unlock wallet: ')
        account = w3.eth.account.from_key(w3.eth.account.decrypt(json_data, password))
    except:
        print('❌ Error reading wallet or incorrect password.')
        sys.exit()

    await simulate_mining(account, args.nft_index, args.nft_id)

if __name__ == "__main__":
    asyncio.run(main())
