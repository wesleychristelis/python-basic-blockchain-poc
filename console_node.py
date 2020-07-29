from uuid import uuid4

from utility.verification import Verification
from blockchain import Blockchain
from wallet import Wallet

class Node:
    """The node which runs the local blockchain instance.
    
    Attributes:
        :id: The id of the node.
        :blockchain: The blockchain which is run by this node.
    """

    def __init__(self, port):
        # self.node_id = str(uuid4())
        # self.node_id = 'Wez' # simple name
        self.port = port
        self.wallet = Wallet(port)
        self.blockchain = self.init_wallet()
        #   self.blockchain = None

    def init_wallet(self):
        self.wallet.create_keys()
        return Blockchain(self.wallet.public_key, self.port)

    def get_transaction_value(self):
        """ Returns tuple of transactions details. tx_recipient and tx_amount"""
        tx_recipient = input("Enter the recipients name: ")
        tx_amount = float(input("Enter the transaction amount to be sent: "))

        # Could also use a KV pair: dictionary or class
        return (tx_recipient, tx_amount)

    def get_user_choice(self):
        """ Returns the input of the user (input selection). """
        return input("Your choice: ")

    def print_blockchain_elements(self):
        # Output blockchain list to console
        temp_chain = self.blockchain.chain
        for index in range(len(temp_chain)):
            print('Outputting Block: {}'.format(index))
            print(temp_chain[index]) # refactor this , using the accessor is not efficient
        else: 
            print('-' * 20)

    def listen_for_input(self):
        quit_input = False
        while quit_input is False:
            print("Select option... ")
            print(f'1. Add new transaction: ')
            print(f'2. Mine new block')
            print(f'3. Output blockchain: ')
            print(f'4. Check transaction validity: ')
            print(f'5. Create Wallet')
            print(f'6. Load Wallet')
            print(f'7. Save Keys')
            print(f'q. Quit')
            user_choice = self.get_user_choice()

            if user_choice == "1":
                print("*** Adding Transaction Start ***")
                
                tx_data = self.get_transaction_value()
                tx_recipient, tx_amount = tx_data

                signature =  self.wallet.sign_transaction(self.wallet.public_key, tx_recipient, tx_amount)
                if self.blockchain.add_transaction(tx_recipient, self.wallet.public_key, signature, amount=tx_amount):
                    print("Success: add_transaction")
                else:
                    print("Failed: add_transaction")
                
                print(self.blockchain.get_open_transactions())
                print("*** Adding Transaction End ***")
            elif user_choice == "2": 
                print("*** Mining Block Start ***")

                if not self.blockchain.mine_block(self.wallet.public_key):
                    print("Mining failed, You have no wallet!")
                
                print("*** Mining Block End ***")
            elif user_choice == "3":
                print("*** Outputing Blockchain Start ***") 
                
                self.print_blockchain_elements()
                
                print("*** Outputing Blockchain End ***")
            elif user_choice == "4":
                print("*** Verifying Blockchain Start ***") 
                if Verification.verify_transactions(self.blockchain.get_open_transactions(), self.blockchain.get_balance):
                    print("All transactions verfied")
                else:
                    print("Invalid transactions found")
                
                print("*** Verifying Blockchain End ***")
            elif user_choice == "5":
                print("*** Creating your wallet ***") 
                # Store in file for dev purposes
                self.wallet.create_keys()
                self.blockchain = Blockchain(self.wallet.public_key, self.port)
                print("*** Create wallet completed ***") 
            elif user_choice == "6":
                self.wallet.load_keys()
                self.blockchain = Blockchain(self.wallet.public_key, self.port)
            elif user_choice == "7":
                print("*** Saving `keys ***") 
                self.wallet.save_keys()
                print("*** Saving Keys Complete ***") 
            elif user_choice == "q":
                quit_input = True
            else:
                print("Input invalid. Please choose a valid choice")
                
            if not Verification.verify_chain(self.blockchain.chain):
                self.print_blockchain_elements()
                print("Invalid Blockchain")
                break

            print(f'Balance for {self.wallet.public_key}: {self.blockchain.get_balance():6.2f}')
        else:
            print("User left")
        
        print("Done")

if(__name__ == "__main__"):
    node = Node()
    node.listen_for_input()