"""
PII Masker for SQL-Guard application
Masks personally identifiable information in query results and logs
"""
import re
import hashlib
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class PIIType(str, Enum):
    """PII type enumeration"""
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    IP_ADDRESS = "IP_ADDRESS"
    NAME = "NAME"
    ADDRESS = "ADDRESS"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    PASSPORT = "PASSPORT"
    DRIVER_LICENSE = "DRIVER_LICENSE"


@dataclass
class PIIPattern:
    """PII detection pattern"""
    pii_type: PIIType
    pattern: str
    mask: str
    description: str


@dataclass
class PIIMatch:
    """PII match result"""
    pii_type: PIIType
    original_value: str
    masked_value: str
    confidence: float
    position: tuple[int, int]


class PIIMasker:
    """PII detection and masking utility"""

    def __init__(self):
        # Default PII patterns
        self.pii_patterns = [
            PIIPattern(
                pii_type=PIIType.EMAIL,
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                mask='***@***.com',
                description='Email address'
            ),
            PIIPattern(
                pii_type=PIIType.PHONE,
                pattern=r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                mask='***-***-****',
                description='Phone number'
            ),
            PIIPattern(
                pii_type=PIIType.SSN,
                pattern=r'\b\d{3}-?\d{2}-?\d{4}\b',
                mask='***-**-****',
                description='Social Security Number'
            ),
            PIIPattern(
                pii_type=PIIType.CREDIT_CARD,
                pattern=r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                mask='****-****-****-****',
                description='Credit card number'
            ),
            PIIPattern(
                pii_type=PIIType.IP_ADDRESS,
                pattern=r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                mask='***.***.***.***',
                description='IP address'
            ),
            PIIPattern(
                pii_type=PIIType.DATE_OF_BIRTH,
                pattern=r'\b(?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b',
                mask='**/**/****',
                description='Date of birth'
            ),
            PIIPattern(
                pii_type=PIIType.PASSPORT,
                pattern=r'\b[A-Z]{1,2}\d{6,9}\b',
                mask='**-******',
                description='Passport number'
            ),
            PIIPattern(
                pii_type=PIIType.DRIVER_LICENSE,
                pattern=r'\b[A-Z]\d{7,8}\b',
                mask='*-*******',
                description='Driver license number'
            )
        ]

        # Column name patterns that likely contain PII
        self.pii_column_patterns = {
            PIIType.EMAIL: [r'.*email.*', r'.*mail.*', r'.*e_mail.*'],
            PIIType.PHONE: [r'.*phone.*', r'.*tel.*', r'.*mobile.*', r'.*cell.*'],
            PIIType.SSN: [r'.*ssn.*', r'.*social.*', r'.*tax_id.*'],
            PIIType.CREDIT_CARD: [r'.*credit.*', r'.*card.*', r'.*payment.*'],
            PIIType.NAME: [r'.*name.*', r'.*first.*', r'.*last.*', r'.*given.*', r'.*family.*'],
            PIIType.ADDRESS: [r'.*address.*', r'.*street.*', r'.*city.*', r'.*zip.*', r'.*postal.*'],
            PIIType.DATE_OF_BIRTH: [r'.*birth.*', r'.*dob.*', r'.*date_of_birth.*'],
            PIIType.IP_ADDRESS: [r'.*ip.*', r'.*address.*']
        }

    def detect_pii(self, text: str) -> List[PIIMatch]:
        """
        Detect PII in text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of PII matches
        """
        matches = []
        
        for pattern in self.pii_patterns:
            regex = re.compile(pattern.pattern, re.IGNORECASE)
            for match in regex.finditer(text):
                matches.append(PIIMatch(
                    pii_type=pattern.pii_type,
                    original_value=match.group(),
                    masked_value=pattern.mask,
                    confidence=0.9,  # High confidence for regex matches
                    position=(match.start(), match.end())
                ))
        
        return matches

    def mask_pii_in_text(self, text: str, custom_patterns: Optional[List[PIIPattern]] = None) -> str:
        """
        Mask PII in text
        
        Args:
            text: Text to mask
            custom_patterns: Custom PII patterns to use
            
        Returns:
            Text with PII masked
        """
        patterns = custom_patterns or self.pii_patterns
        masked_text = text
        
        for pattern in patterns:
            regex = re.compile(pattern.pattern, re.IGNORECASE)
            masked_text = regex.sub(pattern.mask, masked_text)
        
        return masked_text

    def mask_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                  column_mapping: Optional[Dict[str, PIIType]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Mask PII in data structures
        
        Args:
            data: Data to mask (dict or list of dicts)
            column_mapping: Mapping of column names to PII types
            
        Returns:
            Masked data
        """
        if isinstance(data, list):
            return [self.mask_data(item, column_mapping) for item in data]
        
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Check column mapping first
                if column_mapping and key in column_mapping:
                    pii_type = column_mapping[key]
                    masked_value = self._mask_by_type(value, pii_type)
                else:
                    # Auto-detect PII in value
                    masked_value = self.mask_pii_in_text(value)
                
                masked_data[key] = masked_value
            elif isinstance(value, dict):
                masked_data[key] = self.mask_data(value, column_mapping)
            elif isinstance(value, list):
                masked_data[key] = [self.mask_data(item, column_mapping) if isinstance(item, dict) else item for item in value]
            else:
                masked_data[key] = value
        
        return masked_data

    def _mask_by_type(self, value: str, pii_type: PIIType) -> str:
        """Mask value by specific PII type"""
        for pattern in self.pii_patterns:
            if pattern.pii_type == pii_type:
                regex = re.compile(pattern.pattern, re.IGNORECASE)
                return regex.sub(pattern.mask, value)
        
        # Fallback to generic masking
        return self._generic_mask(value)

    def _generic_mask(self, value: str) -> str:
        """Generic masking for unrecognized PII"""
        if len(value) <= 4:
            return '*' * len(value)
        elif len(value) <= 8:
            return value[:2] + '*' * (len(value) - 4) + value[-2:]
        else:
            return value[:3] + '*' * (len(value) - 6) + value[-3:]

    def hash_pii(self, value: str, salt: Optional[str] = None) -> str:
        """
        Hash PII value for consistent anonymization
        
        Args:
            value: PII value to hash
            salt: Optional salt for hashing
            
        Returns:
            Hashed value
        """
        if salt:
            value_with_salt = value + salt
        else:
            value_with_salt = value
        
        return hashlib.sha256(value_with_salt.encode()).hexdigest()[:8]

    def get_column_pii_types(self, column_names: List[str]) -> Dict[str, List[PIIType]]:
        """
        Detect likely PII types for column names
        
        Args:
            column_names: List of column names
            
        Returns:
            Mapping of column names to likely PII types
        """
        column_pii_map = {}
        
        for column_name in column_names:
            column_lower = column_name.lower()
            detected_types = []
            
            for pii_type, patterns in self.pii_column_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, column_lower):
                        detected_types.append(pii_type)
                        break
            
            if detected_types:
                column_pii_map[column_name] = detected_types
        
        return column_pii_map

    def create_custom_pattern(self, pii_type: PIIType, pattern: str, 
                           mask: str, description: str) -> PIIPattern:
        """
        Create custom PII pattern
        
        Args:
            pii_type: Type of PII
            pattern: Regex pattern
            mask: Masking pattern
            description: Pattern description
            
        Returns:
            Custom PII pattern
        """
        return PIIPattern(
            pii_type=pii_type,
            pattern=pattern,
            mask=mask,
            description=description
        )

    def validate_pattern(self, pattern: str) -> bool:
        """
        Validate regex pattern
        
        Args:
            pattern: Regex pattern to validate
            
        Returns:
            True if pattern is valid
        """
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False

    def mask_sql_query(self, sql: str) -> str:
        """
        Mask PII in SQL query text
        
        Args:
            sql: SQL query
            
        Returns:
            SQL query with PII masked
        """
        return self.mask_pii_in_text(sql)

    def mask_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask PII in audit log data
        
        Args:
            log_data: Audit log data
            
        Returns:
            Masked audit log data
        """
        # Fields that commonly contain PII in audit logs
        pii_fields = ['user_agent', 'ip_address', 'details']
        
        masked_log = log_data.copy()
        
        for field in pii_fields:
            if field in masked_log and isinstance(masked_log[field], str):
                masked_log[field] = self.mask_pii_in_text(masked_log[field])
            elif field == 'details' and isinstance(masked_log[field], dict):
                masked_log[field] = self.mask_data(masked_log[field])
        
        return masked_log

    def get_masking_stats(self, original_data: Any, masked_data: Any) -> Dict[str, int]:
        """
        Get statistics about masking performed
        
        Args:
            original_data: Original data
            masked_data: Masked data
            
        Returns:
            Masking statistics
        """
        stats = {
            'total_fields': 0,
            'masked_fields': 0,
            'pii_detected': 0,
            'patterns_matched': {}
        }
        
        if isinstance(original_data, dict) and isinstance(masked_data, dict):
            for key in original_data:
                stats['total_fields'] += 1
                
                if key in masked_data:
                    original_value = str(original_data[key])
                    masked_value = str(masked_data[key])
                    
                    if original_value != masked_value:
                        stats['masked_fields'] += 1
                        
                        # Detect which PII types were found
                        matches = self.detect_pii(original_value)
                        stats['pii_detected'] += len(matches)
                        
                        for match in matches:
                            pii_type = match.pii_type.value
                            stats['patterns_matched'][pii_type] = stats['patterns_matched'].get(pii_type, 0) + 1
        
        return stats

    def is_pii_likely(self, column_name: str, sample_value: Optional[str] = None) -> bool:
        """
        Check if a column likely contains PII
        
        Args:
            column_name: Column name
            sample_value: Optional sample value
            
        Returns:
            True if column likely contains PII
        """
        column_lower = column_name.lower()
        
        # Check column name patterns
        for patterns in self.pii_column_patterns.values():
            for pattern in patterns:
                if re.match(pattern, column_lower):
                    return True
        
        # Check sample value if provided
        if sample_value:
            matches = self.detect_pii(sample_value)
            if matches:
                return True
        
        return False

    def get_pii_compliance_report(self, data: Any) -> Dict[str, Any]:
        """
        Generate PII compliance report
        
        Args:
            data: Data to analyze
            
        Returns:
            Compliance report
        """
        report = {
            'total_records': 0,
            'pii_fields_found': [],
            'compliance_score': 0.0,
            'recommendations': []
        }
        
        if isinstance(data, list):
            report['total_records'] = len(data)
            
            if data:
                # Analyze first record to identify PII fields
                sample_record = data[0]
                if isinstance(sample_record, dict):
                    for field_name, field_value in sample_record.items():
                        if isinstance(field_value, str) and self.is_pii_likely(field_name, field_value):
                            report['pii_fields_found'].append({
                                'field': field_name,
                                'pii_type': 'DETECTED',
                                'sample_value': field_value[:50] + '...' if len(field_value) > 50 else field_value
                            })
        
        # Calculate compliance score
        if report['total_records'] > 0:
            pii_field_ratio = len(report['pii_fields_found']) / len(data[0]) if data else 0
            report['compliance_score'] = max(0.0, 1.0 - pii_field_ratio)
        
        # Generate recommendations
        if report['pii_fields_found']:
            report['recommendations'].append("Consider masking PII fields in query results")
            report['recommendations'].append("Review data access permissions for sensitive fields")
        
        return report