from hashlib import sha256
import time
import json
from utils import apply_sha256, get_merkle_root, todict


class Block:
    def __init__(self, previoushash):
        self.previoushash = previoushash
        self.timestamp = time.time()

        self.nonce = 0
        self.transactions = []
        self.merkle_root = ''

        self.hash = self.calculate_hash()

    def calculate_hash(self):
        digest = apply_sha256(
            self.previoushash, self.timestamp, self.nonce, self.merkle_root)
        return digest

    def mine_block(self, difficulty):
        self.merkle_root = get_merkle_root(self.transactions)
        target = "0"*difficulty
        while not self.hash[:difficulty] == target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print('Block mined!:', self.hash)

    def add_transaction(self, transaction):
        if transaction == None:
            return False
        if self.previoushash != '0':
            if not transaction.process_transaction():
                # print('Transaction failed to process. Discarded')
                return False
        self.transactions.append(transaction)
        # print('Transaction successfully added to block')
        return True

    def __str__(self):
        return json.dumps(self.__dict__)


class Blockchain:
    class __Blockchain:
        difficulty = 0
        minimum_transaction = .1

        def __init__(self):
            self.chain = []
            self.UTXOs = {}
            self.genesis_trx = None

        def __str__(self):
            return json.dumps(todict(self), indent=2)

        def add(self, block):
            block.mine_block(Blockchain.__Blockchain.difficulty)
            self.chain.append(block)

        def __getitem__(self, key):
            return self.chain[key]

        def is_valid(self):
            hashtarget = "0"*Blockchain.__Blockchain.difficulty
            tempUTXOs = {}
            tempUTXOs[self.genesis_trx.outputs[0].id] = self.genesis_trx.outputs[0]

            for i in range(1, len(self.chain)):
                currblock = self.chain[i]
                prevblock = self.chain[i-1]
                if currblock.hash != currblock.calculate_hash():
                    print('# Hashes not equal')
                    return False
                if currblock.previoushash != prevblock.hash:
                    print('# Previous hashes not equal', currblock.previoushash, prevblock.hash)
                    return False
                if currblock.hash[:Blockchain.__Blockchain.difficulty] != hashtarget:
                    print('# Block not mined')
                    return False

                temp_output = None
                for t in range(len(currblock.transactions)):
                    curr_trx = currblock.transactions[t]

                    if not curr_trx.verify_signature():
                        print('# Signature on transaction(%d) is invalid' % t)
                        return False
                    if curr_trx.get_inputs_value() != curr_trx.get_outputs_value():
                        print(
                            '# Inputs are not equal to outputs on transaction(%d)' % t)
                        return False

                    for input_ in curr_trx.inputs:
                        temp_output = tempUTXOs.get(
                            input_.transaction_output_id, None)
                        if not temp_output:
                            print('# Referenced input on transaction(%d) is missing')
                            return False
                        if input_.UTXO.value != temp_output.value:
                            print(
                                '# Referenced input transaction(%d) value is invalid')
                            return False

                        tempUTXOs.pop(input_.transaction_output_id, None)

                    for output in curr_trx.outputs:
                        tempUTXOs[output.id] = output

                    if curr_trx.outputs[0].recipient != curr_trx.recipient:
                        print(
                            '# Transaction(%d) output recipient is not who it should be')
                        return False
                    if curr_trx.outputs[1].recipient != curr_trx.sender:
                        print('# Transaction(%d) output change is not sender')
                        return False
            print('Blockchain is valid')
            return True

        def get_last_hash(self):
            return self.chain[-1].hash if len(self.chain) > 0 else '0'

    __instance = None

    def __new__(cls):
        if not Blockchain.__instance:
            Blockchain.__instance = Blockchain.__Blockchain()
        return Blockchain.__instance

    def __getattr__(self, name):
        return getattr(self.__instance, name)

    def __setattr__(self, name, value):
        return setattr(self.__instance, name, value)

    @staticmethod
    def getinstance():
        return Blockchain.__instance
