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
import plotly.graph_objects as go
from datetime import datetime
import base64
from document_classifier import DocumentClassifier, DocumentType, Priority

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
        self.classifier = DocumentClassifier()
    
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
            # Convert PDF to images with high DPI for better OCR
            pages = convert_from_bytes(pdf_bytes, dpi=300, first_page=1, last_page=5)  # Limit to first 5 pages for demo
            all_text = ""
            
            # Create a progress bar for PDF processing
            progress_bar = st.progress(0)
            total_pages = len(pages)
            
            for page_num, page in enumerate(pages):
                # Update progress
                progress = (page_num + 1) / total_pages
                progress_bar.progress(progress, text=f"Processing page {page_num + 1} of {total_pages}...")
                
                # Preprocess the page image
                preprocessed = self.preprocess_image(page)
                
                # Extract text with better configuration for PDFs
                custom_config = r'--oem 3 --psm 1 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:-/$%#@()[]{}|\n '
                text = pytesseract.image_to_string(preprocessed, config=custom_config)
                
                if text.strip():  # Only add non-empty text
                    all_text += f"{text}\n"
                
                # Show page preview for first page
                if page_num == 0:
                    st.write("📄 First page preview:")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(page, caption="Original PDF Page", width=300)
                    with col2:
                        st.image(preprocessed, caption="Preprocessed for OCR", width=300)
            
            progress_bar.empty()  # Remove progress bar
            
            # Clean up the extracted text
            all_text = self._clean_extracted_text(all_text)
            
            return all_text
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            st.error("This might be due to missing system dependencies. Please ensure poppler-utils is installed.")
            return ""
    
    def _clean_extracted_text(self, text):
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace and normalize line breaks
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Only keep non-empty lines
                cleaned_lines.append(line)
        
        # Join with single spaces, but preserve paragraph breaks
        cleaned_text = ' '.join(cleaned_lines)
        
        # Fix common OCR errors
        replacements = {
            ' . ': '. ',
            ' , ': ', ',
            ' : ': ': ',
            ' ; ': '; ',
            '  ': ' ',  # Multiple spaces to single space
        }
        
        for old, new in replacements.items():
            cleaned_text = cleaned_text.replace(old, new)
        
        return cleaned_text
    
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
        Main processing pipeline with classification and routing
        """
        # Reset file pointer to beginning
        file.seek(0)
        
        if file.type == "application/pdf":
            st.info("📄 Processing PDF document...")
            text = self.extract_text_from_pdf(file.read())
            
            # Show PDF processing info
            st.subheader("PDF Processing Results")
            if text and text.strip():
                st.success(f"✅ Successfully extracted {len(text)} characters from PDF")
                # Show first 500 characters as preview
                st.text_area("Text Preview (first 500 characters):", text[:500], height=100)
            else:
                st.error("❌ No text could be extracted from PDF")
                return "", [], None
                
        else:
            st.info("🖼️ Processing image document...")
            image = Image.open(file)
            preprocessed = self.preprocess_image(image)
            text = self.extract_text_from_image(preprocessed)
            
            # Show preprocessed image
            st.subheader("Preprocessed Image")
            st.image(preprocessed, caption="Preprocessed for OCR", use_column_width=True)
            
            if text and text.strip():
                st.success(f"✅ Successfully extracted {len(text)} characters from image")
            else:
                st.error("❌ No text could be extracted from image")
                return "", [], None
        
        # Extract entities from the text
        st.info("🧠 Extracting entities with NLP...")
        entities = self.extract_entities(text)
        
        if entities:
            st.success(f"✅ Found {len(entities)} entities")
        else:
            st.warning("⚠️ No entities found - classification may be less accurate")
        
        # Classify document and determine routing
        st.info("🎯 Classifying document and determining routing...")
        classification_result = self.classifier.classify_document(text, entities)
        
        if classification_result:
            doc_type = classification_result.document_type.value.replace('_', ' ').title()
            confidence = classification_result.confidence
            st.success(f"✅ Classified as: {doc_type} (Confidence: {confidence:.1%})")
        else:
            st.error("❌ Classification failed")
        
        return text, entities, classification_result

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
    page = st.sidebar.selectbox("Choose a page", [
        "Document Processor", 
        "Classification & Routing", 
        "Workflow Automation",
        "About", 
        "Demo Data"
    ])
    
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
                        extracted_text, entities, classification_result = processor.process_document(uploaded_file)
                        
                        # Validate results
                        if not extracted_text or not extracted_text.strip():
                            st.error("❌ No text could be extracted from the document. Please check:")
                            st.write("• Document quality and resolution")
                            st.write("• File format compatibility")
                            st.write("• Text visibility and contrast")
                            st.session_state.processed = False
                            return
                        
                        if not classification_result:
                            st.error("❌ Document classification failed")
                            st.session_state.processed = False
                            return
                        
                        # Store results in session state
                        st.session_state.extracted_text = extracted_text
                        st.session_state.entities = entities
                        st.session_state.classification_result = classification_result
                        st.session_state.processed = True
                        
                        st.success("🎉 Document processing completed successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Error processing document: {str(e)}")
                        st.error("Please try:")
                        st.write("• Uploading a different document")
                        st.write("• Checking file format and size")
                        st.write("• Ensuring document is readable")
                        
                        # Show debug information
                        with st.expander("🔧 Debug Information"):
                            st.write(f"File type: {uploaded_file.type}")
                            st.write(f"File size: {uploaded_file.size} bytes")
                            st.write(f"Error details: {str(e)}")
                        
                        st.session_state.processed = False
            
            # Display results if processed
            if st.session_state.get('processed', False):
                st.markdown("---")
                st.header("📊 Processing Results")
                
                # Show document classification first
                if 'classification_result' in st.session_state:
                    classification = st.session_state.classification_result
                    
                    st.subheader("🎯 Document Classification & Routing")
                    
                    # Classification summary
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Document Type", 
                                classification.document_type.value.replace('_', ' ').title())
                    with col2:
                        confidence_color = "🟢" if classification.confidence > 0.7 else "🟡" if classification.confidence > 0.4 else "🔴"
                        st.metric("Confidence", f"{confidence_color} {classification.confidence:.1%}")
                    with col3:
                        priority_color = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                        priority_icon = priority_color.get(classification.routing.priority.value, "⚪")
                        st.metric("Priority", f"{priority_icon} {classification.routing.priority.value.title()}")
                    with col4:
                        st.metric("SLA", f"⏰ {classification.routing.sla_hours}h")
                    
                    # Routing information
                    st.info(f"📤 **Routing Destination:** {classification.routing.department} → {classification.routing.system}")
                    st.info(f"📧 **Notification:** {classification.routing.email}")
                    st.info(f"📝 **Action:** {classification.routing.description}")
                    
                    # Processing notes
                    if classification.processing_notes:
                        with st.expander("🔍 Processing Notes"):
                            for note in classification.processing_notes:
                                st.write(f"• {note}")
                    
                    # Document metadata
                    if classification.extracted_metadata:
                        with st.expander("📋 Document Metadata"):
                            for key, value in classification.extracted_metadata.items():
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

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
    
    elif page == "Classification & Routing":
        st.header("📋 Document Classification & Routing System")
        st.markdown("This page shows the intelligent routing system that automatically classifies documents and routes them to appropriate departments.")
        
        # Initialize processor for routing table
        processor = DocumentProcessor()
        
        # Show routing configuration
        st.subheader("🎯 Routing Configuration")
        routing_df = processor.classifier.get_routing_summary()
        st.dataframe(routing_df, use_container_width=True)
        
        # Document type distribution (if we have processed documents)
        if 'classification_result' in st.session_state:
            st.subheader("📊 Current Document Analysis")
            classification = st.session_state.classification_result
            
            # Create a workflow visualization
            workflow = processor.classifier.simulate_routing_workflow(classification)
            
            st.subheader("🔄 Automated Workflow")
            
            # Display workflow steps
            for step in workflow['workflow_steps']:
                status_icon = {"completed": "✅", "in_progress": "🔄", "pending": "⏳"}
                icon = status_icon.get(step['status'], "⚪")
                
                with st.container():
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.write(f"{icon}")
                    with col2:
                        st.write(f"**Step {step['step']}: {step['action']}**")
                        st.write(f"{step['description']}")
                        st.caption(f"Timestamp: {step['timestamp']}")
                    st.write("")
        
        else:
            st.info("💡 Upload and process a document in the 'Document Processor' tab to see the routing workflow in action!")
        
        # Show document type examples
        st.subheader("📄 Supported Document Types")
        
        doc_types = {
            "Invoice": "Automatically routed to Accounts Payable for payment processing",
            "Contract": "Sent to Legal Department for review and compliance verification",
            "Purchase Order": "Routed to Procurement for vendor coordination",
            "Receipt": "Sent to Accounting for expense categorization",
            "Bank Statement": "Routed to Treasury for cash flow analysis",
            "Tax Document": "Urgent routing to Tax Department for compliance",
            "Legal Document": "Immediate routing to Legal Department",
            "HR Document": "Sent to Human Resources for employee records"
        }
        
        for doc_type, description in doc_types.items():
            with st.expander(f"📑 {doc_type}"):
                st.write(description)
    
    elif page == "Workflow Automation":
        st.header("⚙️ Workflow Automation Dashboard")
        st.markdown("Monitor and manage automated document workflows and routing decisions.")
        
        # Initialize processor
        processor = DocumentProcessor()
        
        # Workflow statistics (simulated)
        st.subheader("📈 Workflow Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Documents Processed Today", "127", "↗️ +23")
        with col2:
            st.metric("Avg Classification Accuracy", "94.2%", "↗️ +2.1%")
        with col3:
            st.metric("SLA Compliance", "98.5%", "↗️ +1.2%")
        with col4:
            st.metric("Manual Reviews", "3", "↘️ -8")
        
        # Department workload distribution
        st.subheader("🏢 Department Workload Distribution")
        
        # Sample data for visualization
        dept_data = {
            'Department': ['Accounts Payable', 'Legal', 'Procurement', 'Accounting', 'HR', 'Treasury'],
            'Documents': [45, 12, 23, 31, 8, 8],
            'Avg SLA (hours)': [24, 4, 12, 48, 48, 72],
            'Status': ['On Track', 'Urgent', 'On Track', 'On Track', 'On Track', 'On Track']
        }
        
        dept_df = pd.DataFrame(dept_data)
        
        # Create workload chart
        fig = px.bar(dept_df, x='Department', y='Documents', 
                    title='Document Distribution by Department',
                    color='Status',
                    color_discrete_map={'On Track': 'green', 'Urgent': 'red'})
        st.plotly_chart(fig, use_container_width=True)
        
        # SLA monitoring
        st.subheader("⏰ SLA Monitoring")
        
        # Create SLA chart
        fig_sla = go.Figure()
        fig_sla.add_trace(go.Scatter(
            x=dept_df['Department'],
            y=dept_df['Avg SLA (hours)'],
            mode='markers+lines',
            name='Average SLA',
            marker=dict(size=10, color='blue')
        ))
        fig_sla.update_layout(
            title='Average SLA by Department',
            xaxis_title='Department',
            yaxis_title='Hours',
            showlegend=True
        )
        st.plotly_chart(fig_sla, use_container_width=True)
        
        # Recent routing decisions
        st.subheader("📋 Recent Routing Decisions")
        
        if 'classification_result' in st.session_state:
            classification = st.session_state.classification_result
            
            recent_data = {
                'Timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                'Document Type': [classification.document_type.value.replace('_', ' ').title()],
                'Confidence': [f"{classification.confidence:.1%}"],
                'Routed To': [classification.routing.department],
                'Priority': [classification.routing.priority.value.title()],
                'SLA': [f"{classification.routing.sla_hours}h"]
            }
            
            recent_df = pd.DataFrame(recent_data)
            st.dataframe(recent_df, use_container_width=True)
        else:
            st.info("Process a document to see routing decisions here.")
        
        # Automation rules
        st.subheader("🔧 Automation Rules")
        
        rules_data = {
            'Rule': [
                'High-value invoices (>$10,000)',
                'Legal documents with urgency keywords',
                'Tax documents during filing season',
                'Contracts requiring signatures',
                'Purchase orders from preferred vendors'
            ],
            'Action': [
                'Escalate to Finance Director',
                'Immediate legal review',
                'Priority tax department routing',
                'DocuSign integration trigger',
                'Auto-approve and fast-track'
            ],
            'Status': ['Active', 'Active', 'Active', 'Active', 'Active']
        }
        
        rules_df = pd.DataFrame(rules_data)
        st.dataframe(rules_df, use_container_width=True)
        
        # Configuration options
        st.subheader("⚙️ System Configuration")
        
        with st.expander("📧 Email Notifications"):
            st.checkbox("Send email notifications on document routing", value=True)
            st.checkbox("Daily summary reports to department heads", value=True)
            st.checkbox("SLA breach alerts", value=True)
        
        with st.expander("🔔 Alert Thresholds"):
            st.slider("Classification confidence threshold", 0.0, 1.0, 0.7, 0.1)
            st.slider("SLA warning threshold (% of time elapsed)", 0, 100, 80, 5)
            st.number_input("High-value document threshold ($)", value=10000, step=1000)
    
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
        
        ### Document Processing
        - **Multi-format Support**: Process PDFs, images (PNG, JPG, TIFF)
        - **Advanced Preprocessing**: Image enhancement, noise reduction, deskewing
        - **Smart Entity Extraction**: Automatic detection of invoices numbers, amounts, dates, etc.
        - **Human-in-the-Loop**: Review and edit extracted data
        - **Export Capabilities**: Download results as CSV
        - **Real-time Processing**: Instant feedback and results
        
        ### Intelligent Classification & Routing
        - **Automatic Document Classification**: AI-powered identification of document types
        - **Smart Routing**: Automatic routing to appropriate departments and systems
        - **Priority Management**: Intelligent prioritization based on document type and content
        - **SLA Tracking**: Service Level Agreement monitoring and compliance
        - **Workflow Automation**: End-to-end automated document processing workflows
        - **Department Integration**: Seamless integration with existing enterprise systems
        
        ## 🛠️ Technology Stack
        
        - **Backend**: Python, OpenCV, Tesseract, spaCy
        - **Frontend**: Streamlit
        - **Data Processing**: Pandas, NumPy
        - **Visualization**: Plotly
        
        ## 📈 Use Cases
        
        ### Financial Operations
        - **Invoice Processing**: Automatic AP routing with vendor management
        - **Receipt Management**: Expense categorization and reimbursement workflows
        - **Purchase Orders**: Procurement coordination and delivery tracking
        - **Bank Statements**: Treasury analysis and cash flow management
        
        ### Legal & Compliance
        - **Contract Management**: Legal review and compliance verification
        - **Legal Documents**: Case management and litigation support
        - **Tax Documents**: Compliance monitoring and filing automation
        
        ### Human Resources
        - **Employee Documents**: HRIS integration and record management
        - **Benefits Administration**: Health plan and claims processing
        
        ### Enterprise Integration
        - **Multi-department Routing**: Intelligent document distribution
        - **SLA Management**: Automated compliance and escalation
        - **Workflow Automation**: End-to-end process automation
        - **Audit Trails**: Complete document processing history
        """)
    
    elif page == "Demo Data":
        st.header("📋 Demo Data and Examples")
        st.markdown("Here are some example documents you can use to test the application:")
        
        # PDF Test Documents Section
        st.subheader("🔧 Generate Test PDF Documents")
        st.markdown("Create sample PDF documents to test the classification system:")
        
        if st.button("🚀 Generate Test PDFs"):
            try:
                # Try to create test PDFs
                st.info("Creating test PDF documents...")
                
                # Create a simple test without reportlab for now
                st.success("✅ Test PDFs would be created here!")
                st.info("📄 Sample documents that would be generated:")
                st.write("• **Invoice PDF**: Complete invoice with line items, amounts, and vendor details")
                st.write("• **Contract PDF**: Service agreement with parties, terms, and signatures")
                st.write("• **Purchase Order PDF**: PO with items, quantities, and delivery information")
                st.write("")
                st.write("💡 **Upload any PDF document** to test the classification system!")
                
            except Exception as e:
                st.error(f"Error creating test PDFs: {e}")
                st.info("You can still upload your own PDF documents to test the system.")
        
        st.markdown("---")
        
        # Sample data for demonstration
        st.subheader("📝 Sample Text Processing")
        st.markdown("Test the classification system with sample invoice text:")
        
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
            
            # Classify the sample text
            classification_result = processor.classifier.classify_document(sample_invoice_text, entities)
            
            # Show classification results
            st.subheader("🎯 Classification Results")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Document Type", classification_result.document_type.value.replace('_', ' ').title())
            with col2:
                st.metric("Confidence", f"{classification_result.confidence:.1%}")
            with col3:
                st.metric("Priority", classification_result.routing.priority.value.title())
            
            st.info(f"📤 **Routing:** {classification_result.routing.department} → {classification_result.routing.system}")
            
            # Show entities
            if entities:
                st.subheader("📊 Extracted Entities")
                df = pd.DataFrame(entities)
                df = df.drop_duplicates(subset=['text', 'label'])
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No entities extracted from sample text.")
        
        # PDF Troubleshooting Section
        st.markdown("---")
        st.subheader("🔧 PDF Processing Troubleshooting")
        
        with st.expander("📄 PDF Processing Tips"):
            st.markdown("""
            **For best PDF classification results:**
            
            • **Text-based PDFs**: Work best (created from Word, Excel, etc.)
            • **Scanned PDFs**: Require OCR processing (may take longer)
            • **High Quality**: 300 DPI or higher for scanned documents
            • **Clear Text**: Good contrast between text and background
            • **Standard Fonts**: Avoid decorative or handwritten fonts
            
            **Common Issues:**
            
            • **No text extracted**: PDF may be image-only or corrupted
            • **Low classification confidence**: Poor OCR quality or unclear text
            • **Wrong classification**: Document may contain mixed content
            
            **Supported Document Types:**
            
            • ✅ **Invoices**: Bills, payment requests, service invoices
            • ✅ **Contracts**: Service agreements, employment contracts
            • ✅ **Purchase Orders**: Procurement documents, requisitions
            • ✅ **Receipts**: Transaction receipts, expense documents
            • ✅ **Bank Statements**: Account statements, transaction histories
            • ✅ **Tax Documents**: Forms, returns, tax-related papers
            • ✅ **Legal Documents**: Court documents, legal correspondence
            • ✅ **HR Documents**: Employee records, job offers, evaluations
            """)
        
        with st.expander("🚀 Testing the System"):
            st.markdown("""
            **Step-by-step testing process:**
            
            1. **Upload Document**: Use the file uploader in the Document Processor tab
            2. **Review OCR Results**: Check the extracted text quality
            3. **Verify Classification**: Confirm document type and confidence score
            4. **Check Routing**: Review the suggested department and system
            5. **Validate Entities**: Ensure key information was extracted correctly
            6. **Test Workflow**: View the automated routing workflow
            
            **What to expect:**
            
            • **Processing Time**: 5-30 seconds depending on document size
            • **Classification Confidence**: 70%+ for good quality documents
            • **Entity Extraction**: Key information like amounts, dates, names
            • **Automatic Routing**: Department assignment and priority setting
            """)
            
        # System Status
        st.markdown("---")
        st.subheader("🔍 System Status")
        
        processor = DocumentProcessor()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            nlp_status = "✅ Ready" if processor.nlp else "❌ Not Available"
            st.metric("NLP Engine", nlp_status)
        
        with col2:
            classifier_status = "✅ Ready" if processor.classifier else "❌ Not Available"
            st.metric("Document Classifier", classifier_status)
            
        with col3:
            routing_count = len(processor.classifier.routing_destinations) if processor.classifier else 0
            st.metric("Routing Rules", f"{routing_count} configured")

if __name__ == "__main__":
    main()