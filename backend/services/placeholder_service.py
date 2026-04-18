# def process_user_input(text:str):
#     return {
#         "category": "General",
#         "message": "processing is not implemented yet "
#     }

from services.classifier import predict_category    

def process_user_input(text:str):
    result = predict_category(text)

    return {
        "category":result["category"],
        "confidence":result["confidence"],
        "message":"Classification completed successfully"
     }