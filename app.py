import streamlit as st
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import spacy
import pandas as pd
import re
import io
import plotly.express as px
from datetime import datetime
import base64

# Configure page
st.set_page_config(
    page_title="Intelligent Document Processor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load spaCy model
@st.cache_resource
def load_nlp_model():
    try:
        nlp = spacy.load("en_core_web_sm")
        return nlp
    except OSError:
        st.error("spaCy English model not found. Please install it using: python -m spacy download en_core_web_sm")
        return None

class DocumentProcessor:
    def __init__(self):
        self.nlp = load_nlp_model()
    
    def preprocess_image(self, image):
        """
        Preprocess image for better OCR results using OpenCV
        """
        # Convert PIL image to OpenCV format
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Remove noise with median blur
        blurred = cv2.medianBlur(gray, 3)
        
        # Apply threshold to get binary image
        thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # De-skew the image (advanced feature)
        coords = np.column_stack(np.where(opening > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Rotate the image to deskew
            (h, w) = opening.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            opening = cv2.warpAffine(opening, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return opening
    
    def extract_text_from_image(self, image):
        """
        Extract text from preprocessed image using Tesseract OCR
        """
        try:
            # Configure Tesseract parameters for better accuracy
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:-/$%#@()[]{}|'
            text = pytesseract.image_to_string(image, config=custom_config)
            return text
        except Exception as e:
            st.error(f"Error during OCR: {str(e)}")
            return ""
    
    def extract_text_from_pdf(self, pdf_bytes):
        """
        Extract text from PDF by converting pages to images
        """
        try:
            pages = convert_from_bytes(pdf_bytes, dpi=300)
            all_text = ""
            
            for page_num, page in enumerate(pages):
                st.write(f"Processing page {page_num + 1}...")
                preprocessed = self.preprocess_image(page)
                text = self.extract_text_from_image(preprocessed)
                all_text += f"\n--- Page {page_num + 1} ---\n{text}\n"
            
            return all_text
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return ""
    
    def extract_entities(self, text):
        """
        Extract named entities and custom patterns from text
        """
        if not self.nlp:
            return []
        
        entities = []
        doc = self.nlp(text)
        
        # Extract spaCy entities
        for ent in doc.ents:
            entities.append({
                'text': ent.text.strip(),
                'label': ent.label_,
                'description': spacy.explain(ent.label_),
                'confidence': 'High',
                'source': 'spaCy NER'
            })
        
        # Custom patterns for invoice/receipt data
        patterns = {
            'Invoice Number': [
                r'(?:invoice|inv|invoice #|inv #)[\s:]*([A-Z0-9\-]+)',
                r'(?:number|no|#)[\s:]*([A-Z0-9\-]+)'
            ],
            'Amount': [
                r'\$[\s]*([0-9,]+\.?[0-9]*)',
                r'(?:total|amount|sum)[\s:]*\$?[\s]*([0-9,]+\.?[0-9]*)',
                r'([0-9,]+\.[0-9]{2})(?:\s*USD|\s*$)'
            ],
            'Date': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
                r'(?:date|dated)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            'Email': [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            'Phone': [
                r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
            ],
            'Tax ID': [
                r'(?:tax id|tax #|ein)[\s:]*([0-9\-]+)',
                r'([0-9]{2}-[0-9]{7})'
            ]
        }
        
        for label, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        'text': match.group(1) if match.groups() else match.group(0),
                        'label': label,
                        'description': f'Custom extracted {label}',
                        'confidence': 'Medium',
                        'source': 'Regex Pattern'
                    })
        
        return entities
    
    def process_document(self, file):
        """
        Main processing pipeline
        """
        if file.type == "application/pdf":
            text = self.extract_text_from_pdf(file.read())
        else:
            image = Image.open(file)
            preprocessed = self.preprocess_image(image)
            text = self.extract_text_from_image(preprocessed)
            
            # Show preprocessed image
            st.subheader("Preprocessed Image")
            st.image(preprocessed, caption="Preprocessed for OCR", use_column_width=True)
        
        entities = self.extract_entities(text)
        
        return text, entities

def create_download_link(df, filename):
    """Create a download link for DataFrame"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
    return href

def main():
    st.title("📄 Intelligent Document Processing & Automation")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Document Processor", "About", "Demo Data"])
    
    if page == "Document Processor":
        st.header("Upload and Process Documents")
        st.markdown("Upload invoices, receipts, forms, or any document containing structured data.")
        
        # Initialize processor
        processor = DocumentProcessor()
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'png', 'jpg', 'jpeg', 'tiff'],
            help="Supported formats: PDF, PNG, JPG, JPEG, TIFF"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.success(f"File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Processing options
            col1, col2 = st.columns(2)
            with col1:
                process_btn = st.button("🚀 Process Document", type="primary")
            with col2:
                show_raw_text = st.checkbox("Show raw extracted text")
            
            if process_btn:
                with st.spinner("Processing document... This may take a few moments."):
                    try:
                        # Process the document
                        extracted_text, entities = processor.process_document(uploaded_file)
                        
                        # Store results in session state
                        st.session_state.extracted_text = extracted_text
                        st.session_state.entities = entities
                        st.session_state.processed = True
                        
                    except Exception as e:
                        st.error(f"Error processing document: {str(e)}")
                        st.session_state.processed = False
            
            # Display results if processed
            if st.session_state.get('processed', False):
                st.markdown("---")
                st.header("📊 Processing Results")
                
                # Show raw text if requested
                if show_raw_text and 'extracted_text' in st.session_state:
                    st.subheader("Raw Extracted Text")
                    st.text_area("", st.session_state.extracted_text, height=200)
                
                # Show extracted entities
                if 'entities' in st.session_state and st.session_state.entities:
                    st.subheader("🎯 Extracted Information")
                    
                    # Create DataFrame
                    df = pd.DataFrame(st.session_state.entities)
                    
                    # Remove duplicates
                    df = df.drop_duplicates(subset=['text', 'label'])
                    
                    # Display in expandable sections by category
                    categories = df['label'].unique()
                    
                    for category in categories:
                        with st.expander(f"{category} ({len(df[df['label'] == category])} items)"):
                            category_df = df[df['label'] == category][['text', 'confidence', 'source']]
                            st.dataframe(category_df, use_container_width=True)
                    
                    # Summary statistics
                    st.subheader("📈 Extraction Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Entities", len(df))
                    with col2:
                        st.metric("Categories", len(categories))
                    with col3:
                        high_conf = len(df[df['confidence'] == 'High'])
                        st.metric("High Confidence", high_conf)
                    
                    # Visualization
                    if len(df) > 0:
                        fig = px.bar(df['label'].value_counts().reset_index(), 
                                   x='count', y='label', orientation='h',
                                   title="Entities by Category")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Human-in-the-loop validation
                    st.subheader("✏️ Review and Edit Results")
                    st.info("Review the extracted data below and make corrections if needed:")
                    
                    edited_df = st.data_editor(
                        df[['text', 'label', 'confidence']],
                        use_container_width=True,
                        num_rows="dynamic"
                    )
                    
                    # Export options
                    st.subheader("💾 Export Data")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📁 Export to CSV"):
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"extracted_data_{timestamp}.csv"
                            st.markdown(create_download_link(edited_df, filename), unsafe_allow_html=True)
                            st.success("CSV file ready for download!")
                    
                    with col2:
                        if st.button("📋 Copy to Clipboard"):
                            st.code(edited_df.to_csv(index=False), language='csv')
                    
                    with col3:
                        if st.button("🔄 Process Another Document"):
                            st.session_state.processed = False
                            st.rerun()
                
                else:
                    st.warning("No entities were extracted from the document. Try uploading a different document or check the image quality.")
    
    elif page == "About":
        st.header("About This Application")
        st.markdown("""
        ## 🎯 What is Intelligent Document Processing?
        
        This application demonstrates advanced document processing using:
        
        - **OpenCV** for image preprocessing and enhancement
        - **Tesseract OCR** for text extraction from images and PDFs
        - **spaCy NLP** for Named Entity Recognition
        - **Custom regex patterns** for domain-specific data extraction
        - **Streamlit** for the interactive web interface
        
        ## 🚀 Features
        
        - **Multi-format Support**: Process PDFs, images (PNG, JPG, TIFF)
        - **Advanced Preprocessing**: Image enhancement, noise reduction, deskewing
        - **Smart Entity Extraction**: Automatic detection of invoices numbers, amounts, dates, etc.
        - **Human-in-the-Loop**: Review and edit extracted data
        - **Export Capabilities**: Download results as CSV
        - **Real-time Processing**: Instant feedback and results
        
        ## 🛠️ Technology Stack
        
        - **Backend**: Python, OpenCV, Tesseract, spaCy
        - **Frontend**: Streamlit
        - **Data Processing**: Pandas, NumPy
        - **Visualization**: Plotly
        
        ## 📈 Use Cases
        
        - Invoice processing and data extraction
        - Receipt digitization for expense management
        - Form processing and automation
        - Document digitization workflows
        - Compliance and audit trail creation
        """)
    
    elif page == "Demo Data":
        st.header("📋 Demo Data and Examples")
        st.markdown("Here are some example documents you can use to test the application:")
        
        # Sample data for demonstration
        sample_invoice_text = """
        INVOICE #INV-2024-001
        Date: 03/15/2024
        
        Bill To:
        John Smith
        123 Main Street
        New York, NY 10001
        john.smith@email.com
        Phone: (555) 123-4567
        
        Description: Professional Services
        Amount: $1,250.00
        Tax: $125.00
        Total: $1,375.00
        
        Tax ID: 12-3456789
        """
        
        st.subheader("Sample Invoice Text")
        st.text_area("Sample invoice content:", sample_invoice_text, height=300)
        
        if st.button("Process Sample Text"):
            processor = DocumentProcessor()
            entities = processor.extract_entities(sample_invoice_text)
            
            if entities:
                df = pd.DataFrame(entities)
                df = df.drop_duplicates(subset=['text', 'label'])
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No entities extracted from sample text.")

if __name__ == "__main__":
    main()