# Module 2 - Create a Cryptocurrency

# Datetime returns the extact date the block is mined 
import datetime
# Hash the blocks
import hashlib
# Encode the blocks before hashing them
import json
# Create and object of flask class, web application itself
# Jsonify returns the messages in postman when we interact with our blockchain
from flask import Flask, jsonify, request
# Request==2.18.4 install: pip install request
import requests 
from uuid import uuid4
from urllib.parse import urlparse


# Part 1 - Building a Blockchain

class Blockchain: 
    # Takes one same argument which refer to the object we create
    def __init__(self):
        # Chain containg the blocks, List containing the blocks
        self.chain = []
        self.transactions = []
        # Creates the Genesis Block (First Block of the Blockchain)
        # Each Block will have it's own proof
        # Second Argument is a key that each block will have (previous hash value)
        # But since its the firs, gensis block, it will not have any previous hash value.
        # Arbitrary value 
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes =set()
    # Create a new block with all the features in a blockchain and will append this new mined block to the blockchain
    def create_block(self, proof, previous_hash):
        # Make a dictionary that will define each block in the blockchain with its four essential keys, index of the block, time stamp, proof of the block, previous hash 
        block = {'index' : len(self.chain) + 1 ,
                 'timestamp' : str(datetime.datetime.now()) ,
                 'proof' : proof,
                 'previous_hash' : previous_hash,
                 'transactions': self.transactions}
        # Updates information into the empty list
        self.transactions =[]
        # Append the block to the chain 
        self.chain.append(block)
        # Display the information of this block in Postman
        return block
    # Gets the previous block
    def get_previous_block (self):
        # Returns the last index of the chain
        return self.chain[-1]
    # First Argument, self (apply this proof of work method from instance object that would be created)
    # Second Argument, previous proof, in order to make the problem that miners have to solve, the previous proof has to be there
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False 
        # Introudce while loop to increment this new proof to check if its the right proof 
        while check_proof is False:
            # Leading Zeros ID (define the problem) (more = harder)
            # EASY CHALLENGE (CAN MAKE IT HARDER)
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == "0000":
                check_proof = True
            else:
                new_proof +=1
        return new_proof

    def hash(self, block):
        # Encodes block in the right SHA 256 Format
        encoded_block = json.dumps(block, sort_keys = True).encode()
        # Returns the cryptographic hash of our block
        return hashlib.sha256(encoded_block).hexdigest()
    
    # Checks if the chain if valid or not
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False 
            previous_block = block
            block_index += 1 
            return True 
        # Take care of our transactions
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender' : sender,
                                  'receiver' : receiver,
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def node(self, address):
        parsed_url = urlparse(address)
        # Since not a list, need to use add
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

# Part 2 - Mining our Blockchain

# Create a web application 
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
# Create an address for the node on Port 
# UUID generates a random address
node_address = str(uuid4()).replace('-', '')


# Create a Blockchain
blockchain = Blockchain()

# USE route() decorator to tell Flask what URL should trigger our function
# Mining a new Block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'Sakin', amount = "10")
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': "Congratulations, you just mined a block!",
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash'],
                'transactions' : block['transactions']}
    return jsonify(response), 200 

# Getting the Full Blockchain 
@app.route('/get_chain', methods=['GET'])
# Display Chain
def get_chain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    return jsonify(response), 200 

# Check if the blockchain is valid    
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': "Blockchain is Valid" }
    else:
        response = {'message' : "Blockchain is not Valid" }
    return jsonify(response), 200 
        
# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiever', 'amount']
    if not all (key in json for key in transaction_keys):
        return "Some Elements of the Transactions are missing" , 400
    # Takes values of keys
    index  = blockchain.add_transaction(json['sender'], json['receiever'], json['amount'])
    response = {'message': f"This transaction will be added to Block {index} "}
    return jsonify(response), 201



# Part 3 - Decentralizing our Blockchain

# Connecting new Nodes 
@app.route('/connect_node', methods=['POST'])

def connect_node():
    json = request.get_json()
    nodes = json.get('node')
    if nodes is None: 
        return "No Mode", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now conncected. The Kincoin Blockchain now contains the following nodes' , 
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replace the chain by the longest chian if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': "Nodes had different chains so the chain was replaced by the longest chain",
                    'new_chain' : blockchain.chain }
    else:
        response = {'message' : "All good, Chain was the longest one.",
                    'actual_chain' : blockchain.chain}
    return jsonify(response), 200

# Running the Application
app.run(host = '0.0.0.0', port = 5000)

    
