from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import Crypto.Random
import binascii

class Wallet:
    def __init__(self, node_id):
        self.private_key = None
        self.public_key = None
        self.node_id = node_id
    
    def create_keys(self):
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key
    
    def save_keys(self):
        """Saves the keys to a file (wallet.txt)."""
        if(self.public_key != None and self.private_key != None):
            try: 
                with open(f'wallet-{self.node_id}.txt', mode='w') as file_store:
                    file_store.write(self.public_key)
                    file_store.write("\n")
                    file_store.write(self.private_key)
                return True
            except(IOError, IndexError):
                print("Saving wallets failed!")
                return False

    def load_keys(self):
        """Loads the keys from the wallet.txt file into memory."""
        try:
            with open(f'wallet-{self.node_id}.txt', mode='r') as file_store:
                keys = file_store.readlines()
                self.public_key = keys[0][:-1] # truncuate the carriage return
                self.private_key = keys[1]
                return True
        except(IOError, IndexError):
            print("Loading waller failed")
            return False

    def generate_keys(self):
        # Something small now, we can set this higher if we want
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        # Convert binary private kety to string, export key format DER == binary encoding
        return (binascii.hexlify(private_key.exportKey(format="DER")).decode('ascii'), binascii.hexlify(public_key.exportKey(format="DER")).decode('ascii'))

    def sign_transaction(self, sender, recipient, amount):
        """ Generate siganture for a new transaction 
            Arguments:
            :sender: sendor of the trn
            :recipient: reciever of the trn
            :amount: amount of trn
        """ 
        # Keys are stroed as stringsand we need to convert them back to binary
        # Private key is used for siging
        signer_identity = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        temp_hash = SHA256.new((str(sender) + str(recipient) + str(amount)).encode('utf8'))
        signature = signer_identity.sign(temp_hash)

        return binascii.hexlify(signature).decode('ascii')
    
    @staticmethod
    def verify_transaction(transaction):
        """Verify the signature of a transaction.

        Arguments:
            :transaction: The transaction that should be verified.
        """
        # We use public keys as addresses in ur cin network
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)

        temp_hash = temp_hash = SHA256.new((str(transaction.sender) + str(transaction.recipient) + str(transaction.amount)).encode('utf8'))
        return verifier.verify(temp_hash, binascii.unhexlify(transaction.signature))

        





