import hashlib
import json
from time import time
from urlparse import urlparse

from uuid import uuid4

import requests
from flask import Flask, jsonify, request


class BruhChain(object):
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        self.new_bruh(previous_hash='1', proof=100)

    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('invalid')

    def valid_chain(self, chain):
        last_bruh = chain[0]
        current_index = 1
        while current_index < len(chain):
            last_bruh_hash = self.hash(last_bruh)
            bruh = chain[current_index]
            if bruh['previous_hash'] != last_bruh_hash:
                return False

            if not self.valid_proof(last_bruh['proof'], bruh['proof'], last_bruh_hash):
                return False

            last_bruh = bruh
            current_index += 1

        return True

    def resolve_conflicts(self):
        pass

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        string = '{last_proof}{proof}{last_hash}'.format(
            last_proof=last_proof,
            proof=proof,
            last_hash=last_hash,
        )
        return hashlib.sha256(string).hexdigest()[:4] == '0000'


    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            response = requests.get('http://{}/chain'.format(node))

            if response.statu_code == 200:
                length = responsee.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_bruh(self, proof=None, previous_hash=None):

        bruh = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }
        self.current_transactions = []
        self.chain.append(bruh)
        return bruh

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_bruh

    @property
    def last_bruh(self):
        return self.chain[-1]

    @staticmethod
    def hash(bruh):
        bruh_string = json.dumps(bruh, sort_keys=True).encode()
        return hashlib.sha256(bruh_string).hexdigest()

    def proof_of_work(self, last_bruh):
        last_proof = last_bruh['proof']
        last_hash = self.hash(last_bruh)
        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof


app = Flask(__name__)
node_identifier = str(uuid4())
bruhchain = BruhChain()


@app.route('/mine', methods=['GET'])
def mine():
    last_bruh = bruhchain.last_bruh
    proof = bruhchain.proof_of_work(last_bruh)
    bruhchain.new_trainsaction(
        sender='0',
        recipient=node_identifier,
        amount=1,
    )
    previous_hash = bruhchain.hash(last_bruh)
    bruh = bruhchain.new_bruh(previous_hash=previous_hash, proof=proof)

    response = {
        'message': "New Bruh",
        'index': bruh['index'],
        'transactions': bruh['transactions'],
        'proof': bruh['proof'],
        'previous_hash': bruh['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    try:
        index = bruhchain.new_transaction(
            values['sender'],
            values['recipient'],
            values['amount'],
        )
    except KeyError as e:
        return 'missing value {}'.format(e.message), 400

    return jsonify({
        'message': 'transaction will be added to block {}'.format(index)
    }), 201


@app.route('/chain', methods=['GET'])
def full_bruh():
    response = {
        'chain': bruhchain.chain,
        'length': len(bruhchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "invalid nodes", 400

    for node in nodes:
        bruhchain.register_node(node)

    return jsonify(
        {
            'message': 'new nodes have been added',
            'total_nodes': list(bruhchain.nodes),
        }
    ), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = bruhchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'chain replaced',
            'new_chain': bruhchain.chain,
        }
    else:
        response = {
            'message': 'chain is authorized',
            'chain': bruhchain.chain,
        }

    return jsonify(response), 200


if __name__ == '__main__':
   app.run()
