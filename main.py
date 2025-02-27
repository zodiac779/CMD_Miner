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
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

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

# ✅ ใช้ Queue เก็บ nonce ที่สำเร็จ
result_queue = queue.Queue()

# ✅ ตั้งค่า Gas Price อัตโนมัติ
gas_price = w3.eth.gas_price if args.gas_price is None else w3.to_wei(args.gas_price, 'gwei')

# # ✅ ใช้ Cache เพื่อลดการเรียก Smart Contract ซ้ำซ้อน
# @lru_cache(maxsize=128)
def get_current_block():
    return int(contract.functions.currentBlock().call())

# # ✅ เพิ่มตัวแปร global `latest_block` ตั้งแต่เริ่มต้น
# latest_block = None

# # ✅ ฟังก์ชันอัปเดต current block แบบ Async
# async def update_current_block():
#     global latest_block
#     while True:
#         new_block = get_current_block()
        
#         # ✅ ตรวจสอบว่า latest_block มีค่าหรือไม่ก่อนเปรียบเทียบ
#         if latest_block is None or new_block != latest_block:
#             latest_block = new_block
#             print(f"\n🔄 New Block Detected: {latest_block}")
        
#         await asyncio.sleep(0.5)

# ✅ ฟังก์ชันคำนวณ Hash โดยใช้ sha256
def sha256(block_number, nonce):
    data = encode(['uint256', 'uint256'], [block_number, nonce])
    return hashlib.sha256(data).hexdigest()

# ✅ ฟังก์ชันสำหรับ Hash Worker (ใช้ Multi-threading)
def hash_worker(difficulty, start_nonce, step, block_number):
    minerDiff = int(2 ** (256 - difficulty))
    target = minerDiff.to_bytes(32, 'big').hex()
    
    nonce = start_nonce
    start_time = time.time()
    last_display_time = start_time  # ✅ กำหนดค่าเริ่มต้นก่อนใช้

    while True:
        hash_val = sha256(block_number, nonce)

        if hash_val < target:  # ✅ เปรียบเทียบ int กับ int
            elapsed_time = time.time() - start_time
            result_queue.put((nonce, hash_val))
            print(f"\n✅ Block Mined! Nonce: {nonce}, Hash: {hash_val}")
            print(f"Time Taken: {elapsed_time:.2f} seconds")
            return
        
        nonce += step  # ✅ กระโดดข้ามค่า nonce ตามจำนวน threads

        # ✅ อัปเดต Hash Rate ทุก 1 วินาที
        current_time = time.time()
        if current_time - last_display_time > 1:
            print(f"⚡ Current hash rate: {nonce / (current_time - start_time):.2f} H/s", end="\r", flush=True)
            last_display_time = current_time  # ✅ อัปเดตค่าล่าสุด

