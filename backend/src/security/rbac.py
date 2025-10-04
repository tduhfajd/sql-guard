"""
Role-Based Access Control (RBAC) service for SQL-Guard application
Manages user permissions and access control
"""
from typing import Dict, List, Optional, Set, Any
from enum import Enum
from dataclasses import dataclass

from ..models.user import User, UserRole, USER_PERMISSIONS, get_user_permissions, has_permission
from ..models.database_connection import ConnectionType
from ..models.sql_template import TemplateStatus


class Permission(str, Enum):
    """System permissions enumeration"""
    # Query execution permissions
    EXECUTE_SELECT_QUERIES = "execute_select_queries"
    EXECUTE_APPROVED_TEMPLATES = "execute_approved_templates"
    EXECUTE_DDL_STATEMENTS = "execute_ddl_statements"
    EXECUTE_DML_STATEMENTS = "execute_dml_statements"
    
    # Template management permissions
    CREATE_TEMPLATES = "create_templates"
    UPDATE_TEMPLATES = "update_templates"
    DELETE_TEMPLATES = "delete_templates"
    VIEW_ALL_TEMPLATES = "view_all_templates"
    VIEW_APPROVED_TEMPLATES = "view_approved_templates"
    
    # Approval workflow permissions
    APPROVE_TEMPLATES = "approve_templates"
    VIEW_APPROVAL_QUEUE = "view_approval_queue"
    SUBMIT_FOR_APPROVAL = "submit_for_approval"
    
    # User management permissions
    MANAGE_USERS = "manage_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    VIEW_ALL_USERS = "view_all_users"
    
    # Database management permissions
    MANAGE_DATABASE_CONNECTIONS = "manage_database_connections"
    CREATE_DATABASE_CONNECTIONS = "create_database_connections"
    UPDATE_DATABASE_CONNECTIONS = "update_database_connections"
    DELETE_DATABASE_CONNECTIONS = "delete_database_connections"
    TEST_DATABASE_CONNECTIONS = "test_database_connections"
    
    # Security and policy permissions
    CONFIGURE_SECURITY_POLICIES = "configure_security_policies"
    VIEW_SECURITY_POLICIES = "view_security_policies"
    MANAGE_SECURITY_POLICIES = "manage_security_policies"
    
    # Audit and monitoring permissions
    VIEW_ALL_AUDIT_LOGS = "view_all_audit_logs"
    VIEW_OWN_AUDIT_LOGS = "view_own_audit_logs"
    EXPORT_AUDIT_LOGS = "export_audit_logs"
    VIEW_SYSTEM_STATISTICS = "view_system_statistics"
    
    # System administration permissions
    SYSTEM_ADMINISTRATION = "system_administration"
    CONFIGURE_SYSTEM = "configure_system"
    VIEW_SYSTEM_HEALTH = "view_system_health"


@dataclass
class AccessContext:
    """Access control context"""
    user_id: str
    user_role: UserRole
    database_id: Optional[str] = None
    schema_name: Optional[str] = None
    table_name: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None


