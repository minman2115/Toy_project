from flask import *
import pickle
import numpy as np
from sklearn.externals import joblib

app = Flask(__name__)

models = {}

def init():
    with open("./model/classification_model.pkl", "rb") as f:
        models["classification"] = pickle.load(f)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predic")
def predic():
    result = {}
    result["category"] = [ "정치", "경제", "사회", "생활/문화", "세계", "IT/과학"]

    model = models["classification"]

    # URL Query - ?setence=문자열
    sentence = request.values.get("sentence")

    result["result"] = list(np.round_(model.predict_proba([sentence])[0]*100, 2))

    return json.dumps(result, ensure_ascii=False).encode('utf8')

init()

app.run(debug=True)