# ✅ ฟังก์ชันขุด Block โดยใช้ ThreadPoolExecutor
def mine_block(difficulty, block_number, start_nonce=0):
    threads = []
    num_threads = args.threads
    nonce_range = 2**32  # ✅ ช่วง nonce สูงสุด

    for i in range(num_threads):
        thread_nonce_start = start_nonce + i * (nonce_range // num_threads)  # ✅ กระจาย nonce ให้แต่ละ thread
        t = threading.Thread(target=hash_worker, args=(difficulty, thread_nonce_start, num_threads, block_number))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    if not result_queue.empty():
        return result_queue.get()
    return None, None

# ✅ ฟังก์ชันส่ง Transaction
async def send_transaction(provider, signer, tx_data):
    tx_data['nonce'] = provider.eth.get_transaction_count(signer.address)

    # ✅ ตรวจสอบว่าเครือข่ายรองรับ EIP-1559 หรือไม่
    if provider.eth.chain_id in [1, 5, 137, 8899]:  # ✅ Ethereum Mainnet, Goerli, Polygon
        priority_fee = provider.eth.max_priority_fee  # ✅ ใช้ค่าจากตลาด
        base_fee = provider.eth.gas_price  # ✅ คำนวณค่าธรรมเนียมเบื้องต้น
        
        tx_data['maxPriorityFeePerGas'] = priority_fee
        tx_data['maxFeePerGas'] = base_fee + priority_fee  # ✅ maxFeePerGas ต้องมากกว่า Priority Fee
    else:
        tx_data['gasPrice'] = provider.eth.gas_price  # ✅ ใช้ gasPrice สำหรับเครือข่ายที่ยังรองรับ

    try:
        signed_tx = signer.sign_transaction(tx_data)
        print(f"📤 Submitting Transaction...", end="\r", flush=True)
        tx_hash = provider.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"✅ Tx Hash: 0x{tx_hash.hex()}")

        # ✅ รอให้ TX ได้รับ Confirmations ก่อนเริ่มขุด Block ใหม่
        while True:
            await asyncio.sleep(1)
            try:
                tx_receipt = provider.eth.get_transaction_receipt(tx_hash)

                if tx_receipt:
                    block_number = tx_receipt['blockNumber']
                    current_block_number = provider.eth.block_number
                    confirmations = current_block_number - block_number + 1  # ✅ คำนวณ Confirmations
                    sys.stdout.write("\033[K")
                    print(f"🛠️ Confirmations: {confirmations}/3", end="\r", flush=True)
                    
                    if confirmations >= 1:
                        print(f"✅ Transaction Confirmed with {confirmations} Confirmations!")
                        break  # ✅ ออกจากลูปเมื่อ Confirmations >= 3
                else:
                    sys.stdout.write("\033[K")
                    print(f"⏳ Waiting for TX to be Mined...", end="\r", flush=True)
            except:
                sys.stdout.write("\033[K")
                print(f"⏳ Waiting RPC receipt", end="\r", flush=True)
                continue
        return tx_hash
    except Exception as e:
        print(f"❌ Transaction Failed: {e}")
        return None

async def wait_for_new_block(current_block):
    print("\n⏳ Waiting for new block to start mining...", end="\r", flush=True)
    while True:
        await asyncio.sleep(1)
        new_block = get_current_block()
        if new_block > current_block:
            print(f"\n🔄 New Block Detected: {new_block}! Restarting mining...\n")
            return new_block


# ✅ ฟังก์ชันจำลองการขุด
async def simulate_mining(signer, _index, _nftId):
    while True:
        block_number = get_current_block()
        current_difficulty = int(contract.functions.currentDifficulty().call())

        miner_diff = max(1, int(current_difficulty - ((_nftId % 100000) // 100)))

        print(f"⛏️ Current Block: {block_number} | Difficulty: {miner_diff}")

        nonce, hash_val = mine_block(miner_diff, block_number)
        if nonce is None:
            await asyncio.sleep(1)
            continue
        
        print("⏳ Waiting for Submit Solve...\n")
        await send_transaction(w3, signer, contract.functions.submitPoW(_index, _nftId, nonce, f"0x{hash_val}").build_transaction({"from": signer.address}))
        
        # # ✅ รอให้ Blockchain อัปเดต Block ก่อนเริ่มขุดใหม่
        # block_number = await wait_for_new_block(block_number)
# ✅ อ่านไฟล์ Wallet และเริ่มการขุด
async def main():
    try:
        with open(args.wallet, 'r') as fd:
            json_data = json.load(fd)
        print(f'🔑 Wallet Address: 0x{json_data["address"]}')
        password = getpass('🔓 Unlock wallet: ')
    except:
        print('❌ Error reading wallet.')
        sys.exit()

    try:
        account = w3.eth.account.from_key(w3.eth.account.decrypt(json_data, password))
    except:
        print('❌ Unlock wallet failed.')
        sys.exit()

    # asyncio.create_task(update_current_block())  # ✅ รันเช็คบล็อกแบบ Async
    await simulate_mining(account, args.nft_index, args.nft_id)

if __name__ == "__main__":
    asyncio.run(main())
