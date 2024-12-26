# import libraries
from flask import Flask, render_template

# import app functions
from app.templates.api.v1.endpoints import api_v1
from app.templates.api.v2.endpoints import api_v2

import logging
logging.basicConfig(level=logging.DEBUG)

# initialize flask app
app = Flask(__name__)
# Register blueprints with version prefixes
app.register_blueprint(api_v1, url_prefix='/api/v1')
app.register_blueprint(api_v2, url_prefix='/api/v2')

# endpoint to load index.html
@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/monitor')
def monitor():
    return render_template('monitor.html')

if __name__ == '__main__':
    logging.basicConfig(filename='app.log', level=logging.INFO)
    app.run(debug=True)
