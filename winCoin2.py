# Yatin
# Module 1 - Create a Blockchain

# To be installed:
# Flask==0.12.2: pip install Flask==0.12.2
# Postman HTTP Client: https://www.getpostman.com/

# Importing libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urlparse import urlparse

# Part 1 - Building a Blockchain

class Blockchain():

	def __init__(self):			# genesis block
		self.chain= [] 		# empty list i.e. chain
		self.transactions= []
		self.transactions.append({'sender':'reward',
								'receiver':'Yatin',
								'amount':1})
		self.create_block(proof= 1, previous_hash= '0')
		self.nodes= set() 		# as we don't have to store key value pairs

	def create_block(self, proof, previous_hash):
		block= {'index': len(self.chain) + 1,
				'timestamp': str(datetime.datetime.now()),
				'proof': proof,
				'previous_hash': previous_hash,
				'transactions': self.transactions}
		self.transactions= []			# emptying transactions
		self.chain.append(block)
		return block

	def get_previous_block(self):
		return self.chain[-1]

	def proof_of_work(self, previous_proof):
		new_proof= 1
		check_proof= False
		while check_proof is False:
			hash_operation= hashlib.sha256(str(previous_proof**2- new_proof**2).encode()).hexdigest()
			# this shouln't be associative as it'll lead to instant calculation of proof by using a set
			if hash_operation[:4]== '0000':
				check_proof= True
			else:
				new_proof+= 1;
		return new_proof

	def hash(self, block):
		encoded_block= json.dumps(block, sort_keys= True).encode()
		return hashlib.sha256(encoded_block).hexdigest()

	def is_chain_valid(self, chain):
		# we may not take the chain
		previous_block= chain[0]
		block_index= 1
		# don't worry we aren't accessing the block by block_index but by chain index
		while block_index < len(chain):
			block= chain[block_index]
			if block['previous_hash'] != self.hash(previous_block):
				return False
			# let's compare the proof of previous both by first storing & then cal
			hash_operation= hashlib.sha256(str(previous_block['proof']**2 - block['proof']**2)).hexdigest()
			if hash_operation[:4] != '0000':
				return False
			previous_block= block
			block_index+= 1
		return True

	def add_transaction(self, sender, receiver, amount):
		self.transactions.append({'sender': sender,
								'receiver': receiver,
								'amount': amount})
		return self.chain[-1]['index'] + 1

	def add_node(self, address):
		parsed_url= urlparse(address)
		# print (parsed_url)
		self.nodes.add(parsed_url.netloc)

	def update_chain(self):
		network= self.nodes
		longest_chain = None
		max_length= len(self.chain)
		for node in network:
			response= requests.get('http://%s/get_chain' % node)		# its a response file
			if response.status_code== 200:
				length =response.json()['length']
				chain= response.json()['chain']
				if (length > max_length and self.is_chain_valid(chain)):
					max_length= length
					longest_chain= chain

		if longest_chain:
			self.chain= longest_chain
			return True
		return False


# Part 2 - Mining our Blockchain

# Creating a Web App
app= Flask(__name__)

# Creating an address for node on this port
# node_address = str(uuid4()).replace('-','')

# Creating a Blockchain
blockchain = Blockchain()

# Mining a Blockchain
@app.route('/mine_block', methods= ['GET'])
def mine_block():
	previous_block= blockchain.get_previous_block()
	new_proof= blockchain.proof_of_work(previous_block['proof'])
	previous_hash= blockchain.hash(previous_block)
	blockchain.add_transaction(sender= 'reward', receiver= 'Yatin', amount= 1000)
	block= blockchain.create_block(new_proof, previous_hash)
	response= {'message': 'Congratulations, you just mined a block!',
				'index': block['index'],
				'proof': block['proof'],
				'timestamp': block['timestamp'],
				'previous_hash': block['previous_hash'],
				'transactions': block['transactions']}
	return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods= ['GET'])
def get_chain():
	response= {'chain':blockchain.chain,
				'length': len(blockchain.chain)}
	return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods= ['GET'])
def is_valid():
	is_valid= blockchain.is_chain_valid(blockchain.chain)
	if is_valid:
		response= {'message': 'All good. The blockchain is valid.'}
	else:
		response= {'message': 'Error: Blockchain Not Valid'}
	return jsonify(response),200

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
	json= request.get_json()
	tranasaction_keys= ['sender', 'receiver', 'amount']
	if not all(key in json for key in tranasaction_keys):
		return 'some elements are missing', 400
	index_block= blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
	response= {'message': 'This transaction will be added to block%s' % index_block}
	return jsonify(response), 200

@app.route('/add_nodes', methods=['POST'])
def add_nodes():
	json= request.get_json()
	nodes= json.get('nodes')
	if nodes is None:
		return "No node", 400
	for node in nodes:
		blockchain.add_node(node)
	response= {'message': 'all nodes added to main chain',
				'total_nodes': list(blockchain.nodes)}
	return jsonify(response), 200

@app.route('/update_chain', methods=['GET'])
def update_chain():
	is_chain_replaced= blockchain.update_chain()
	print ("kewl")
	if is_chain_replaced:
		response= {'message':'the chain is updated',
			'new_chain': blockchain.chain}
	else:
		response= {'message': 'No change',
			'chain': blockchain.chain}
	return jsonify(response), 200


# Running the app
app.run(host= '0.0.0.0', port= 5001)