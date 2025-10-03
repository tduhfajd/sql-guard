"""
Template Service for SQL-Guard application
Manages SQL templates with versioning and approval workflow
"""
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog

from ..models.user import User, UserRole
from ..models.sql_template import SQLTemplate, TemplateStatus, ParameterDefinition, ParameterType
from ..models.approval_request import ApprovalRequest, ApprovalStatus
from ..models.audit_log import AuditLog, AuditAction, AuditSeverity
from ..security.sql_validator import SQLValidator
from ..security.rbac import RBACService

logger = structlog.get_logger()


class TemplateService:
    """Template management service"""

    def __init__(self):
        self.sql_validator = SQLValidator()
        self.rbac_service = RBACService()

    async def create_template(self, template_data: Dict[str, Any], user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Create new SQL template
        
        Args:
            template_data: Template creation data
            user_id: User ID creating the template
            user_role: User role
            
        Returns:
            Created template
        """
        try:
            # Check permissions
            if not self.rbac_service.can_create_template(User(id=user_id, role=user_role, is_active=True)):
                raise PermissionError("Insufficient permissions to create templates")
            
            # Validate template data
            await self._validate_template_data(template_data)
            
            # Create template
            template = SQLTemplate(
                id=str(uuid.uuid4()),
                name=template_data["name"],
                description=template_data.get("description"),
                sql_content=template_data["sql_content"],
                parameters=template_data.get("parameters", {}),
                version=1,
                status=TemplateStatus.DRAFT,
                require_approval=template_data.get("require_approval", True),
                created_by=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save template
            await self._save_template(template)
            
            # Log creation
            await self._log_template_action(user_id, template.id, AuditAction.TEMPLATE_CREATED, {
                "template_name": template.name,
                "version": template.version
            })
            
            logger.info("Template created", 
                       template_id=template.id, 
                       template_name=template.name, 
                       user_id=user_id)
            
            return self._template_to_dict(template)
            
        except Exception as e:
            logger.error("Template creation failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def update_template(self, template_id: str, update_data: Dict[str, Any], 
                           user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Update existing template
        
        Args:
            template_id: Template ID
            update_data: Update data
            user_id: User ID updating the template
            user_role: User role
            
        Returns:
            Updated template
        """
        try:
            # Get existing template
            template = await self._get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # Check permissions
            if not self.rbac_service.can_update_template(
                User(id=user_id, role=user_role, is_active=True), 
                template["created_by"]
            ):
                raise PermissionError("Insufficient permissions to update this template")
            
            # Validate update data
            if "sql_content" in update_data:
                await self._validate_template_data(update_data)
            
            # Create new version
            new_version = template["version"] + 1
            updated_template = SQLTemplate(
                id=template_id,
                name=update_data.get("name", template["name"]),
                description=update_data.get("description", template["description"]),
                sql_content=update_data.get("sql_content", template["sql_content"]),
                parameters=update_data.get("parameters", template["parameters"]),
                version=new_version,
                status=TemplateStatus.DRAFT,
                require_approval=update_data.get("require_approval", template["require_approval"]),
                created_by=template["created_by"],
                created_at=template["created_at"],
                updated_at=datetime.utcnow()
            )
            
            # Save updated template
            await self._save_template(updated_template)
            
            # Log update
            await self._log_template_action(user_id, template_id, AuditAction.TEMPLATE_UPDATED, {
                "template_name": updated_template.name,
                "version": new_version,
                "changes": list(update_data.keys())
            })
            
            logger.info("Template updated", 
                       template_id=template_id, 
                       version=new_version, 
                       user_id=user_id)
            
            return self._template_to_dict(updated_template)
            
        except Exception as e:
            logger.error("Template update failed", 
                        template_id=template_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def delete_template(self, template_id: str, user_id: str, user_role: UserRole) -> bool:
        """
        Delete template
        
        Args:
            template_id: Template ID
            user_id: User ID deleting the template
            user_role: User role
            
        Returns:
            True if deletion successful
        """
        try:
            # Get template
            template = await self._get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # Check permissions
            if not self.rbac_service.can_delete_template(
                User(id=user_id, role=user_role, is_active=True), 
                template["created_by"]
            ):
                raise PermissionError("Insufficient permissions to delete this template")
            
            # Delete template
            await self._delete_template(template_id)
            
            # Log deletion
            await self._log_template_action(user_id, template_id, AuditAction.TEMPLATE_DELETED, {
                "template_name": template["name"],
                "version": template["version"]
            })
            
            logger.info("Template deleted", 
                       template_id=template_id, 
                       user_id=user_id)
            
            return True
            
        except Exception as e:
            logger.error("Template deletion failed", 
                        template_id=template_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def get_template(self, template_id: str, user_id: str, user_role: UserRole) -> Optional[Dict[str, Any]]:
        """
        Get template by ID
        
        Args:
            template_id: Template ID
            user_id: User ID requesting the template
            user_role: User role
            
        Returns:
            Template data
        """
        try:
            template = await self._get_template(template_id)
            if not template:
                return None
            
            # Check if user can view this template
            if not self._can_view_template(template, user_id, user_role):
                raise PermissionError("Insufficient permissions to view this template")
            
            return template
            
        except Exception as e:
            logger.error("Template retrieval failed", 
                        template_id=template_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def list_templates(self, user_id: str, user_role: UserRole, 
                           status_filter: Optional[str] = None,
                           limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        List templates accessible to user
        
        Args:
            user_id: User ID
            user_role: User role
            status_filter: Optional status filter
            limit: Number of templates per page
            offset: Number of templates to skip
            
        Returns:
            List of templates with pagination info
        """
        try:
            # Get templates based on user role
            templates = await self._get_templates_for_user(user_id, user_role, status_filter, limit, offset)
            
            # Get total count
            total_count = await self._get_template_count_for_user(user_id, user_role, status_filter)
            
            return {
                "templates": templates,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error("Template listing failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def execute_template(self, template_id: str, database_id: str, 
                             parameters: Dict[str, Any], user_id: str, 
                             user_role: UserRole) -> Dict[str, Any]:
        """
        Execute approved template
        
        Args:
            template_id: Template ID
            database_id: Target database ID
            parameters: Template parameters
            user_id: User ID executing the template
            user_role: User role
            
        Returns:
            Execution result
        """
        try:
            # Get template
            template = await self._get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # Check if template is approved
            if template["status"] != TemplateStatus.APPROVED:
                raise PermissionError("Template not approved for execution")
            
            # Check execution permissions
            if not self.rbac_service.can_execute_template(
                User(id=user_id, role=user_role, is_active=True), 
                TemplateStatus.APPROVED
            ):
                raise PermissionError("Insufficient permissions to execute templates")
            
            # Validate parameters
            await self._validate_template_parameters(template, parameters)
            
            # Render template
            rendered_sql = await self._render_template(template, parameters)
            
            # Execute SQL (this would call the SQL execution service)
            execution_result = await self._execute_rendered_sql(rendered_sql, database_id, user_id, user_role)
            
            # Log execution
            await self._log_template_action(user_id, template_id, AuditAction.TEMPLATE_EXECUTED, {
                "template_name": template["name"],
                "database_id": database_id,
                "parameters": parameters,
                "row_count": execution_result.get("row_count", 0)
            })
            
            return execution_result
            
        except Exception as e:
            logger.error("Template execution failed", 
                        template_id=template_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def validate_template(self, template_data: Dict[str, Any], user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Validate template without saving
        
        Args:
            template_data: Template data to validate
            user_id: User ID
            user_role: User role
            
        Returns:
            Validation result
        """
        try:
            # Validate template data
            await self._validate_template_data(template_data)
            
            # Validate SQL content
            sql_validation = self.sql_validator.validate_sql(
                template_data["sql_content"], 
                user_role
            )
            
            # Validate parameters
            parameter_validation = await self._validate_template_parameters_structure(template_data.get("parameters", {}))
            
            return {
                "is_valid": sql_validation.is_valid and parameter_validation["is_valid"],
                "sql_validation": {
                    "is_valid": sql_validation.is_valid,
                    "errors": sql_validation.errors,
                    "warnings": sql_validation.warnings,
                    "estimated_cost": sql_validation.estimated_cost
                },
                "parameter_validation": parameter_validation,
                "security_checks": sql_validation.security_checks
            }
            
        except Exception as e:
            logger.error("Template validation failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def _validate_template_data(self, template_data: Dict[str, Any]) -> None:
        """Validate template data structure"""
        required_fields = ["name", "sql_content"]
        for field in required_fields:
            if field not in template_data:
                raise ValueError(f"Missing required field: {field}")
        
        if not template_data["name"].strip():
            raise ValueError("Template name cannot be empty")
        
        if not template_data["sql_content"].strip():
            raise ValueError("SQL content cannot be empty")

    async def _validate_template_parameters(self, template: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        """Validate template parameters"""
        template_params = template.get("parameters", {})
        
        # Check required parameters
        for param_name, param_def in template_params.items():
            if param_def.get("required", True) and param_name not in parameters:
                raise ValueError(f"Missing required parameter: {param_name}")
        
        # Validate parameter types
        for param_name, param_value in parameters.items():
            if param_name in template_params:
                param_def = template_params[param_name]
                await self._validate_parameter_type(param_name, param_value, param_def)

    async def _validate_template_parameters_structure(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameter structure"""
        errors = []
        warnings = []
        
        for param_name, param_def in parameters.items():
            if not isinstance(param_def, dict):
                errors.append(f"Parameter '{param_name}' definition must be a dictionary")
                continue
            
            # Check required fields
            if "type" not in param_def:
                errors.append(f"Parameter '{param_name}' missing type definition")
            
            # Validate type
            if "type" in param_def:
                try:
                    ParameterType(param_def["type"])
                except ValueError:
                    errors.append(f"Parameter '{param_name}' has invalid type: {param_def['type']}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def _validate_parameter_type(self, param_name: str, param_value: Any, param_def: Dict[str, Any]) -> None:
        """Validate individual parameter type"""
        param_type = param_def.get("type")
        
        if param_type == ParameterType.STRING and not isinstance(param_value, str):
            raise ValueError(f"Parameter '{param_name}' must be a string")
        elif param_type == ParameterType.INTEGER and not isinstance(param_value, int):
            raise ValueError(f"Parameter '{param_name}' must be an integer")
        elif param_type == ParameterType.FLOAT and not isinstance(param_value, (int, float)):
            raise ValueError(f"Parameter '{param_name}' must be a number")
        elif param_type == ParameterType.BOOLEAN and not isinstance(param_value, bool):
            raise ValueError(f"Parameter '{param_name}' must be a boolean")

    async def _render_template(self, template: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Render template with parameters"""
        sql = template["sql_content"]
        
        # Simple parameter substitution
        for param_name, param_value in parameters.items():
            placeholder = f":{param_name}"
            sql = sql.replace(placeholder, str(param_value))
        
        return sql

    async def _can_view_template(self, template: Dict[str, Any], user_id: str, user_role: UserRole) -> bool:
        """Check if user can view template"""
        # Users can view their own templates
        if template["created_by"] == user_id:
            return True
        
        # Check role-based permissions
        if user_role == UserRole.ADMIN:
            return True
        elif user_role == UserRole.APPROVER:
            return True
        elif user_role == UserRole.OPERATOR and template["status"] == TemplateStatus.APPROVED:
            return True
        elif user_role == UserRole.VIEWER and template["status"] == TemplateStatus.APPROVED:
            return True
        
        return False

    async def _get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID (simulated)"""
        # In real implementation, this would query the database
        if template_id == "template-123":
            return {
                "id": template_id,
                "name": "user_analysis",
                "description": "Analyze user data",
                "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date",
                "parameters": {
                    "start_date": {"type": "date", "required": True},
                    "end_date": {"type": "date", "required": True}
                },
                "version": 1,
                "status": TemplateStatus.APPROVED,
                "require_approval": True,
                "created_by": "user-123",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        return None

    async def _get_templates_for_user(self, user_id: str, user_role: UserRole, 
                                    status_filter: Optional[str], 
                                    limit: int, offset: int) -> List[Dict[str, Any]]:
        """Get templates accessible to user (simulated)"""
        # In real implementation, this would query the database with proper filtering
        templates = []
        
        if user_role == UserRole.ADMIN:
            # Admins can see all templates
            templates = [
                {
                    "id": "template-123",
                    "name": "user_analysis",
                    "status": TemplateStatus.APPROVED,
                    "version": 1,
                    "created_by": "user-123"
                }
            ]
        elif user_role in [UserRole.APPROVER, UserRole.OPERATOR, UserRole.VIEWER]:
            # Others can see approved templates
            templates = [
                {
                    "id": "template-123",
                    "name": "user_analysis",
                    "status": TemplateStatus.APPROVED,
                    "version": 1,
                    "created_by": "user-123"
                }
            ]
        
        return templates[offset:offset + limit]

    async def _get_template_count_for_user(self, user_id: str, user_role: UserRole, 
                                         status_filter: Optional[str]) -> int:
        """Get total template count for user (simulated)"""
        # In real implementation, this would count templates in database
        return 1

    async def _save_template(self, template: SQLTemplate) -> None:
        """Save template to database (simulated)"""
        # In real implementation, this would save to database
        logger.info("Template saved", template_id=template.id, name=template.name)

    async def _delete_template(self, template_id: str) -> None:
        """Delete template from database (simulated)"""
        # In real implementation, this would delete from database
        logger.info("Template deleted", template_id=template_id)

    async def _execute_rendered_sql(self, sql: str, database_id: str, 
                                  user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """Execute rendered SQL (simulated)"""
        # In real implementation, this would call the SQL execution service
        return {
            "results": [{"id": 1, "name": "John Doe"}],
            "columns": ["id", "name"],
            "row_count": 1,
            "execution_time": 0.1
        }

    def _template_to_dict(self, template: SQLTemplate) -> Dict[str, Any]:
        """Convert template model to dictionary"""
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "sql_content": template.sql_content,
            "parameters": template.parameters,
            "version": template.version,
            "status": template.status.value,
            "require_approval": template.require_approval,
            "created_by": template.created_by,
            "created_at": template.created_at,
            "updated_at": template.updated_at
        }

    async def _log_template_action(self, user_id: str, template_id: str, 
                                 action: AuditAction, details: Dict[str, Any]) -> None:
        """Log template action"""
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type="TEMPLATE",
                resource_id=template_id,
                details=details,
                timestamp=datetime.utcnow(),
                severity=AuditSeverity.INFO
            )
            
            logger.info("Template action logged", 
                       user_id=user_id, 
                       template_id=template_id, 
                       action=action.value)
            
        except Exception as e:
            logger.error("Failed to log template action", 
                        user_id=user_id, 
                        template_id=template_id, 
                        error=str(e))