class RBACService:
    """Role-Based Access Control service"""

    def __init__(self):
        # Extended permissions mapping
        self.extended_permissions = {
            UserRole.VIEWER: [
                Permission.EXECUTE_SELECT_QUERIES,
                Permission.VIEW_APPROVED_TEMPLATES,
                Permission.VIEW_OWN_AUDIT_LOGS
            ],
            UserRole.OPERATOR: [
                Permission.EXECUTE_SELECT_QUERIES,
                Permission.EXECUTE_APPROVED_TEMPLATES,
                Permission.VIEW_APPROVED_TEMPLATES,
                Permission.VIEW_OWN_AUDIT_LOGS,
                Permission.SUBMIT_FOR_APPROVAL
            ],
            UserRole.APPROVER: [
                Permission.EXECUTE_SELECT_QUERIES,
                Permission.EXECUTE_APPROVED_TEMPLATES,
                Permission.VIEW_ALL_TEMPLATES,
                Permission.APPROVE_TEMPLATES,
                Permission.VIEW_APPROVAL_QUEUE,
                Permission.VIEW_ALL_AUDIT_LOGS,
                Permission.VIEW_SYSTEM_STATISTICS
            ],
            UserRole.ADMIN: [
                Permission.EXECUTE_SELECT_QUERIES,
                Permission.EXECUTE_APPROVED_TEMPLATES,
                Permission.EXECUTE_DDL_STATEMENTS,
                Permission.EXECUTE_DML_STATEMENTS,
                Permission.CREATE_TEMPLATES,
                Permission.UPDATE_TEMPLATES,
                Permission.DELETE_TEMPLATES,
                Permission.VIEW_ALL_TEMPLATES,
                Permission.APPROVE_TEMPLATES,
                Permission.VIEW_APPROVAL_QUEUE,
                Permission.SUBMIT_FOR_APPROVAL,
                Permission.MANAGE_USERS,
                Permission.CREATE_USERS,
                Permission.UPDATE_USERS,
                Permission.DELETE_USERS,
                Permission.VIEW_ALL_USERS,
                Permission.MANAGE_DATABASE_CONNECTIONS,
                Permission.CREATE_DATABASE_CONNECTIONS,
                Permission.UPDATE_DATABASE_CONNECTIONS,
                Permission.DELETE_DATABASE_CONNECTIONS,
                Permission.TEST_DATABASE_CONNECTIONS,
                Permission.CONFIGURE_SECURITY_POLICIES,
                Permission.VIEW_SECURITY_POLICIES,
                Permission.MANAGE_SECURITY_POLICIES,
                Permission.VIEW_ALL_AUDIT_LOGS,
                Permission.EXPORT_AUDIT_LOGS,
                Permission.VIEW_SYSTEM_STATISTICS,
                Permission.SYSTEM_ADMINISTRATION,
                Permission.CONFIGURE_SYSTEM,
                Permission.VIEW_SYSTEM_HEALTH
            ]
        }

        # Database access restrictions
        self.database_access_restrictions = {
            UserRole.VIEWER: {
                'allowed_types': [ConnectionType.PRODUCTION, ConnectionType.STAGING],
                'read_only': True,
                'max_connections': 5
            },
            UserRole.OPERATOR: {
                'allowed_types': [ConnectionType.PRODUCTION, ConnectionType.STAGING],
                'read_only': True,
                'max_connections': 10
            },
            UserRole.APPROVER: {
                'allowed_types': [ConnectionType.PRODUCTION, ConnectionType.STAGING, ConnectionType.DEVELOPMENT],
                'read_only': False,
                'max_connections': 15
            },
            UserRole.ADMIN: {
                'allowed_types': [ConnectionType.PRODUCTION, ConnectionType.STAGING, ConnectionType.DEVELOPMENT, ConnectionType.AUDIT],
                'read_only': False,
                'max_connections': 50
            }
        }

        # Schema access restrictions
        self.schema_access_restrictions = {
            UserRole.VIEWER: ['public'],
            UserRole.OPERATOR: ['public'],
            UserRole.APPROVER: ['public', 'staging'],
            UserRole.ADMIN: ['public', 'staging', 'admin', 'audit']
        }

    def can_execute_query(self, user: User, sql_query: str) -> bool:
        """Check if user can execute SQL query"""
        if not user.is_active:
            return False
        
        # Check basic query execution permission
        if not self.has_permission(user.role, Permission.EXECUTE_SELECT_QUERIES):
            return False
        
        # Check for DDL/DML permissions
        sql_upper = sql_query.upper()
        
        # DDL check
        ddl_keywords = ['CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE']
        if any(keyword in sql_upper for keyword in ddl_keywords):
            return self.has_permission(user.role, Permission.EXECUTE_DDL_STATEMENTS)
        
        # DML check
        dml_keywords = ['INSERT', 'UPDATE', 'DELETE', 'MERGE']
        if any(keyword in sql_upper for keyword in dml_keywords):
            return self.has_permission(user.role, Permission.EXECUTE_DML_STATEMENTS)
        
        return True

    def can_create_template(self, user: User) -> bool:
        """Check if user can create templates"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.CREATE_TEMPLATES)

    def can_update_template(self, user: User, template_creator_id: str) -> bool:
        """Check if user can update template"""
        if not user.is_active:
            return False
        
        # Users can update their own templates, admins can update any
        if user.id == template_creator_id:
            return True
        
        return self.has_permission(user.role, Permission.UPDATE_TEMPLATES)

    def can_delete_template(self, user: User, template_creator_id: str) -> bool:
        """Check if user can delete template"""
        if not user.is_active:
            return False
        
        # Users can delete their own templates, admins can delete any
        if user.id == template_creator_id:
            return True
        
        return self.has_permission(user.role, Permission.DELETE_TEMPLATES)

    def can_execute_template(self, user: User, template_status: TemplateStatus) -> bool:
        """Check if user can execute template"""
        if not user.is_active:
            return False
        
        # Only approved templates can be executed
        if template_status != TemplateStatus.APPROVED:
            return False
        
        return self.has_permission(user.role, Permission.EXECUTE_APPROVED_TEMPLATES)

    def can_approve_template(self, user: User) -> bool:
        """Check if user can approve templates"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.APPROVE_TEMPLATES)

    def can_view_approvals(self, user: User) -> bool:
        """Check if user can view approval queue"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.VIEW_APPROVAL_QUEUE)

    def can_manage_users(self, user: User) -> bool:
        """Check if user can manage users"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.MANAGE_USERS)

    def can_create_user(self, user: User) -> bool:
        """Check if user can create users"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.CREATE_USERS)

    def can_update_user(self, user: User) -> bool:
        """Check if user can update users"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.UPDATE_USERS)

    def can_delete_user(self, user: User) -> bool:
        """Check if user can delete users"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.DELETE_USERS)

    def can_access_database(self, user: User, database_type: ConnectionType) -> bool:
        """Check if user can access database type"""
        if not user.is_active:
            return False
        
        restrictions = self.database_access_restrictions.get(user.role, {})
        allowed_types = restrictions.get('allowed_types', [])
        
        return database_type in allowed_types

    def can_access_schema(self, user: User, schema_name: str) -> bool:
        """Check if user can access schema"""
        if not user.is_active:
            return False
        
        allowed_schemas = self.schema_access_restrictions.get(user.role, [])
        return schema_name.lower() in allowed_schemas

    def can_view_audit_logs(self, user: User, target_user_id: Optional[str] = None) -> bool:
        """Check if user can view audit logs"""
        if not user.is_active:
            return False
        
        # Users can view their own logs
        if target_user_id == user.id:
            return self.has_permission(user.role, Permission.VIEW_OWN_AUDIT_LOGS)
        
        # Check if user can view all logs
        return self.has_permission(user.role, Permission.VIEW_ALL_AUDIT_LOGS)

    def can_view_all_audit_logs(self, user: User) -> bool:
        """Check if user can view all audit logs"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.VIEW_ALL_AUDIT_LOGS)

    def can_export_audit_logs(self, user: User) -> bool:
        """Check if user can export audit logs"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.EXPORT_AUDIT_LOGS)

    def can_configure_policies(self, user: User) -> bool:
        """Check if user can configure security policies"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.CONFIGURE_SECURITY_POLICIES)

    def can_manage_database_connections(self, user: User) -> bool:
        """Check if user can manage database connections"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.MANAGE_DATABASE_CONNECTIONS)

    def can_view_system_statistics(self, user: User) -> bool:
        """Check if user can view system statistics"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.VIEW_SYSTEM_STATISTICS)

    def can_perform_system_administration(self, user: User) -> bool:
        """Check if user can perform system administration"""
        if not user.is_active:
            return False
        
        return self.has_permission(user.role, Permission.SYSTEM_ADMINISTRATION)

    def has_permission(self, user_role: UserRole, permission: Permission) -> bool:
        """Check if user role has specific permission"""
        role_permissions = self.extended_permissions.get(user_role, [])
        return permission in role_permissions

    def get_user_permissions(self, user_role: UserRole) -> List[Permission]:
        """Get all permissions for user role"""
        return self.extended_permissions.get(user_role, [])

    def get_role_hierarchy(self) -> Dict[UserRole, List[UserRole]]:
        """Get role hierarchy (roles that inherit from others)"""
        return {
            UserRole.VIEWER: [],
            UserRole.OPERATOR: [UserRole.VIEWER],
            UserRole.APPROVER: [UserRole.OPERATOR, UserRole.VIEWER],
            UserRole.ADMIN: [UserRole.APPROVER, UserRole.OPERATOR, UserRole.VIEWER]
        }

    def can_inherit_permissions(self, from_role: UserRole, to_role: UserRole) -> bool:
        """Check if one role can inherit permissions from another"""
        hierarchy = self.get_role_hierarchy()
        return from_role in hierarchy.get(to_role, [])

    def get_effective_permissions(self, user_role: UserRole) -> Set[Permission]:
        """Get all effective permissions for role (including inherited)"""
        permissions = set(self.get_user_permissions(user_role))
        
        # Add inherited permissions
        hierarchy = self.get_role_hierarchy()
        for inherited_role in hierarchy.get(user_role, []):
            permissions.update(self.get_user_permissions(inherited_role))
        
        return permissions

    def validate_access_context(self, context: AccessContext) -> bool:
        """Validate access context"""
        # Check if user is active
        if not context.user_id:
            return False
        
        # Check database access
        if context.database_id:
            # This would typically check against actual database type
            # For now, we'll assume it's valid if user has query execution permission
            if not self.has_permission(context.user_role, Permission.EXECUTE_SELECT_QUERIES):
                return False
        
        # Check schema access
        if context.schema_name:
            if not self.can_access_schema(User(id=context.user_id, role=context.user_role, is_active=True), context.schema_name):
                return False
        
        return True

    def get_access_summary(self, user: User) -> Dict[str, Any]:
        """Get comprehensive access summary for user"""
        return {
            'user_id': user.id,
            'role': user.role,
            'is_active': user.is_active,
            'permissions': [p.value for p in self.get_effective_permissions(user.role)],
            'database_access': self.database_access_restrictions.get(user.role, {}),
            'schema_access': self.schema_access_restrictions.get(user.role, []),
            'can_execute_queries': self.can_execute_query(user, "SELECT 1"),
            'can_manage_users': self.can_manage_users(user),
            'can_approve_templates': self.can_approve_template(user),
            'can_view_all_audit_logs': self.can_view_all_audit_logs(user),
            'can_configure_policies': self.can_configure_policies(user)
        }

    def check_resource_access(self, user: User, resource_type: str, resource_id: str) -> bool:
        """Check if user can access specific resource"""
        if not user.is_active:
            return False
        
        if resource_type == 'template':
            # Users can access their own templates, admins can access all
            return self.has_permission(user.role, Permission.VIEW_ALL_TEMPLATES)
        
        elif resource_type == 'user':
            # Users can view their own profile, admins can view all
            if resource_id == user.id:
                return True
            return self.has_permission(user.role, Permission.VIEW_ALL_USERS)
        
        elif resource_type == 'database':
            # Check database access permissions
            return self.has_permission(user.role, Permission.MANAGE_DATABASE_CONNECTIONS)
        
        elif resource_type == 'audit_log':
            # Check audit log access permissions
            return self.can_view_audit_logs(user, resource_id)
        
        return False

    def get_restricted_columns(self, user: User, table_name: str) -> List[str]:
        """Get list of columns user cannot access"""
        # This would typically be configured per table/user
        # For now, return empty list (no restrictions)
        return []

    def get_query_restrictions(self, user: User) -> Dict[str, Any]:
        """Get query execution restrictions for user"""
        restrictions = {
            'max_execution_time': 30,  # seconds
            'max_rows': 1000,
            'auto_limit': True,
            'allowed_operations': ['SELECT']
        }
        
        if user.role == UserRole.OPERATOR:
            restrictions['max_execution_time'] = 60
            restrictions['max_rows'] = 5000
        
        elif user.role == UserRole.APPROVER:
            restrictions['max_execution_time'] = 120
            restrictions['max_rows'] = 10000
            restrictions['allowed_operations'] = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        
        elif user.role == UserRole.ADMIN:
            restrictions['max_execution_time'] = 300
            restrictions['max_rows'] = 50000
            restrictions['allowed_operations'] = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        
        return restrictions