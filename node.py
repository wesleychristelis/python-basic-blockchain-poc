from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from wallet import Wallet
from blockchain import Blockchain

app = Flask(__name__)
# app.config["APPLICATION_ROOT"] = "crypto"
# wallet = Wallet()
# blockchain = Blockchain(wallet.public_key)
CORS(app)

@app.route('/', methods=['GET'])
def get_home_ui():
    return send_from_directory('ui', 'node.html')

@app.route('/network', methods=['GET'])
def get_network_ui():
    return send_from_directory('ui', 'network.html')

@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if(wallet.save_keys()):  
        global blockchain
        blockchain = Blockchain(wallet.public_key, args.port)

        # Assumes authenticated user , therfore we could return the private key
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance(),
            'node_id': blockchain.node_id
        }
        return(jsonify(response), 201)
    else:
        response = {
            'message': "Error saving keys !!!"
        }
        return(jsonify(response), 500)

@app.route('/wallet', methods=['GET'])
def load_keys():
    response = {}

    if(wallet.load_keys()):
        global blockchain
        blockchain = Blockchain(wallet.public_key, args.port)

        response['public_key'] = wallet.public_key
        response['private_key'] = wallet.private_key
        response['funds'] = blockchain.get_balance()
        response['node_id'] = blockchain.node_id

        return (response, 200)
    else:
        response['message'] = 'Loading of wallet has failed'
        return (response, 500)

@app.route('/balance', methods=['GET'])
def balance():
    balance = blockchain.get_balance()
    
    if( balance != None):
        return (jsonify({
            "message": "Balance fetched successfully",
            "funds": balance
        }),200)
    else:
        return (jsonify({
            "message": "Loading balance failed",
            "wallet_setup": wallet.public_key != None
        }), 500)

@app.route('/broadcast-transaction', methods=['POST'])
def broadcast_transaction():
    values = request.get_json()
    
    if not values:
        response = {'message': 'No data found.'}
        return jsonify(response), 400
    
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(key in values for key in required):
        response = {'message': 'Some data is missing.'}
        return jsonify(response), 400

    success = blockchain.add_transaction(values['recipient'], values['sender'], values['signature'], values['amount'], is_receiving=True)
    if success:
        response = {
            'message': 'Successfully added transaction.',
            'transaction': {
                'sender': values['sender'],
                'recipient': values['recipient'],
                'amount': values['amount'],
                'signature': values['signature']
            }
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Creating a transaction failed.'
        }
        print(response)
        return jsonify(response), 500

@app.route('/broadcast-block', methods=['POST'])
def broadcast_block():
    values = request.get_json()
    if not values:
        response = {'message': 'No data found.'}
        return jsonify(response), 400
    if 'block' not in values:
        response = {'message': 'Some data is missing.'}
        return jsonify(response), 400
    block = values['block']
    if block['index'] == blockchain.chain[-1].index + 1:
        if blockchain.add_block(block):
            response = {'message': 'Block added'}
            print(response)
            return jsonify(response), 201
        else:
            response = {'message': 'Block seems invalid.'}
            print(response)
            return jsonify(response), 409
    elif block['index'] > blockchain.chain[-1].index:
        response = {'message': 'Block seems to differ from local blockchain.'}
        blockchain.resolve_conflicts = True
        print(response)
        return jsonify(response), 200
    else: 
        response = {'message': 'Block seems to be shorter than loca blockchain, block not added'}
        print(response)
        return jsonify(response), 409
    # body = request.get_json()
    
    # if(not body):
    #     response = {
    #        'message': "Failure: Bad Request"
    #     }
    #     return (jsonify(response),400)

    # if 'block' not in body:
    #     response = {
    #        'message': "Failure: No data found in request"
    #     }
    #     return (jsonify(response),400)

    # block = body['block']
    
    # # Check index on blocks, the block is the next block
    # if block['index'] == blockchain.chain[-1].index + 1:
    #     success = blockchain.add_block(block)
    #     if(success):
    #         response = {
    #             "message":"Success: Broadcast block added to chain"
    #         }
    #         print(response)
    #         return (jsonify(response), 201)
    #     # Error on source block
    #     else:
    #         response = {
    #             "message":"Failure: Validation failed adding broadcast block."
    #         }
    #         print(response)
    #         return (jsonify(response), 409)
    # # Index is ahead of the last index
    # elif block['index'] > blockchain.chain[-1].index:
    #     response = {
    #         "message": "Failure: Broadcast block is ahead of local blockchain, blockchain differs"
    #     }
    #     # We return a 200 success, as this condition being met implies a problem on our local chain
    #     # Error on peer node
    #     print(f'/broadcast_block() -> blockchain.resovle_conflicts: {blockchain.resovle_conflicts}')
    #     blockchain.resovle_conflicts = True
    #     print(f'/broadcast_block() -> blockchain.resovle_conflicts: {blockchain.resovle_conflicts}')
    #     return (jsonify(response),200)
    # # Index is shorter than chain, error on source block
    # else:
    #     response = {
    #          "message": "Failure: Broadcast block is shorter than local blockchain. Blockchain differs"
    #     }
    #     print(response)
    #     return (jsonify(response),409)

