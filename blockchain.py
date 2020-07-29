import json
import pickle
import requests

# Own lib
from utility.verification import Verification
from utility.hash_util import hash_block
from utility.global_constants import MINING_REWARD
from utility.helpers import sum_reducer
from wallet import Wallet

from block import Block
from transaction import Transaction

print(__name__)

class Blockchain:
    def __init__(self, public_key, node_id):
        print("Blockchain constructor")
        # Initialise 1st block (genesis block)
        genesis_block = Block(0, "", [], -1, 0)
        # Empty list for the blockchain
        self.node_id = node_id
        self.chain = [genesis_block]
        self.__open_transactions = []
        self.public_key = public_key ## Public key
        self.resovle_conflicts = False
        self.__peer_nodes = set()
        self.load_data()

    @property
    def chain(self):
        # returns a copy of the list
        return self.__chain[:]
    
    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_open_transactions(self):
        return self.__open_transactions[:]

    def load_data(self):
        """Initialize blockchain + open transactions data from a file."""
        try:
            with open(f'blockchain-{self.node_id}.txt', mode='r') as file_store:
                file_content = file_store.readlines()
                blockchain = json.loads(file_content[0][:-1]) # first line without carriage return

                # We need to convert  the loaded data because Transactions should use OrderedDict
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
                    updated_block = Block(block['index'], block['previous_hash'], converted_tx, block['proof'], block['timestamp'])
                    updated_blockchain.append(updated_block)
                
                self.chain = updated_blockchain
                open_transactions = json.loads(file_content[1][:-1])

                # We need to convert  the loaded data because Transactions should use OrderedDict
                updated_transactions = []
                for tx in open_transactions:
                    updated_transaction = Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount'])
                    updated_transactions.append(updated_transaction)

                self.__open_transactions = updated_transactions
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)

        except (IOError, IndexError):
            print("Handled exception ... no blockchain store found")
        finally: 
            print("Finally lets move on !!!")

    # Using the JSON text version of saving data, so we can easily test the security by editeing the file and checking the chain fails
    def save_data(self):
        """Save blockchain + open transactions snapshot to a file."""
        try:
            with open(f'blockchain-{self.node_id}.txt', mode='w') as file_store:
                saveable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.previous_hash, [
                    tx.__dict__ for tx in block_el.transactions], block_el.proof, block_el.timestamp) for block_el in self.__chain]]
                
                file_store.write(json.dumps(saveable_chain))
                file_store.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                file_store.write(json.dumps(saveable_tx))
                file_store.write('\n')
                # Save node data    
                file_store.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving failed!')

    # Start: Use of Pickle instead. uses less code. not fully implemented yet.
    def save_data_pickle(self):
        """Save blockchain + open transactions snapshot to a file."""
        with open("blockchain.pickle", mode='wb') as file_store:
            save_data = {
                'chain': self.__chain,
                'ot': self.__open_transactions
            }
            file_store.write(pickle.dumps(save_data))

    def load_data_pickle(self):
        
        with open('blockchain.pickle', mode='rb') as file_store:
            file_content = pickle.loads(file_store.read())
            self.__chain = file_content['chain']
            self.__open_transactions = file_content['ot']
    # End: Use of Pickle instead. uses less code. not fully implemented yet.

    def proof_of_work(self):
        """Generate a proof of work for the open transactions, the hash of the previous block and a random number (which is guessed until it fits)."""
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof_nonce = 0

        while not Verification.valid_proof(self.__open_transactions, last_hash, proof_nonce):
            proof_nonce += 1
        
        return proof_nonce

    def get_balance(self, sender=None):
        """ Get amount(s) sent and recieved for a sender in the blockchain """

        if(sender == None):
            if(self.public_key == None):
                return None
            participant = self.public_key
        else:
            participant = sender
            
        # Nested list comprehension
        tx_sender = [[tx.amount for tx in block.transactions if tx.sender == participant] for block in self.__chain]
        
        # Calculate open transaction not yet mined
        open_tx_sender = [open_tx.amount for open_tx in self.__open_transactions if open_tx.sender == participant]
        tx_sender.append(open_tx_sender)
        amount_sent = sum_reducer(tx_sender)
        
        # Todo: We can abstract this
        tx_recipient = [[tx.amount for tx in block.transactions if tx.recipient == participant] for block in self.__chain]
        amount_received = sum_reducer(tx_recipient)
        
        return amount_received - amount_sent

    def get_last_blockchain_value(self):
        """ Returns the last value of a curretn blick chain"""
        # If list is empty  
        if len(self.__chain) < 1:
            return None

        return self.__chain[-1]

    def add_transaction(self, recipient, sender, signature, amount = 1.0, is_receiving=False):
        """ Adds transaction to open transactions

            Arguments:
                :sender: To Who
                :recipient: By Whom
                :amount: How much
        """
        if self.public_key == None:
            return False
        
        transaction = Transaction(sender, recipient, signature, amount)
        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            if not is_receiving:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transaction'.format(node)
                    try:
                        response = requests.post(url, json={
                                                 'sender': sender, 'recipient': recipient, 'amount': amount, 'signature': signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, needs resolving')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False 

    def add_block(self, block):
        transactions = [Transaction(tx['sender'],tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
        is_valid_prood = Verification.valid_proof(transactions[:-1], block['previous_hash'],block['proof'])
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not is_valid_prood or not hashes_match:
            return False
        block_object = Block(block['index'], block['previous_hash'], transactions, block['proof'], block['timestamp'])
        self.__chain.append(block_object)

        # Make a copy becuaes we are manipkauting the original and dont wan to iterate on it
        open_trns = self.__open_transactions[:]

        # Could possibly refactor for better perfomance
        # Update the open trnasaction on the peer node when a new block is braodcast
        for incoming_trn in block['transactions']:
            for open_trn in open_trns:
                if(open_trn.sender == incoming_trn['sender'] and open_trn.recipient == incoming_trn['recipient'] and open_trn.amount == incoming_trn['amount'] and open_trn.signature == incoming_trn['signature'] ):
                    try:
                        self.__open_transactions.remove(open_trn)
                    except ValueError:
                        print("Item is already removed")

        self.save_data()
        return True

    def resolve(self):
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = f'http://{node}/chain'
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(block['index'], block['previous_hash'], [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']],
                                    block['proof'], block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.chain = winner_chain
        if replace:
            #  we assume transactions are correct after replace , we clear the transactions
            self.__open_transactions = []
        self.save_data()
        return replace

    def mine_block(self, node):
        """ Adds all open transactions onto a block in the blockchain """

        if self.public_key == None:
            return None

        last_block = self.get_last_blockchain_value()
        # List comprehensions
        hashed_block = hash_block(last_block)

        proof = self.proof_of_work()
        reward_transaction = Transaction("MINING", self.public_key, '', MINING_REWARD)

        # Create copy of open transactions
        copied_transactions = self.__open_transactions[:]
        
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None

        # What if the append block fails. We use a copy of the list without affecting the original
        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block, copied_transactions, proof)

        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()

        # Broadcast to all registered peer nodes about mine
        for node in self.__peer_nodes:
            url = f'http://{node}/broadcast-block'
            serializable_block = block.__dict__.copy()
            serializable_block['transactions'] = [tx.__dict__ for tx in serializable_block['transactions']]
            try:
                result = requests.post(url, json={'block': serializable_block})
                print(f'mine_block()-> Broadcast to url {url} with reponse of {result}')
                if result.status_code == 400 or result.status_code == 500:
                    print("Block declined, needs resolving")
                if result.status_code == 409:
                    self.resovle_conflicts = True
                    print(f'/mine_block() -> self.resovle_conflicts: {self.resovle_conflicts}')
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_peer_node(self, node):
        """ Adds new node peer node set 

            Arguments:
            :node: the node URL that should be added
        """
        self.__peer_nodes.add(node)
        self.save_data()
    
    def remove_node(self, peer_node):
        """ Removes node peer node set 

            Arguments:
            :node: the node URL that should be deleted
        """
        self.__peer_nodes.discard(peer_node)
        self.save_data()
    
    def get_peer_nodes(self):
        """ Return a list of all connected peer nodes """
        return  list(self.__peer_nodes)