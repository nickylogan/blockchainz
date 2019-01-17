from transaction import Wallet, Transaction, TransactionOutput
from blockchain import Blockchain, Block
import time

def main():
    bc = Blockchain()

    walletA = Wallet('A')
    walletB = Wallet('B')
    coinbase = Wallet('C')
    
    genesis_trx = Transaction(coinbase.public_key, walletA.public_key, 1000000, None)
    genesis_trx.generate_signature(coinbase.private_key, coinbase.password)
    genesis_trx.transaction_id = '0'
    genesis_trx.outputs.append(TransactionOutput(genesis_trx.recipient, genesis_trx.value, genesis_trx.transaction_id))
    bc.genesis_trx = genesis_trx
    bc.UTXOs[bc.genesis_trx.outputs[0].id] = bc.genesis_trx.outputs[0]

    print('Creating and mining genesis block...')
    genesis = Block('0')
    genesis.add_transaction(genesis_trx)
    bc.add(genesis)

    f=open("time.csv", "w+")

    for i in range(1000000):
        print("%d: " % i, end='')
        start = time.time()
        block = Block(bc.get_last_hash())
        # print("Wallet A's balance is:", walletA.get_balance())
        # print("Wallet A is attempting to send funds(1) to Wallet B...")
        block.add_transaction(walletA.send_funds(walletB.public_key, 1))
        bc.add(block)
        end = time.time()
        f.write(("%d,%f\n" % (i, end-start)))
        # print("Wallet A's balance is:", walletA.get_balance())
        # print("Wallet B's balance is:", walletB.get_balance())

    print("Wallet B's balance is:", walletB.get_balance())
    print("Wallet B is attempting to send funds(1000000) to Wallet A...")
    
    start = time.time()
    block = Block(bc.get_last_hash())
    block.add_transaction(walletB.send_funds(walletA.public_key, 1000000))
    bc.add(block)
    end = time.time()

    print("Wallet A's balance is:", walletA.get_balance())
    print("Wallet B's balance is:", walletB.get_balance())

    print("Time elapsed: %fs" % (end-start))

    bc.is_valid()

    f.close()

if __name__ == "__main__":
    main()