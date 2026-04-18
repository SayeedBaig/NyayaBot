import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression 

data = pd.read_csv("models/training_data.csv")

#split data
x = data["text"]
y = data["category"]   

#converting text to numericalvalues
vectorizer = TfidfVectorizer()
x_vectorized = vectorizer.fit_transform(x)  

#train the model
model = LogisticRegression()
model.fit(x_vectorized, y)  

# # def predict_category(text:str):
#     #transform input text
#     text_vectorized = vectorizer.transform([text])  

#     #predict category
#     prediction = model.predict(text_vectorized)[0]

#     #get confidence probablity
#     probabilities = model.predict_proba(text_vectorized)[0]
#     confidence = max(probabilities)

#     return{
#         "category": prediction,
#         "confidence": float(confidence)
#     }


def predict_category(text: str):
    text_lower = text.lower()

    # 🔹 Rule-based logic
    if any(word in text_lower for word in ["salary", "wages", "job", "employer"]):
        return {"category": "labour", "confidence": 0.9}

    elif any(word in text_lower for word in ["rent", "landlord", "evict", "tenant"]):
        return {"category": "tenant", "confidence": 0.9}

    elif any(word in text_lower for word in ["product", "refund", "defect", "order"]):
        return {"category": "consumer", "confidence": 0.9}

    # 🔹 ML fallback
    text_vectorized = vectorizer.transform([text])
    prediction = model.predict(text_vectorized)[0]
    probabilities = model.predict_proba(text_vectorized)[0]
    confidence = max(probabilities)

    return {
        "category": prediction,
        "confidence": float(confidence)
    }
