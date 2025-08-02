#!/usr/bin/env python3
"""
Demo script for Intelligent Document Processing Application
This script demonstrates the core functionality without the Streamlit UI
"""

import sys
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import pytesseract
import spacy
import pandas as pd
import re

class DocumentProcessorDemo:
    def __init__(self):
        """Initialize the demo processor"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy model loaded successfully")
        except OSError:
            print("❌ spaCy model not found. Please run: python -m spacy download en_core_web_sm")
            sys.exit(1)
    
    def create_sample_invoice_image(self):
        """Create a sample invoice image for demonstration"""
        # Create a white image
        width, height = 800, 1000
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Try to use a better font, fallback to default
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_title = ImageFont.load_default()
            font_normal = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw invoice content
        y_pos = 50
        
        # Header
        draw.text((50, y_pos), "INVOICE", fill='black', font=font_title)
        y_pos += 60
        
        # Invoice details
        draw.text((50, y_pos), "Invoice #: INV-2024-001", fill='black', font=font_normal)
        y_pos += 30
        draw.text((50, y_pos), "Date: 03/15/2024", fill='black', font=font_normal)
        y_pos += 50
        
        # Bill to
        draw.text((50, y_pos), "Bill To:", fill='black', font=font_normal)
        y_pos += 30
        draw.text((50, y_pos), "John Smith", fill='black', font=font_normal)
        y_pos += 25
        draw.text((50, y_pos), "123 Main Street", fill='black', font=font_normal)
        y_pos += 25
        draw.text((50, y_pos), "New York, NY 10001", fill='black', font=font_normal)
        y_pos += 25
        draw.text((50, y_pos), "john.smith@email.com", fill='black', font=font_normal)
        y_pos += 25
        draw.text((50, y_pos), "Phone: (555) 123-4567", fill='black', font=font_normal)
        y_pos += 50
        
        # Services
        draw.text((50, y_pos), "Description: Professional Services", fill='black', font=font_normal)
        y_pos += 30
        draw.text((50, y_pos), "Hours: 50", fill='black', font=font_normal)
        y_pos += 30
        draw.text((50, y_pos), "Rate: $25.00/hour", fill='black', font=font_normal)
        y_pos += 50
        
        # Amounts
        draw.text((50, y_pos), "Subtotal: $1,250.00", fill='black', font=font_normal)
        y_pos += 30
        draw.text((50, y_pos), "Tax (10%): $125.00", fill='black', font=font_normal)
        y_pos += 30
        draw.text((50, y_pos), "Total: $1,375.00", fill='black', font=font_normal)
        y_pos += 50
        
        # Footer
        draw.text((50, y_pos), "Tax ID: 12-3456789", fill='black', font=font_small)
        y_pos += 25
        draw.text((50, y_pos), "Thank you for your business!", fill='black', font=font_small)
        
        return image
    
    def preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        # Convert PIL to OpenCV format
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Remove noise
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return opening
    
    def extract_text(self, image):
        """Extract text using Tesseract OCR"""
        try:
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, config=custom_config)
            return text
        except Exception as e:
            print(f"❌ OCR Error: {e}")
            return ""
    
    def extract_entities(self, text):
        """Extract entities using spaCy and custom patterns"""
        entities = []
        
        # spaCy NER
        doc = self.nlp(text)
        for ent in doc.ents:
            entities.append({
                'text': ent.text.strip(),
                'label': ent.label_,
                'description': spacy.explain(ent.label_),
                'confidence': 'High',
                'source': 'spaCy NER'
            })
        
        # Custom patterns
        patterns = {
            'Invoice Number': [r'(?:invoice|inv|invoice #|inv #)[\s:]*([A-Z0-9\-]+)'],
            'Amount': [r'\$[\s]*([0-9,]+\.?[0-9]*)'],
            'Date': [r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'],
            'Email': [r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'],
            'Phone': [r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'],
            'Tax ID': [r'([0-9]{2}-[0-9]{7})']
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
    
    def run_demo(self):
        """Run the complete demo"""
        print("🚀 Starting Intelligent Document Processing Demo")
        print("=" * 60)
        
        # Step 1: Create sample document
        print("\n📄 Step 1: Creating sample invoice image...")
        sample_image = self.create_sample_invoice_image()
        sample_image.save("demo_invoice.png")
        print("✅ Sample invoice created: demo_invoice.png")
        
        # Step 2: Preprocess image
        print("\n🔧 Step 2: Preprocessing image for OCR...")
        preprocessed = self.preprocess_image(sample_image)
        cv2.imwrite("demo_preprocessed.png", preprocessed)
        print("✅ Image preprocessed: demo_preprocessed.png")
        
        # Step 3: Extract text
        print("\n📝 Step 3: Extracting text with OCR...")
        extracted_text = self.extract_text(preprocessed)
        print("✅ Text extracted successfully")
        print("\nExtracted Text:")
        print("-" * 40)
        print(extracted_text)
        print("-" * 40)
        
        # Step 4: Extract entities
        print("\n🎯 Step 4: Extracting entities with NLP...")
        entities = self.extract_entities(extracted_text)
        print(f"✅ Found {len(entities)} entities")
        
        # Step 5: Display results
        print("\n📊 Step 5: Processing results...")
        if entities:
            df = pd.DataFrame(entities)
            # Remove duplicates
            df = df.drop_duplicates(subset=['text', 'label'])
            
            print("\nExtracted Entities:")
            print("=" * 80)
            for _, row in df.iterrows():
                print(f"• {row['label']}: {row['text']} (Confidence: {row['confidence']}, Source: {row['source']})")
            
            # Save results
            df.to_csv("demo_results.csv", index=False)
            print(f"\n✅ Results saved to: demo_results.csv")
            
            # Summary
            print(f"\n📈 Summary:")
            print(f"   • Total entities: {len(df)}")
            print(f"   • Categories: {len(df['label'].unique())}")
            print(f"   • High confidence: {len(df[df['confidence'] == 'High'])}")
            
        else:
            print("⚠️ No entities were extracted")
        
        # Cleanup
        print("\n🧹 Cleaning up demo files...")
        for file in ["demo_invoice.png", "demo_preprocessed.png"]:
            if os.path.exists(file):
                os.remove(file)
                print(f"   Removed: {file}")
        
        print("\n🎉 Demo completed successfully!")
        print("\nTo run the full application:")
        print("   streamlit run app.py")

def main():
    """Main demo function"""
    # Check dependencies
    try:
        import cv2
        import pytesseract
        import spacy
        print("✅ All required packages are available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Check Tesseract
    try:
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR is available")
    except:
        print("❌ Tesseract not found. Please install tesseract-ocr")
        sys.exit(1)
    
    # Run demo
    demo = DocumentProcessorDemo()
    demo.run_demo()

if __name__ == "__main__":
    main()