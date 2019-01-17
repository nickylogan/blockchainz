from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes


def unserialize_pem_private_key(private_key, password):
    private_key = serialization.load_pem_private_key(
        bytes.fromhex(private_key),
        password=bytes.fromhex(password),
        backend=default_backend()
    )
    return private_key

def unserialize_pem_public_key(public_key):
    public_key = serialization.load_pem_public_key(
        bytes.fromhex(public_key),
        backend=default_backend()
    )
    return public_key

def apply_sha256(*args):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    for arg in args:
        if not isinstance(arg, bytes):
            digest.update(bytes(str(arg), 'utf-8'))
        else:
            digest.update(arg)
    return digest.finalize().hex()


def get_merkle_root(transactions):
    count = len(transactions)
    previous_tree_layer = [t.transaction_id for t in transactions]
    tree_layer = previous_tree_layer
    while count > 1:
        tree_layer = []
        for i in range(1, len(previous_tree_layer)):
            tree_layer.append(
                apply_sha256(previous_tree_layer[i-1], previous_tree_layer[i])
            )
        count = len(tree_layer)
        previous_tree_layer = tree_layer
    merkle_root = tree_layer[0] if count == 1 else ""
    return merkle_root

def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, todict(value, classkey)) 
            for key, value in obj.__dict__.items() 
            if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj