from utility.hash_util import hash_string_256, hash_block
from wallet import Wallet

class Verification:

    @staticmethod
    def valid_proof(transactions, last_hash, proof_number):
        """ Proof of work: (decided by th eimplmenter of the crypto currency)
            Transactions - Previous Hash - Proof (Nonce) (random number) : implemented in a loop 
            We combine the 3 above values in a hash (1 string with 64 chars)
            If hash starts with a "n" amount of leading chars (this is up to you).
            If the block is chnaged the POW would need to be recaclualted for that block and all susequent blocks. 
            This is time consuming  and therefore makes it really hard to change as time and power is needed.
        """
        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof_number)).encode()
        guess_hash = hash_string_256(guess)

        return guess_hash[0:2] == "00" # for simplicity we will on looking for 2 leading zeroes
    
    @classmethod
    def verify_chain(cls, blockchain):
        """ Verify blocks in chain. Returns true if chain is valid """  
        # Enumerate returns a tuple of the value with an index, and we unpack
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            # Compare the first value of a block with the entire previous block
            if(block.previous_hash != hash_block(blockchain[index -1])):
                return False
            
            # Check proof on transactions , EXCLUDING the reward transaction
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print("Proof of work is invalid")
                return False
        
        return True
    
    @staticmethod
    def verify_transaction(transaction, get_balance, check_funds=True):
        """Verify transaction: Verify there is enough funds to send currency"""
        if check_funds:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(transaction)
        else:
            return Wallet.verify_transaction(transaction)

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        return all([cls.verify_transaction(tx, get_balance, False) for tx in open_transactions])