@app.route('/transaction', methods=['POST'])
def add_transaction():
    if(wallet.public_key == None):
        response = {
           'message': "No Wallet found"
        }
        return (jsonify(response),404)
    
    body = request.get_json()
 
    if(not body):
        response = {
           'message': "Bad Request"
        }
        return (jsonify(response),400)

    required_fields = ['recipient', 'amount']
    if(not all(field in body for field in required_fields)):
        response = {
           'message': "Required data is missing"
        }
        return (jsonify(response),400)

    recipient = body['recipient']
    amount = body['amount']

    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    if(blockchain.add_transaction(recipient, wallet.public_key, signature, amount)):
        response = {
           'message': "Transaction added successfully",
           'transaction': {
                'sender': wallet.public_key,
                'recipient': recipient,
                'amount': amount,
                'signature': signature
            },
           'funds': blockchain.get_balance(),
           'node_id': blockchain.node_id
        }
        return (jsonify(response),201)
    else:
        response = {
           'message': "Error adding transaction",
        }
        return (jsonify(response),500)

@app.route('/transaction', methods=['GET'])
def get_transaction():
    response = {}
    return (jsonify(response),202)

@app.route('/mine', methods=["POST"])
def mine():
    print(f'/mine() -> blockchain.resovle_conflicts: {blockchain.resovle_conflicts}')
    if blockchain.resovle_conflicts:
        response = {
            "message": "Resolve conflicts first. Block not added"
        }
        return (jsonify(response), 409)

    block = blockchain.mine_block(wallet.public_key)
    
    response = {}
    if(block != None):
        block_dict = block.__dict__.copy()
        block_dict['transactions'] = [tx.__dict__ for tx in block_dict['transactions']]
        response['message'] = "Block mined successfully"
        response['block'] = block_dict
        response['funds'] = blockchain.get_balance()

        return (response, 201)
    else:
        response['message'] = 'Adding a block failed'
        response['wallet_setup'] = wallet.public_key != None

        return (jsonify(response), 500)

@app.route('/resolve-conflicts', methods=['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    if replaced:
        response = {'message': 'Chain was replaced!'}
    else:
        response = {'message': 'Local chain kept!'}
    return jsonify(response), 200

@app.route('/transactions', methods=['GET'])
def get_open_transactions():
    transactions = blockchain.get_open_transactions()
    transactions_dict = [tx.__dict__ for tx in transactions]
    return (jsonify(transactions_dict), 200)

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    # Transform to json using dictionaries

    # go through all the blocks and copy a dictionary version into list
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    
    # transform transactions seperately. More readable
    for dict_block in dict_chain:
        dict_block['transactions'] = [tx.__dict__ for tx in dict_block['transactions']]
    return (jsonify(dict_chain), 200)

@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        "all_nodes": blockchain.get_peer_nodes()
    }
    return jsonify(response, 200)

@app.route('/node', methods=['POST'])
def add_node():
    body = request.get_json()

    if(not body):
        response = {
            "message": "No request data found"
        }
        return (jsonify(response), 400)

    if("node" not in body):
        response = {
            "message": "No peer_node data found"
        }
        return (jsonify(response), 400)

    peer_node = body.get("node")
    blockchain.add_peer_node(peer_node)
    return jsonify({
        "message": "Peer node added succesfully",
        "all_nodes": blockchain.get_peer_nodes()
    }, 201)

@app.route('/node', methods=['DELETE'])
def remove_node():
    node_url = request.args.get('node_url')

    if(node_url == '' or node_url == None):
        response = {
            "message": "No request data found"
        }
        return (jsonify(response), 400)
    blockchain.remove_node(node_url)
    return (jsonify({
        "message":f'Node {node_url} removed successfully.',
        "all_nodes": blockchain.get_peer_nodes()
    }),204)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    print(f'Args {args}; Port={args.port}')

    # For dev purposes we need to differentiate the textfiles we write 
    wallet = Wallet(args.port)
    blockchain = Blockchain(wallet.public_key, args.port)
    app.run(host='0.0.0.0', port=args.port)