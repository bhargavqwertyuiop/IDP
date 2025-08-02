#!/usr/bin/env python3
"""
Test PDF Generator
Creates sample PDF documents for testing the classification and routing system
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime, timedelta
import os

class TestPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        styles = {}
        
        styles['Title'] = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        )
        
        styles['Subtitle'] = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.darkblue
        )
        
        styles['Body'] = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12
        )
        
        return styles
    
    def create_sample_invoice(self, filename="test_invoice.pdf"):
        """Create a sample invoice PDF"""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("INVOICE", self.custom_styles['Title']))
        story.append(Spacer(1, 20))
        
        # Invoice details
        invoice_data = [
            ["Invoice #:", "INV-2024-001"],
            ["Date:", "March 15, 2024"],
            ["Due Date:", "April 15, 2024"],
            ["", ""]
        ]
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(invoice_table)
        story.append(Spacer(1, 20))
        
        # Bill to section
        story.append(Paragraph("Bill To:", self.custom_styles['Subtitle']))
        bill_to_text = """
        ABC Corporation<br/>
        123 Business Street<br/>
        New York, NY 10001<br/>
        contact@abccorp.com<br/>
        Phone: (555) 123-4567
        """
        story.append(Paragraph(bill_to_text, self.custom_styles['Body']))
        story.append(Spacer(1, 20))
        
        # Services table
        story.append(Paragraph("Services:", self.custom_styles['Subtitle']))
        
        services_data = [
            ["Description", "Quantity", "Rate", "Amount"],
            ["Professional Consulting Services", "40 hours", "$150.00", "$6,000.00"],
            ["Project Management", "20 hours", "$125.00", "$2,500.00"],
            ["Technical Documentation", "10 hours", "$100.00", "$1,000.00"],
            ["", "", "Subtotal:", "$9,500.00"],
            ["", "", "Tax (8.5%):", "$807.50"],
            ["", "", "Total:", "$10,307.50"]
        ]
        
        services_table = Table(services_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        services_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (2, -3), (-1, -1), 'Helvetica-Bold'),
        ]))
        story.append(services_table)
        story.append(Spacer(1, 30))
        
        # Payment terms
        story.append(Paragraph("Payment Terms:", self.custom_styles['Subtitle']))
        terms_text = """
        Net 30 days. Please remit payment to:<br/>
        ABC Services Inc.<br/>
        Tax ID: 12-3456789<br/>
        Account: 1234567890
        """
        story.append(Paragraph(terms_text, self.custom_styles['Body']))
        
        doc.build(story)
        print(f"✅ Created sample invoice: {filename}")
        return filename
    
    def create_sample_contract(self, filename="test_contract.pdf"):
        """Create a sample contract PDF"""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("SERVICE AGREEMENT", self.custom_styles['Title']))
        story.append(Spacer(1, 30))
        
        # Contract details
        contract_text = f"""
        This Service Agreement ("Agreement") is entered into on {datetime.now().strftime('%B %d, %Y')} 
        between TechCorp Solutions, a Delaware corporation ("Company"), and ClientCorp Inc., 
        a New York corporation ("Client").
        """
        story.append(Paragraph(contract_text, self.custom_styles['Body']))
        story.append(Spacer(1, 20))
        
        # Whereas clauses
        story.append(Paragraph("RECITALS", self.custom_styles['Subtitle']))
        whereas_text = """
        WHEREAS, Company provides professional consulting services in technology implementation;<br/><br/>
        WHEREAS, Client desires to engage Company to provide such services;<br/><br/>
        WHEREAS, the parties wish to set forth the terms and conditions of their agreement;
        """
        story.append(Paragraph(whereas_text, self.custom_styles['Body']))
        story.append(Spacer(1, 20))
        
        # Terms
        story.append(Paragraph("TERMS AND CONDITIONS", self.custom_styles['Subtitle']))
        
        terms_sections = [
            ("1. Services", "Company shall provide technology consulting services as described in Exhibit A."),
            ("2. Term", f"This Agreement shall commence on {datetime.now().strftime('%B %d, %Y')} and continue for a period of twelve (12) months."),
            ("3. Compensation", "Client shall pay Company $150,000 for the services, payable in monthly installments."),
            ("4. Confidentiality", "Both parties agree to maintain confidentiality of proprietary information."),
            ("5. Termination", "Either party may terminate this Agreement with thirty (30) days written notice.")
        ]
        
        for title, content in terms_sections:
            story.append(Paragraph(title, self.custom_styles['Subtitle']))
            story.append(Paragraph(content, self.custom_styles['Body']))
            story.append(Spacer(1, 15))
        
        # Signatures
        story.append(Spacer(1, 30))
        story.append(Paragraph("IN WITNESS WHEREOF", self.custom_styles['Subtitle']))
        
        signature_data = [
            ["TechCorp Solutions", "", "ClientCorp Inc."],
            ["", "", ""],
            ["_________________________", "", "_________________________"],
            ["John Smith, CEO", "", "Jane Doe, CTO"],
            [f"Date: {datetime.now().strftime('%m/%d/%Y')}", "", f"Date: {datetime.now().strftime('%m/%d/%Y')}"]
        ]
        
        signature_table = Table(signature_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(signature_table)
        
        doc.build(story)
        print(f"✅ Created sample contract: {filename}")
        return filename
    
    def create_sample_purchase_order(self, filename="test_purchase_order.pdf"):
        """Create a sample purchase order PDF"""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("PURCHASE ORDER", self.custom_styles['Title']))
        story.append(Spacer(1, 20))
        
        # PO details
        po_data = [
            ["PO Number:", "PO-2024-0456"],
            ["Date:", datetime.now().strftime('%B %d, %Y')],
            ["Delivery Date:", (datetime.now() + timedelta(days=30)).strftime('%B %d, %Y')],
            ["Vendor:", "Office Supplies Plus"]
        ]
        
        po_table = Table(po_data, colWidths=[2*inch, 3*inch])
        po_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(po_table)
        story.append(Spacer(1, 20))
        
        # Ship to
        story.append(Paragraph("Ship To:", self.custom_styles['Subtitle']))
        ship_to_text = """
        TechCorp Solutions<br/>
        456 Technology Drive<br/>
        San Francisco, CA 94105<br/>
        Attn: Procurement Department
        """
        story.append(Paragraph(ship_to_text, self.custom_styles['Body']))
        story.append(Spacer(1, 20))
        
        # Items table
        story.append(Paragraph("Items Ordered:", self.custom_styles['Subtitle']))
        
        items_data = [
            ["Item", "Description", "Quantity", "Unit Price", "Total"],
            ["OF-001", "Office Chairs (Ergonomic)", "25", "$299.00", "$7,475.00"],
            ["OF-002", "Standing Desks", "15", "$599.00", "$8,985.00"],
            ["OF-003", "Monitor Arms", "30", "$89.00", "$2,670.00"],
            ["OF-004", "Desk Organizers", "50", "$25.00", "$1,250.00"],
            ["", "", "", "Subtotal:", "$20,380.00"],
            ["", "", "", "Shipping:", "$500.00"],
            ["", "", "", "Total:", "$20,880.00"]
        ]
        
        items_table = Table(items_data, colWidths=[1*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
            ('GRID', (0, 0), (-1, -4), 1, colors.black),
            ('FONTNAME', (3, -3), (-1, -1), 'Helvetica-Bold'),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Terms
        story.append(Paragraph("Terms:", self.custom_styles['Subtitle']))
        terms_text = """
        Payment Terms: Net 30 days<br/>
        Delivery: FOB Destination<br/>
        Special Instructions: Please coordinate delivery with receiving department.
        """
        story.append(Paragraph(terms_text, self.custom_styles['Body']))
        
        doc.build(story)
        print(f"✅ Created sample purchase order: {filename}")
        return filename
    
    def create_all_test_documents(self):
        """Create all test documents"""
        print("🚀 Creating test PDF documents...")
        
        # Create output directory
        os.makedirs("test_documents", exist_ok=True)
        
        # Create test documents
        files = []
        files.append(self.create_sample_invoice("test_documents/sample_invoice.pdf"))
        files.append(self.create_sample_contract("test_documents/sample_contract.pdf"))
        files.append(self.create_sample_purchase_order("test_documents/sample_purchase_order.pdf"))
        
        print(f"\n🎉 Created {len(files)} test documents:")
        for file in files:
            print(f"  📄 {file}")
        
        print("\n💡 You can now upload these documents to test the classification system!")
        return files

def main():
    """Main function to create test documents"""
    generator = TestPDFGenerator()
    generator.create_all_test_documents()

if __name__ == "__main__":
    main()