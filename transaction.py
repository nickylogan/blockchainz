from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
from blockchain import Blockchain
import utils
import secrets
import json


class Wallet:
    def __init__(self, name):
        self.name = name
        self.generate_key_pair()
        self.UTXOs = {}

    def generate_key_pair(self):
        # use pem instead later
        self.password = secrets.token_bytes().hex()

        prv_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        self.private_key = prv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(
                bytes.fromhex(self.password))
        ).hex()

        pub_key = prv_key.public_key()
        self.public_key = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).hex()

    def get_balance(self):
        total = 0
        bc = Blockchain.getinstance()
        for _, UTXO in bc.UTXOs.items():
            if UTXO.is_mine(self.public_key):
                self.UTXOs[UTXO.id] = UTXO
                total += UTXO.value
        return total

    def send_funds(self, _recipient, value):
        if self.get_balance() < value:
            print('# Not enough funds to send transaction. Transaction discarded')
            return None
        inputs = []

        total = 0
        for _, UTXO in self.UTXOs.items():
            total += UTXO.value
            inputs.append(TransactionInput(UTXO.id))
            if total > value:
                break

        new_trx = Transaction(self.public_key, _recipient, value, inputs)
        new_trx.generate_signature(self.private_key, self.password)

        for i in inputs:
            self.UTXOs.pop(i.transaction_output_id, None)

        return new_trx

    def __str__(self):
        return json.dumps(utils.todict(self), indent=2)


class Transaction:
    sequence = 0

    def __init__(self, sender, recipient, value, inputs):
        self.sender = sender
        self.recipient = recipient
        self.value = value
        self.inputs = inputs
        self.outputs = []

    def calculate_hash(self):
        Transaction.sequence += 1
        return utils.apply_sha256(
            self.sender,
            self.recipient,
            self.value,
            Transaction.sequence
        )

    def generate_signature(self, private_key, password):
        digest = utils.apply_sha256(
            self.sender,
            self.recipient,
            self.value
        )
        private_key = utils.unserialize_pem_private_key(private_key, password)
        self.signature = private_key.sign(
            bytes.fromhex(digest),
            ec.ECDSA(hashes.SHA256())
        ).hex()

    def verify_signature(self):
        digest = utils.apply_sha256(
            self.sender,
            self.recipient,
            self.value
        )
        try:
            sender_pub = utils.unserialize_pem_public_key(self.sender)
            sender_pub.verify(
                bytes.fromhex(self.signature),
                bytes.fromhex(digest),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False

    def process_transaction(self):
        if not self.verify_signature():
            return False
        for i in self.inputs:
            i.UTXO = Blockchain.getinstance().UTXOs[i.transaction_output_id]
        if self.get_inputs_value() < Blockchain.getinstance().minimum_transaction:
            return False

        leftover = self.get_inputs_value() - self.value
        self.transaction_id = self.calculate_hash()

        self.outputs.append(TransactionOutput(
            self.recipient, self.value, self.transaction_id))
        self.outputs.append(TransactionOutput(
            self.sender, leftover, self.transaction_id))

        for o in self.outputs:
            Blockchain.getinstance().UTXOs[o.id] = o

        for i in self.inputs:
            if i.UTXO:
                Blockchain.getinstance().UTXOs.pop(i.UTXO.id, None)

        return True

    def get_inputs_value(self):
        total = 0
        for i in self.inputs:
            if i.UTXO:
                total += i.UTXO.value
        return total

    def get_outputs_value(self):
        return sum((o.value for o in self.outputs))


class TransactionInput:
    def __init__(self, transaction_output_id):
        self.transaction_output_id = transaction_output_id
        self.UTXO = None


class TransactionOutput:
    def __init__(self, recipient, value, parent_transaction_id):
        self.recipient = recipient
        self.value = value
        self.parent_transaction_id = parent_transaction_id
        self.id = utils.apply_sha256(
            recipient,
            value,
            parent_transaction_id
        )

    def is_mine(self, pub_key):
        return pub_key == self.recipient
