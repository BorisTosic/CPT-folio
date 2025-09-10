from flask import Flask
from flask import render_template
from flask import request
import database_manager as dbHandler

app = Flask(__name__)

@app.route('/index.html', methods=['GET'])
@app.route('/', methods=['POST', 'GET'])
def index():
   return render_template('/index.html', content='data')

@app.route('/sign_in.html', methods=['GET'])
@app.route('/', methods=['POST', 'GET'])
def sign_in():
   return render_template('/sign_in.html', content='data')

@app.route('/sign_up.html', methods=['GET'])
@app.route('/', methods=['POST', 'GET'])
def sign_up():
   return render_template('/sign_up.html', content='data')

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5000)