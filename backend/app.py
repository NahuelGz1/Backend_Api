import os
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/api/ping', methods = ['GET'])
def ping():
    return jsonify({"status":"ok",
    "message":"Backend Flask running"}),200

if __name__ == '__main__':
    port = int(os.getenv('PORT',5000))
    app.run(host='0.0.0.0',port=port,debug=True)