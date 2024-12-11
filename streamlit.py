import streamlit as st
import PyPDF2
import docx
import openai

openai.api_key = "apikey"  

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

st.title("Document Summary Generator")

if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'summary_generated' not in st.session_state:
    st.session_state.summary_generated = False

uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx"])

if uploaded_file:
    st.session_state.processing = True
    st.session_state.summary_generated = False

    file_type = uploaded_file.type
    if file_type == "application/pdf":
        text = extract_text_from_pdf(uploaded_file)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = extract_text_from_docx(uploaded_file)
    else:
        st.error("Unsupported file type. Please upload a PDF or DOCX file.")
    
    if text:
        with st.spinner('Generating summary...'):
            summary = generate_summary(text)
        st.session_state.processing = False
        st.session_state.summary_generated = True
        st.subheader("Generated Summary:")
        st.write(summary)
    else:
        st.session_state.processing = False
        st.error("Could not extract text from the file. Please check the file format and content.")
if st.session_state.processing:
    with st.spinner('Processing your file...'):
        st.write("")

