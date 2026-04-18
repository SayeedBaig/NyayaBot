import os
from docx import Document

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "..", "templates")

def generate_document(category: str, user_name: str, details: str, opposite_party: str, issue: str):

    if category == "labour":
        template_file = "labour_complaint.docx"
    elif category == "tenant":
        template_file = "tenant_complaint.docx"
    elif category == "consumer":
        template_file = "consumer_complaint.docx"
    else:
        raise ValueError("Invalid category")

    template_path = os.path.join(TEMPLATE_DIR, template_file)

    doc = Document(template_path)

    for para in doc.paragraphs:
        para.text = para.text.replace("[USER_NAME]", user_name)
        para.text = para.text.replace("[DETAILS]", details)
        para.text = para.text.replace("[OPPOSITE_PARTY]", opposite_party)
        para.text = para.text.replace("[ISSUE]", issue)

    output_path = os.path.join(BASE_DIR, f"generated_{category}.docx")
    doc.save(output_path)

    return output_path