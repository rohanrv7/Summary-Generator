import pinecone
import openai
import PyPDF2
import docx
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)

openai.api_key = "apikey"
pinecone.init(api_key="apikey", environment="us-west1-gcp")

def get_session_index():
    session_id = session.get('session_id', None)
    if session_id is None:
        session_id = str(uuid.uuid4())  
        session['session_id'] = session_id
    return session_id

def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ''
        for page in range(len(pdf_reader.pages)):
            page_text = pdf_reader.pages[page].extract_text() or ""
            text += page_text
        return text.strip()
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = ''
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting text from DOCX: {str(e)}"

def generate_summary(text):
    try:
        prompt = (
            "You are a highly knowledgeable summarization assistant. Please summarize the following text in detail, "
            "covering all main points, key ideas, and important details. The summary should be organized in the following structure:\n"
            "- **Introduction**: Key points and purpose of the document.\n"
            "- **Key Findings**: Most important facts and data.\n"
            "- **Conclusion**: Final takeaways and recommendations.\n\n"
            f"{text}\n\n"
            "Summary (in bullet points, at least 500 words):"
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        if response.get("choices"):
            summary = response["choices"][0]["message"]["content"].strip()
            return summary
        else:
            return "Error: No summary generated"
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def store_embeddings_in_pinecone(text):
    try:
        
        response = openai.Embedding.create(
            model="text-embedding-ada-002", 
            input=text
        )
        embeddings = response['data'][0]['embedding']
      
        session_index_name = get_session_index()

        if session_index_name not in pinecone.list_indexes():
            pinecone.create_index(session_index_name, dimension=len(embeddings), metric="cosine")
        index = pinecone.Index(session_index_name)
        index.upsert(
            vectors=[(str(uuid.uuid4()), embeddings)],  
            namespace=session_index_name
        )
        return True
    except Exception as e:
        return f"Error storing embeddings in Pinecone: {str(e)}"

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
          
        file_type = file.content_type
        if file_type == 'application/pdf':
            text = extract_text_from_pdf(file)
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            text = extract_text_from_docx(file)
        else:
            return jsonify({"error": "Unsupported file type. Please upload a PDF or DOCX file."}), 400

        if not text:
            return jsonify({"error": "No extractable text found in the file."}), 400

        store_embeddings_in_pinecone(text)

        summary = generate_summary(text)
        
        return jsonify({"summary": summary})

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5001)
