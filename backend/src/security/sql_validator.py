"""
SQL Validator for SQL-Guard application
Validates SQL queries against security policies and detects injection attempts
"""
import re
import sqlparse
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from ..models.user import UserRole
from ..models.security_policy import PolicyType


class SQLInjectionType(str, Enum):
    """SQL injection attack types"""
    UNION_BASED = "UNION_BASED"
    BOOLEAN_BASED = "BOOLEAN_BASED"
    TIME_BASED = "TIME_BASED"
    ERROR_BASED = "ERROR_BASED"
    COMMENT_BASED = "COMMENT_BASED"
    FUNCTION_CALL = "FUNCTION_CALL"


@dataclass
class SQLValidationResult:
    """SQL validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    has_ddl: bool
    has_dml: bool
    has_where_clause: bool
    parameter_count: int
    estimated_cost: float
    security_checks: Dict[str, Any]
    injection_attempts: List[SQLInjectionType]


class SQLValidator:
    """SQL query validator with security checks"""

    def __init__(self):
        # SQL injection patterns
        self.injection_patterns = {
            SQLInjectionType.UNION_BASED: [
                r'\bUNION\s+SELECT\b',
                r'\bUNION\s+ALL\s+SELECT\b',
                r'\bUNION\s+DISTINCT\s+SELECT\b'
            ],
            SQLInjectionType.BOOLEAN_BASED: [
                r'\bOR\s+1\s*=\s*1\b',
                r'\bOR\s+true\b',
                r'\bAND\s+1\s*=\s*1\b',
                r'\bOR\s+\d+\s*=\s*\d+\b'
            ],
            SQLInjectionType.TIME_BASED: [
                r'\bWAITFOR\s+DELAY\b',
                r'\bSLEEP\s*\(\s*\d+\s*\)',
                r'\bPG_SLEEP\s*\(\s*\d+\s*\)',
                r'\bBENCHMARK\s*\(\s*\d+\s*,\s*.*\s*\)'
            ],
            SQLInjectionType.ERROR_BASED: [
                r'\bEXTRACTVALUE\s*\(',
                r'\bUPDATEXML\s*\(',
                r'\bCONVERT\s*\(.*\s*,\s*.*\s*\)',
                r'\bCAST\s*\(.*\s*AS\s*.*\s*\)'
            ],
            SQLInjectionType.COMMENT_BASED: [
                r'--.*$',
                r'/\*.*\*/',
                r';\s*--',
                r';\s*/\*'
            ],
            SQLInjectionType.FUNCTION_CALL: [
                r'\bEXEC\s+',
                r'\bEXECUTE\s+',
                r'\bXP_CMDSHELL\s*\(',
                r'\bSP_EXECUTESQL\s*\(',
                r'\bEVAL\s*\(',
                r'\bLOAD_FILE\s*\('
            ]
        }

        # DDL keywords
        self.ddl_keywords = {
            'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'RENAME', 'COMMENT',
            'GRANT', 'REVOKE', 'SET', 'RESET'
        }

        # DML keywords
        self.dml_keywords = {
            'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'UPSERT'
        }

        # DCL keywords
        self.dcl_keywords = {
            'GRANT', 'REVOKE', 'DENY'
        }

        # Dangerous function patterns
        self.dangerous_functions = {
            'LOAD_FILE', 'INTO OUTFILE', 'INTO DUMPFILE',
            'XP_CMDSHELL', 'SP_EXECUTESQL', 'EXEC',
            'EVAL', 'EXECUTE', 'CALL'
        }

    def validate_sql(self, sql: str, user_role: UserRole, 
                    database_id: Optional[str] = None) -> SQLValidationResult:
        """
        Validate SQL query against security policies
        
        Args:
            sql: SQL query to validate
            user_role: User role for permission checking
            database_id: Target database ID
            
        Returns:
            SQLValidationResult with validation details
        """
        errors = []
        warnings = []
        injection_attempts = []

        # Parse SQL
        try:
            parsed = sqlparse.parse(sql.strip())
            if not parsed:
                errors.append("Empty SQL query")
                return SQLValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    has_ddl=False,
                    has_dml=False,
                    has_where_clause=False,
                    parameter_count=0,
                    estimated_cost=0.0,
                    security_checks={},
                    injection_attempts=injection_attempts
                )

            statement = parsed[0]
        except Exception as e:
            errors.append(f"SQL parsing error: {str(e)}")
            return SQLValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                has_ddl=False,
                has_dml=False,
                has_where_clause=False,
                parameter_count=0,
                estimated_cost=0.0,
                security_checks={},
                injection_attempts=injection_attempts
            )

        # Check for SQL injection attempts
        injection_attempts = self._detect_sql_injection(sql)
        if injection_attempts:
            errors.append("SQL injection attempt detected")
            for attempt in injection_attempts:
                errors.append(f"Injection type: {attempt.value}")

        # Analyze SQL structure
        has_ddl = self._has_ddl_statements(statement)
        has_dml = self._has_dml_statements(statement)
        has_where_clause = self._has_where_clause(statement)
        parameter_count = self._count_parameters(sql)

        # Check permissions based on user role
        if user_role == UserRole.VIEWER:
            if has_ddl:
                errors.append("DDL operations not allowed for VIEWER role")
            if has_dml:
                errors.append("DML operations not allowed for VIEWER role")

        # Check for dangerous patterns
        if self._has_dangerous_functions(sql):
            errors.append("Dangerous function calls detected")

        # Check for UPDATE/DELETE without WHERE clause
        if has_dml and not has_where_clause:
            if self._has_update_or_delete_without_where(sql):
                errors.append("UPDATE/DELETE without WHERE clause not allowed")

        # Estimate query cost
        estimated_cost = self._estimate_query_cost(statement)

        # Security checks summary
        security_checks = {
            "has_ddl": has_ddl,
            "has_dml": has_dml,
            "has_where_clause": has_where_clause,
            "parameter_count": parameter_count,
            "has_dangerous_functions": self._has_dangerous_functions(sql),
            "injection_attempts": len(injection_attempts),
            "estimated_cost": estimated_cost
        }

        is_valid = len(errors) == 0

        return SQLValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            has_ddl=has_ddl,
            has_dml=has_dml,
            has_where_clause=has_where_clause,
            parameter_count=parameter_count,
            estimated_cost=estimated_cost,
            security_checks=security_checks,
            injection_attempts=injection_attempts
        )

    def _detect_sql_injection(self, sql: str) -> List[SQLInjectionType]:
        """Detect SQL injection attempts in the query"""
        injection_attempts = []
        sql_upper = sql.upper()

        for injection_type, patterns in self.injection_patterns.items():
            for pattern in patterns:
                if re.search(pattern, sql_upper, re.IGNORECASE):
                    injection_attempts.append(injection_type)
                    break

        return injection_attempts

    def _has_ddl_statements(self, statement) -> bool:
        """Check if statement contains DDL keywords"""
        tokens = [token.value.upper() if token.value else None for token in statement.flatten()]
        
        for token in tokens:
            if token in self.ddl_keywords:
                return True
                
        return False

    def _has_dml_statements(self, statement) -> bool:
        """Check if statement contains DML keywords"""
        tokens = [token.value.upper() if token.value else None for token in statement.flatten()]
        
        for token in tokens:
            if token in self.dml_keywords:
                return True
                
        return False

    def _has_where_clause(self, statement) -> bool:
        """Check if statement has WHERE clause"""
        tokens = [token.value.upper() if token.value else None for token in statement.flatten()]
        return 'WHERE' in tokens

    def _count_parameters(self, sql: str) -> int:
        """Count parameter placeholders in SQL"""
        # Count named parameters (:param)
        named_params = len(re.findall(r':\w+', sql))
        # Count positional parameters (%s, $1, etc.)
        positional_params = len(re.findall(r'%s|\$\d+|\?', sql))
        return named_params + positional_params

    def _has_dangerous_functions(self, sql: str) -> bool:
        """Check for dangerous function calls"""
        sql_upper = sql.upper()
        for func in self.dangerous_functions:
            if func in sql_upper:
                return True
        return False

    def _has_update_or_delete_without_where(self, sql: str) -> bool:
        """Check for UPDATE/DELETE without WHERE clause"""
        sql_upper = sql.upper()
        
        # Simple check for UPDATE/DELETE without WHERE
        update_match = re.search(r'\bUPDATE\s+\w+', sql_upper)
        delete_match = re.search(r'\bDELETE\s+FROM\s+\w+', sql_upper)
        
        if update_match or delete_match:
            # Check if WHERE clause exists after the table name
            if update_match:
                table_end = update_match.end()
                remaining_sql = sql_upper[table_end:]
            else:
                table_end = delete_match.end()
                remaining_sql = sql_upper[table_end:]
            
            # Look for WHERE clause before any other major keywords
            where_match = re.search(r'\bWHERE\b', remaining_sql)
            if not where_match:
                return True
                
        return False

    def _estimate_query_cost(self, statement) -> float:
        """Estimate query execution cost"""
        # Simple cost estimation based on query complexity
        tokens = [token.value.upper() if token.value else None for token in statement.flatten()]
        
        cost = 1.0
        
        # JOIN operations increase cost
        join_count = tokens.count('JOIN')
        cost += join_count * 0.5
        
        # Subqueries increase cost
        subquery_count = tokens.count('SELECT') - 1  # Subtract main SELECT
        cost += subquery_count * 0.3
        
        # ORDER BY increases cost
        if 'ORDER BY' in tokens:
            cost += 0.2
            
        # GROUP BY increases cost
        if 'GROUP BY' in tokens:
            cost += 0.3
            
        # Aggregation functions increase cost
        agg_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']
        for func in agg_functions:
            cost += tokens.count(func) * 0.1
            
        return min(cost, 10.0)  # Cap at 10.0

    def validate_parameters(self, sql: str, parameters: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate parameter values against SQL query
        
        Args:
            sql: SQL query with parameters
            parameters: Parameter values
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Extract parameter names from SQL
        param_names = re.findall(r':(\w+)', sql)
        
        # Check for missing required parameters
        for param_name in param_names:
            if param_name not in parameters:
                errors.append(f"Missing required parameter: {param_name}")
        
        # Check for extra parameters
        for param_name in parameters:
            if param_name not in param_names:
                errors.append(f"Unused parameter: {param_name}")
        
        # Validate parameter types (basic validation)
        for param_name, param_value in parameters.items():
            if param_name in param_names:
                # Check for SQL injection in parameter values
                if isinstance(param_value, str):
                    if self._detect_sql_injection(param_value):
                        errors.append(f"SQL injection detected in parameter {param_name}")
                
                # Check for suspicious patterns
                if isinstance(param_value, str) and len(param_value) > 1000:
                    errors.append(f"Parameter {param_name} value too long")
        
        return len(errors) == 0, errors

    def sanitize_sql(self, sql: str) -> str:
        """
        Sanitize SQL query by removing dangerous patterns
        
        Args:
            sql: SQL query to sanitize
            
        Returns:
            Sanitized SQL query
        """
        # Remove comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Remove multiple semicolons
        sql = re.sub(r';+', ';', sql)
        
        # Remove leading/trailing whitespace
        sql = sql.strip()
        
        return sql

    def get_query_complexity_score(self, sql: str) -> float:
        """
        Calculate query complexity score (0-1)
        
        Args:
            sql: SQL query
            
        Returns:
            Complexity score between 0 and 1
        """
        tokens = [token.value.upper() if token.value else None for token in sqlparse.parse(sql)[0].flatten()]
        
        complexity = 0.0
        
        # Base complexity
        complexity += 0.1
        
        # JOIN complexity
        join_count = tokens.count('JOIN')
        complexity += min(join_count * 0.1, 0.3)
        
        # Subquery complexity
        subquery_count = tokens.count('SELECT') - 1
        complexity += min(subquery_count * 0.15, 0.3)
        
        # Aggregation complexity
        agg_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT']
        for func in agg_functions:
            complexity += tokens.count(func) * 0.05
        
        # Window function complexity
        if 'OVER' in tokens:
            complexity += 0.2
        
        # CTE complexity
        if 'WITH' in tokens:
            complexity += 0.1
        
        return min(complexity, 1.0)

    def extract_table_names(self, sql: str) -> List[str]:
        """
        Extract table names from SQL query
        
        Args:
            sql: SQL query
            
        Returns:
            List of table names
        """
        try:
            parsed = sqlparse.parse(sql)[0]
            tables = []
            
            # Simple extraction - look for identifiers after FROM, JOIN, UPDATE, INSERT INTO
            tokens = [token.value.upper() if token.value else None for token in parsed.flatten()]
            
            for i, token in enumerate(tokens):
                if token in ['FROM', 'JOIN', 'UPDATE', 'INTO']:
                    if i + 1 < len(tokens):
                        table_name = tokens[i + 1]
                        # Remove schema prefix if present
                        if '.' in table_name:
                            table_name = table_name.split('.')[-1]
                        tables.append(table_name.lower())
            
            return list(set(tables))  # Remove duplicates
            
        except Exception:
            return []

    def extract_column_names(self, sql: str) -> List[str]:
        """
        Extract column names from SQL query
        
        Args:
            sql: SQL query
            
        Returns:
            List of column names
        """
        try:
            parsed = sqlparse.parse(sql)[0]
            columns = []
            
            # Look for column references in SELECT clause
            tokens = [token.value for token in parsed.flatten()]
            
            in_select = False
            for i, token in enumerate(tokens):
                if token.upper() == 'SELECT':
                    in_select = True
                elif token.upper() in ['FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING']:
                    in_select = False
                elif in_select and token not in [',', '(', ')', 'AS', 'DISTINCT']:
                    # Simple column name extraction
                    if '.' in token:
                        column_name = token.split('.')[-1]
                    else:
                        column_name = token
                    columns.append(column_name.lower())
            
            return list(set(columns))  # Remove duplicates
            
        except Exception:
            return []