#!/usr/bin/env python3
"""
Document Classification Module
Automatically classifies documents and determines routing destinations
"""

import re
import spacy
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd

class DocumentType(Enum):
    """Supported document types for classification"""
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    PURCHASE_ORDER = "purchase_order"
    BANK_STATEMENT = "bank_statement"
    TAX_DOCUMENT = "tax_document"
    LEGAL_DOCUMENT = "legal_document"
    HR_DOCUMENT = "hr_document"
    INSURANCE_DOCUMENT = "insurance_document"
    MEDICAL_DOCUMENT = "medical_document"
    UNKNOWN = "unknown"

class Priority(Enum):
    """Processing priority levels"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class RoutingDestination:
    """Represents where a document should be routed"""
    department: str
    system: str
    email: str
    priority: Priority
    sla_hours: int  # Service Level Agreement in hours
    description: str

@dataclass
class ClassificationResult:
    """Result of document classification"""
    document_type: DocumentType
    confidence: float
    routing: RoutingDestination
    extracted_metadata: Dict
    processing_notes: List[str]

class DocumentClassifier:
    """
    Intelligent document classifier that identifies document types
    and determines appropriate routing destinations
    """
    
    def __init__(self):
        """Initialize the classifier with routing rules and patterns"""
        self.nlp = None
        self._load_nlp_model()
        self._setup_classification_patterns()
        self._setup_routing_destinations()
    
    def _load_nlp_model(self):
        """Load spaCy model for NLP processing"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy model not available. Classification accuracy may be reduced.")
    
    def _setup_classification_patterns(self):
        """Define patterns for document classification"""
        self.classification_patterns = {
            DocumentType.INVOICE: {
                'keywords': [
                    'invoice', 'bill', 'billing', 'payment due', 'amount due',
                    'invoice number', 'inv #', 'invoice date', 'due date',
                    'remit to', 'bill to', 'sold to', 'ship to'
                ],
                'patterns': [
                    r'invoice\s*#?\s*[:\-]?\s*[A-Z0-9\-]+',
                    r'bill\s*#?\s*[:\-]?\s*[A-Z0-9\-]+',
                    r'amount\s*due\s*[:\$]',
                    r'payment\s*terms',
                    r'net\s*\d+\s*days'
                ],
                'required_entities': ['MONEY', 'DATE'],
                'weight': 1.0
            },
            
            DocumentType.RECEIPT: {
                'keywords': [
                    'receipt', 'thank you', 'purchase', 'transaction',
                    'cash register', 'pos', 'total', 'change', 'tender'
                ],
                'patterns': [
                    r'receipt\s*#?\s*[:\-]?\s*[A-Z0-9\-]+',
                    r'transaction\s*#?\s*[:\-]?\s*[A-Z0-9\-]+',
                    r'thank\s*you\s*for\s*your\s*purchase',
                    r'change\s*due',
                    r'cash\s*tendered'
                ],
                'required_entities': ['MONEY'],
                'weight': 0.8
            },
            
            DocumentType.CONTRACT: {
                'keywords': [
                    'contract', 'agreement', 'terms and conditions', 'whereas',
                    'party', 'parties', 'effective date', 'termination',
                    'obligations', 'covenant', 'indemnify', 'liability'
                ],
                'patterns': [
                    r'this\s+agreement',
                    r'whereas\s+',
                    r'party\s+of\s+the\s+first\s+part',
                    r'effective\s+date',
                    r'terms\s+and\s+conditions',
                    r'in\s+witness\s+whereof'
                ],
                'required_entities': ['PERSON', 'ORG', 'DATE'],
                'weight': 1.2
            },
            
            DocumentType.PURCHASE_ORDER: {
                'keywords': [
                    'purchase order', 'po number', 'po #', 'vendor',
                    'ship to', 'deliver to', 'quantity', 'unit price',
                    'line item', 'procurement', 'requisition'
                ],
                'patterns': [
                    r'purchase\s*order\s*#?\s*[:\-]?\s*[A-Z0-9\-]+',
                    r'po\s*#?\s*[:\-]?\s*[A-Z0-9\-]+',
                    r'ship\s*to\s*address',
                    r'vendor\s*#?\s*[:\-]?\s*[A-Z0-9\-]+',
                    r'delivery\s*date'
                ],
                'required_entities': ['MONEY', 'ORG'],
                'weight': 1.0
            },
            
            DocumentType.BANK_STATEMENT: {
                'keywords': [
                    'bank statement', 'account statement', 'balance',
                    'deposit', 'withdrawal', 'transaction history',
                    'beginning balance', 'ending balance', 'routing number'
                ],
                'patterns': [
                    r'account\s*number\s*[:\-]?\s*[X\*]*\d+',
                    r'statement\s*period',
                    r'beginning\s*balance',
                    r'ending\s*balance',
                    r'routing\s*number'
                ],
                'required_entities': ['MONEY', 'DATE'],
                'weight': 1.0
            },
            
            DocumentType.TAX_DOCUMENT: {
                'keywords': [
                    'tax return', 'form 1040', 'w-2', 'w-4', '1099',
                    'tax identification', 'ein', 'ssn', 'irs',
                    'taxable income', 'deduction', 'withholding'
                ],
                'patterns': [
                    r'form\s*\d{4}[A-Z]*',
                    r'tax\s*year\s*\d{4}',
                    r'ein\s*[:\-]?\s*\d{2}-\d{7}',
                    r'ssn\s*[:\-]?\s*\d{3}-\d{2}-\d{4}',
                    r'adjusted\s*gross\s*income'
                ],
                'required_entities': ['MONEY', 'DATE'],
                'weight': 1.1
            },
            
            DocumentType.LEGAL_DOCUMENT: {
                'keywords': [
                    'plaintiff', 'defendant', 'court', 'jurisdiction',
                    'lawsuit', 'litigation', 'affidavit', 'deposition',
                    'subpoena', 'motion', 'brief', 'docket'
                ],
                'patterns': [
                    r'case\s*no\.?\s*[:\-]?\s*[A-Z0-9\-]+',
                    r'court\s*of\s*',
                    r'plaintiff\s*v\.?\s*defendant',
                    r'state\s*of\s*[A-Z][a-z]+',
                    r'jurisdiction'
                ],
                'required_entities': ['PERSON', 'ORG', 'GPE'],
                'weight': 1.2
            },
            
            DocumentType.HR_DOCUMENT: {
                'keywords': [
                    'employee', 'employment', 'job offer', 'salary',
                    'benefits', 'vacation', 'sick leave', 'performance',
                    'evaluation', 'disciplinary', 'termination', 'resignation'
                ],
                'patterns': [
                    r'employee\s*id\s*[:\-]?\s*[A-Z0-9\-]+',
                    r'job\s*title',
                    r'start\s*date',
                    r'salary\s*[:\$]',
                    r'performance\s*review'
                ],
                'required_entities': ['PERSON', 'MONEY', 'DATE'],
                'weight': 1.0
            }
        }
    
    def _setup_routing_destinations(self):
        """Define routing destinations for each document type"""
        self.routing_destinations = {
            DocumentType.INVOICE: RoutingDestination(
                department="Accounts Payable",
                system="ERP System (SAP/Oracle)",
                email="ap@company.com",
                priority=Priority.HIGH,
                sla_hours=24,
                description="Route to AP for payment processing and vendor management"
            ),
            
            DocumentType.RECEIPT: RoutingDestination(
                department="Accounting",
                system="Expense Management System",
                email="accounting@company.com",
                priority=Priority.MEDIUM,
                sla_hours=48,
                description="Route to accounting for expense categorization and reimbursement"
            ),
            
            DocumentType.CONTRACT: RoutingDestination(
                department="Legal Department",
                system="Contract Management System",
                email="legal@company.com",
                priority=Priority.URGENT,
                sla_hours=4,
                description="Route to legal for review, approval, and compliance verification"
            ),
            
            DocumentType.PURCHASE_ORDER: RoutingDestination(
                department="Procurement",
                system="Procurement System",
                email="procurement@company.com",
                priority=Priority.HIGH,
                sla_hours=12,
                description="Route to procurement for vendor coordination and delivery tracking"
            ),
            
            DocumentType.BANK_STATEMENT: RoutingDestination(
                department="Treasury",
                system="Cash Management System",
                email="treasury@company.com",
                priority=Priority.MEDIUM,
                sla_hours=72,
                description="Route to treasury for cash flow analysis and reconciliation"
            ),
            
            DocumentType.TAX_DOCUMENT: RoutingDestination(
                department="Tax Department",
                system="Tax Management System",
                email="tax@company.com",
                priority=Priority.URGENT,
                sla_hours=2,
                description="Route to tax department for compliance and filing requirements"
            ),
            
            DocumentType.LEGAL_DOCUMENT: RoutingDestination(
                department="Legal Department",
                system="Legal Case Management",
                email="legal@company.com",
                priority=Priority.URGENT,
                sla_hours=1,
                description="Route to legal for immediate review and case management"
            ),
            
            DocumentType.HR_DOCUMENT: RoutingDestination(
                department="Human Resources",
                system="HRIS System",
                email="hr@company.com",
                priority=Priority.MEDIUM,
                sla_hours=48,
                description="Route to HR for employee records and policy compliance"
            ),
            
            DocumentType.INSURANCE_DOCUMENT: RoutingDestination(
                department="Risk Management",
                system="Insurance Management System",
                email="risk@company.com",
                priority=Priority.HIGH,
                sla_hours=24,
                description="Route to risk management for coverage analysis and claims processing"
            ),
            
            DocumentType.MEDICAL_DOCUMENT: RoutingDestination(
                department="Benefits Administration",
                system="Benefits Management System",
                email="benefits@company.com",
                priority=Priority.HIGH,
                sla_hours=24,
                description="Route to benefits for health plan administration and claims"
            ),
            
            DocumentType.UNKNOWN: RoutingDestination(
                department="Document Review Team",
                system="Manual Review Queue",
                email="docreview@company.com",
                priority=Priority.LOW,
                sla_hours=120,
                description="Route to document review team for manual classification"
            )
        }
    
    def classify_document(self, text: str, extracted_entities: List[Dict] = None) -> ClassificationResult:
        """
        Classify a document and determine routing destination
        
        Args:
            text: The extracted text from the document
            extracted_entities: Previously extracted entities from NER
            
        Returns:
            ClassificationResult with document type and routing information
        """
        if not text or not text.strip():
            return self._create_unknown_result("Empty or invalid text")
        
        # Normalize text for analysis
        text_lower = text.lower()
        
        # Calculate scores for each document type
        scores = {}
        processing_notes = []
        
        for doc_type, patterns in self.classification_patterns.items():
            score = self._calculate_classification_score(
                text_lower, patterns, extracted_entities
            )
            scores[doc_type] = score
        
        # Find the best match
        best_type = max(scores.keys(), key=lambda k: scores[k])
        best_score = scores[best_type]
        
        # Set confidence threshold
        confidence_threshold = 0.3
        
        if best_score < confidence_threshold:
            processing_notes.append(f"Low confidence score: {best_score:.2f}")
            return self._create_unknown_result("Classification confidence below threshold", processing_notes)
        
        # Extract metadata specific to document type
        metadata = self._extract_document_metadata(text, best_type, extracted_entities)
        
        # Add processing notes
        processing_notes.append(f"Classified as {best_type.value} with {best_score:.2f} confidence")
        processing_notes.append(f"Matched {len([k for k, v in scores.items() if v > 0])} document patterns")
        
        return ClassificationResult(
            document_type=best_type,
            confidence=best_score,
            routing=self.routing_destinations[best_type],
            extracted_metadata=metadata,
            processing_notes=processing_notes
        )
    
    def _calculate_classification_score(self, text: str, patterns: Dict, entities: List[Dict] = None) -> float:
        """Calculate classification score for a document type"""
        score = 0.0
        
        # Keyword matching
        keyword_matches = 0
        for keyword in patterns['keywords']:
            if keyword.lower() in text:
                keyword_matches += 1
        
        keyword_score = (keyword_matches / len(patterns['keywords'])) * 0.4
        
        # Pattern matching
        pattern_matches = 0
        for pattern in patterns['patterns']:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_matches += 1
        
        pattern_score = (pattern_matches / len(patterns['patterns'])) * 0.4
        
        # Entity matching
        entity_score = 0.0
        if entities and 'required_entities' in patterns:
            entity_types = [e.get('label', '') for e in entities]
            required_entities = patterns['required_entities']
            
            matched_entities = sum(1 for req_entity in required_entities 
                                 if req_entity in entity_types)
            
            entity_score = (matched_entities / len(required_entities)) * 0.2
        
        # Apply document type weight
        weight = patterns.get('weight', 1.0)
        total_score = (keyword_score + pattern_score + entity_score) * weight
        
        return min(total_score, 1.0)  # Cap at 1.0
    
    def _extract_document_metadata(self, text: str, doc_type: DocumentType, entities: List[Dict] = None) -> Dict:
        """Extract metadata specific to document type"""
        metadata = {}
        
        if doc_type == DocumentType.INVOICE:
            metadata.update(self._extract_invoice_metadata(text, entities))
        elif doc_type == DocumentType.CONTRACT:
            metadata.update(self._extract_contract_metadata(text, entities))
        elif doc_type == DocumentType.PURCHASE_ORDER:
            metadata.update(self._extract_po_metadata(text, entities))
        # Add more specific extractors as needed
        
        return metadata
    
    def _extract_invoice_metadata(self, text: str, entities: List[Dict] = None) -> Dict:
        """Extract invoice-specific metadata"""
        metadata = {}
        
        # Extract invoice number
        inv_patterns = [
            r'invoice\s*#?\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'inv\s*#?\s*[:\-]?\s*([A-Z0-9\-]+)'
        ]
        
        for pattern in inv_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['invoice_number'] = match.group(1)
                break
        
        # Extract amounts
        if entities:
            amounts = [e['text'] for e in entities if e.get('label') == 'MONEY' or e.get('label') == 'Amount']
            if amounts:
                metadata['amounts'] = amounts
                # Try to identify total amount (usually the largest)
                try:
                    numeric_amounts = []
                    for amount in amounts:
                        # Clean and convert to float
                        clean_amount = re.sub(r'[^\d.]', '', amount)
                        if clean_amount:
                            numeric_amounts.append(float(clean_amount))
                    
                    if numeric_amounts:
                        metadata['total_amount'] = max(numeric_amounts)
                except:
                    pass
        
        # Extract vendor information
        vendor_patterns = [
            r'from\s*[:\-]?\s*([A-Za-z\s&.,]+?)(?:\n|$)',
            r'vendor\s*[:\-]?\s*([A-Za-z\s&.,]+?)(?:\n|$)'
        ]
        
        for pattern in vendor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['vendor'] = match.group(1).strip()
                break
        
        return metadata
    
    def _extract_contract_metadata(self, text: str, entities: List[Dict] = None) -> Dict:
        """Extract contract-specific metadata"""
        metadata = {}
        
        # Extract parties
        if entities:
            parties = [e['text'] for e in entities if e.get('label') in ['PERSON', 'ORG']]
            if parties:
                metadata['parties'] = parties[:2]  # Usually two main parties
        
        # Extract effective date
        effective_date_pattern = r'effective\s*date\s*[:\-]?\s*([A-Za-z0-9\s,]+)'
        match = re.search(effective_date_pattern, text, re.IGNORECASE)
        if match:
            metadata['effective_date'] = match.group(1).strip()
        
        # Extract contract type
        contract_types = ['service agreement', 'employment contract', 'lease agreement', 
                         'purchase agreement', 'licensing agreement']
        
        for contract_type in contract_types:
            if contract_type.lower() in text.lower():
                metadata['contract_type'] = contract_type
                break
        
        return metadata
    
    def _extract_po_metadata(self, text: str, entities: List[Dict] = None) -> Dict:
        """Extract purchase order specific metadata"""
        metadata = {}
        
        # Extract PO number
        po_patterns = [
            r'purchase\s*order\s*#?\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'po\s*#?\s*[:\-]?\s*([A-Z0-9\-]+)'
        ]
        
        for pattern in po_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['po_number'] = match.group(1)
                break
        
        # Extract vendor
        if entities:
            orgs = [e['text'] for e in entities if e.get('label') == 'ORG']
            if orgs:
                metadata['vendor'] = orgs[0]  # First organization is likely the vendor
        
        return metadata
    
    def _create_unknown_result(self, reason: str, notes: List[str] = None) -> ClassificationResult:
        """Create a result for unknown document type"""
        processing_notes = notes or []
        processing_notes.append(f"Classification failed: {reason}")
        
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            routing=self.routing_destinations[DocumentType.UNKNOWN],
            extracted_metadata={},
            processing_notes=processing_notes
        )
    
    def get_routing_summary(self) -> pd.DataFrame:
        """Get a summary of all routing destinations"""
        data = []
        for doc_type, routing in self.routing_destinations.items():
            data.append({
                'Document Type': doc_type.value.replace('_', ' ').title(),
                'Department': routing.department,
                'System': routing.system,
                'Email': routing.email,
                'Priority': routing.priority.value.title(),
                'SLA (Hours)': routing.sla_hours,
                'Description': routing.description
            })
        
        return pd.DataFrame(data)
    
    def simulate_routing_workflow(self, classification_result: ClassificationResult) -> Dict:
        """Simulate the routing workflow for a classified document"""
        routing = classification_result.routing
        
        workflow_steps = []
        
        # Step 1: Document received
        workflow_steps.append({
            'step': 1,
            'action': 'Document Received',
            'description': f'Document classified as {classification_result.document_type.value}',
            'timestamp': 'T+0 minutes',
            'status': 'completed'
        })
        
        # Step 2: Automatic routing
        workflow_steps.append({
            'step': 2,
            'action': 'Automatic Routing',
            'description': f'Routed to {routing.department} ({routing.system})',
            'timestamp': 'T+1 minute',
            'status': 'completed'
        })
        
        # Step 3: Email notification
        workflow_steps.append({
            'step': 3,
            'action': 'Email Notification',
            'description': f'Notification sent to {routing.email}',
            'timestamp': 'T+2 minutes',
            'status': 'completed'
        })
        
        # Step 4: Queue assignment
        workflow_steps.append({
            'step': 4,
            'action': 'Queue Assignment',
            'description': f'Added to {routing.priority.value} priority queue',
            'timestamp': 'T+3 minutes',
            'status': 'completed'
        })
        
        # Step 5: SLA tracking
        workflow_steps.append({
            'step': 5,
            'action': 'SLA Tracking',
            'description': f'SLA timer started ({routing.sla_hours} hours)',
            'timestamp': 'T+3 minutes',
            'status': 'in_progress'
        })
        
        # Step 6: Processing (future)
        workflow_steps.append({
            'step': 6,
            'action': 'Document Processing',
            'description': f'Awaiting processing by {routing.department}',
            'timestamp': f'Within {routing.sla_hours} hours',
            'status': 'pending'
        })
        
        return {
            'document_type': classification_result.document_type.value,
            'confidence': classification_result.confidence,
            'routing_destination': routing.department,
            'priority': routing.priority.value,
            'sla_hours': routing.sla_hours,
            'workflow_steps': workflow_steps,
            'metadata': classification_result.extracted_metadata
        }