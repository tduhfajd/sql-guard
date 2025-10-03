"""
Approval Service for SQL-Guard application
Manages template approval workflow and reviewer assignments
"""
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog

from ..models.user import User, UserRole
from ..models.sql_template import SQLTemplate, TemplateStatus
from ..models.approval_request import ApprovalRequest, ApprovalStatus, ApprovalAction
from ..models.audit_log import AuditLog, AuditAction, AuditSeverity
from ..security.rbac import RBACService

logger = structlog.get_logger()


class ApprovalService:
    """Approval workflow service"""

    def __init__(self):
        self.rbac_service = RBACService()

    async def submit_for_approval(self, template_id: str, assigned_to: str, 
                                user_id: str, user_role: UserRole, 
                                comments: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit template for approval
        
        Args:
            template_id: Template ID
            assigned_to: User ID assigned to review
            user_id: User ID submitting for approval
            user_role: User role
            comments: Optional comments
            
        Returns:
            Approval request
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_approvals(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to submit for approval")
            
            # Get template
            template = await self._get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # Check if template can be submitted for approval
            if template["status"] != TemplateStatus.DRAFT:
                raise ValueError("Only draft templates can be submitted for approval")
            
            # Create approval request
            approval_request = ApprovalRequest(
                id=str(uuid.uuid4()),
                template_id=template_id,
                requested_by=user_id,
                assigned_to=assigned_to,
                status=ApprovalStatus.PENDING,
                comments=comments,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save approval request
            await self._save_approval_request(approval_request)
            
            # Update template status
            await self._update_template_status(template_id, TemplateStatus.PENDING_APPROVAL)
            
            # Log submission
            await self._log_approval_action(user_id, approval_request.id, AuditAction.APPROVAL_REQUESTED, {
                "template_id": template_id,
                "template_name": template["name"],
                "assigned_to": assigned_to,
                "comments": comments
            })
            
            logger.info("Template submitted for approval", 
                       template_id=template_id, 
                       approval_id=approval_request.id, 
                       user_id=user_id)
            
            return self._approval_request_to_dict(approval_request)
            
        except Exception as e:
            logger.error("Approval submission failed", 
                        template_id=template_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def process_approval(self, approval_id: str, action: ApprovalAction, 
                             user_id: str, user_role: UserRole, 
                             comments: Optional[str] = None) -> Dict[str, Any]:
        """
        Process approval request (approve or reject)
        
        Args:
            approval_id: Approval request ID
            action: Approval action (approve or reject)
            user_id: User ID processing the approval
            user_role: User role
            comments: Optional comments
            
        Returns:
            Updated approval request
        """
        try:
            # Check permissions
            if not self.rbac_service.can_approve_template(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to process approvals")
            
            # Get approval request
            approval_request = await self._get_approval_request(approval_id)
            if not approval_request:
                raise ValueError(f"Approval request not found: {approval_id}")
            
            # Check if user is assigned to this approval
            if approval_request["assigned_to"] != user_id:
                raise PermissionError("You are not assigned to this approval request")
            
            # Check if approval is still pending
            if approval_request["status"] != ApprovalStatus.PENDING:
                raise ValueError("Approval request is no longer pending")
            
            # Validate comments for rejection
            if action == ApprovalAction.REJECT and not comments:
                raise ValueError("Comments are required when rejecting a template")
            
            # Update approval request
            updated_approval = ApprovalRequest(
                id=approval_id,
                template_id=approval_request["template_id"],
                requested_by=approval_request["requested_by"],
                assigned_to=approval_request["assigned_to"],
                status=ApprovalStatus.APPROVED if action == ApprovalAction.APPROVE else ApprovalStatus.REJECTED,
                comments=comments or approval_request["comments"],
                created_at=approval_request["created_at"],
                updated_at=datetime.utcnow(),
                resolved_at=datetime.utcnow()
            )
            
            # Save updated approval request
            await self._save_approval_request(updated_approval)
            
            # Update template status
            new_template_status = TemplateStatus.APPROVED if action == ApprovalAction.APPROVE else TemplateStatus.REJECTED
            await self._update_template_status(approval_request["template_id"], new_template_status)
            
            # Log approval action
            audit_action = AuditAction.TEMPLATE_APPROVED if action == ApprovalAction.APPROVE else AuditAction.TEMPLATE_REJECTED
            await self._log_approval_action(user_id, approval_id, audit_action, {
                "template_id": approval_request["template_id"],
                "action": action.value,
                "comments": comments
            })
            
            logger.info("Approval processed", 
                       approval_id=approval_id, 
                       action=action.value, 
                       user_id=user_id)
            
            return self._approval_request_to_dict(updated_approval)
            
        except Exception as e:
            logger.error("Approval processing failed", 
                        approval_id=approval_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def get_approval_request(self, approval_id: str, user_id: str, user_role: UserRole) -> Optional[Dict[str, Any]]:
        """
        Get approval request by ID
        
        Args:
            approval_id: Approval request ID
            user_id: User ID requesting the approval
            user_role: User role
            
        Returns:
            Approval request data
        """
        try:
            approval_request = await self._get_approval_request(approval_id)
            if not approval_request:
                return None
            
            # Check if user can view this approval
            if not self._can_view_approval(approval_request, user_id, user_role):
                raise PermissionError("Insufficient permissions to view this approval request")
            
            return approval_request
            
        except Exception as e:
            logger.error("Approval retrieval failed", 
                        approval_id=approval_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def list_approvals(self, user_id: str, user_role: UserRole, 
                           status_filter: Optional[str] = None,
                           assigned_to_me: bool = False,
                           limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        List approval requests
        
        Args:
            user_id: User ID
            user_role: User role
            status_filter: Optional status filter
            assigned_to_me: Filter for approvals assigned to current user
            limit: Number of approvals per page
            offset: Number of approvals to skip
            
        Returns:
            List of approval requests with pagination info
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_approvals(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to view approval queue")
            
            # Get approvals based on filters
            approvals = await self._get_approvals_for_user(
                user_id, user_role, status_filter, assigned_to_me, limit, offset
            )
            
            # Get total count
            total_count = await self._get_approval_count_for_user(
                user_id, user_role, status_filter, assigned_to_me
            )
            
            return {
                "approvals": approvals,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error("Approval listing failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def preview_template(self, approval_id: str, parameters: Dict[str, Any], 
                            user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Preview template execution for approval
        
        Args:
            approval_id: Approval request ID
            parameters: Template parameters
            user_id: User ID requesting preview
            user_role: User role
            
        Returns:
            Template preview with rendered SQL
        """
        try:
            # Get approval request
            approval_request = await self._get_approval_request(approval_id)
            if not approval_request:
                raise ValueError(f"Approval request not found: {approval_id}")
            
            # Check if user can view this approval
            if not self._can_view_approval(approval_request, user_id, user_role):
                raise PermissionError("Insufficient permissions to preview this template")
            
            # Get template
            template = await self._get_template(approval_request["template_id"])
            if not template:
                raise ValueError("Template not found")
            
            # Render template with parameters
            rendered_sql = await self._render_template(template, parameters)
            
            # Get security analysis
            security_analysis = await self._analyze_template_security(template, parameters)
            
            return {
                "rendered_sql": rendered_sql,
                "parameter_values": parameters,
                "security_analysis": security_analysis,
                "template_info": {
                    "name": template["name"],
                    "description": template["description"],
                    "version": template["version"]
                }
            }
            
        except Exception as e:
            logger.error("Template preview failed", 
                        approval_id=approval_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def bulk_process_approvals(self, approval_ids: List[str], action: ApprovalAction,
                                   user_id: str, user_role: UserRole, 
                                   comments: Optional[str] = None) -> Dict[str, Any]:
        """
        Process multiple approval requests
        
        Args:
            approval_ids: List of approval request IDs
            action: Approval action
            user_id: User ID processing approvals
            user_role: User role
            comments: Optional comments
            
        Returns:
            Bulk processing result
        """
        try:
            # Check permissions
            if not self.rbac_service.can_approve_template(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to process approvals")
            
            results = []
            approved_count = 0
            rejected_count = 0
            failed_count = 0
            
            for approval_id in approval_ids:
                try:
                    result = await self.process_approval(approval_id, action, user_id, user_role, comments)
                    results.append({"approval_id": approval_id, "success": True, "result": result})
                    
                    if action == ApprovalAction.APPROVE:
                        approved_count += 1
                    else:
                        rejected_count += 1
                        
                except Exception as e:
                    results.append({
                        "approval_id": approval_id, 
                        "success": False, 
                        "error": str(e)
                    })
                    failed_count += 1
            
            logger.info("Bulk approval processing completed", 
                       user_id=user_id, 
                       action=action.value,
                       total=len(approval_ids),
                       approved=approved_count,
                       rejected=rejected_count,
                       failed=failed_count)
            
            return {
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "failed_count": failed_count,
                "results": results
            }
            
        except Exception as e:
            logger.error("Bulk approval processing failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def get_approval_stats(self, user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Get approval statistics
        
        Args:
            user_id: User ID
            user_role: User role
            
        Returns:
            Approval statistics
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_approvals(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to view approval statistics")
            
            # Get statistics (simulated)
            stats = {
                "pending_count": 5,
                "approved_count": 25,
                "rejected_count": 3,
                "average_approval_time": "2.5 hours",
                "approval_rate": 89.3
            }
            
            return stats
            
        except Exception as e:
            logger.error("Approval statistics retrieval failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def _can_view_approval(self, approval_request: Dict[str, Any], 
                              user_id: str, user_role: UserRole) -> bool:
        """Check if user can view approval request"""
        # Users can view their own approval requests
        if approval_request["requested_by"] == user_id:
            return True
        
        # Users can view approvals assigned to them
        if approval_request["assigned_to"] == user_id:
            return True
        
        # Admins and approvers can view all approvals
        if user_role in [UserRole.ADMIN, UserRole.APPROVER]:
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
                "status": TemplateStatus.DRAFT,
                "created_by": "user-123"
            }
        return None

    async def _get_approval_request(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get approval request by ID (simulated)"""
        # In real implementation, this would query the database
        if approval_id == "approval-123":
            return {
                "id": approval_id,
                "template_id": "template-123",
                "requested_by": "user-123",
                "assigned_to": "approver-456",
                "status": ApprovalStatus.PENDING,
                "comments": "Please review this template",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "resolved_at": None
            }
        return None

    async def _get_approvals_for_user(self, user_id: str, user_role: UserRole, 
                                    status_filter: Optional[str], 
                                    assigned_to_me: bool, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Get approvals for user (simulated)"""
        # In real implementation, this would query the database with proper filtering
        approvals = [
            {
                "id": "approval-123",
                "template_id": "template-123",
                "template_name": "user_analysis",
                "requested_by": "user-123",
                "assigned_to": "approver-456",
                "status": ApprovalStatus.PENDING,
                "created_at": datetime.utcnow()
            }
        ]
        
        return approvals[offset:offset + limit]

    async def _get_approval_count_for_user(self, user_id: str, user_role: UserRole, 
                                         status_filter: Optional[str], 
                                         assigned_to_me: bool) -> int:
        """Get approval count for user (simulated)"""
        # In real implementation, this would count approvals in database
        return 1

    async def _save_approval_request(self, approval_request: ApprovalRequest) -> None:
        """Save approval request to database (simulated)"""
        # In real implementation, this would save to database
        logger.info("Approval request saved", approval_id=approval_request.id)

    async def _update_template_status(self, template_id: str, status: TemplateStatus) -> None:
        """Update template status (simulated)"""
        # In real implementation, this would update template in database
        logger.info("Template status updated", template_id=template_id, status=status.value)

    async def _render_template(self, template: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Render template with parameters"""
        sql = template["sql_content"]
        
        # Simple parameter substitution
        for param_name, param_value in parameters.items():
            placeholder = f":{param_name}"
            sql = sql.replace(placeholder, str(param_value))
        
        return sql

    async def _analyze_template_security(self, template: Dict[str, Any], 
                                      parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze template security (simulated)"""
        return {
            "has_ddl": False,
            "has_dml": False,
            "has_where_clause": True,
            "parameter_count": len(parameters),
            "estimated_cost": 1.5,
            "security_score": 0.8
        }

    def _approval_request_to_dict(self, approval_request: ApprovalRequest) -> Dict[str, Any]:
        """Convert approval request model to dictionary"""
        return {
            "id": approval_request.id,
            "template_id": approval_request.template_id,
            "requested_by": approval_request.requested_by,
            "assigned_to": approval_request.assigned_to,
            "status": approval_request.status.value,
            "comments": approval_request.comments,
            "created_at": approval_request.created_at,
            "updated_at": approval_request.updated_at,
            "resolved_at": approval_request.resolved_at
        }

    async def _log_approval_action(self, user_id: str, approval_id: str, 
                                action: AuditAction, details: Dict[str, Any]) -> None:
        """Log approval action"""
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type="APPROVAL",
                resource_id=approval_id,
                details=details,
                timestamp=datetime.utcnow(),
                severity=AuditSeverity.INFO
            )
            
            logger.info("Approval action logged", 
                       user_id=user_id, 
                       approval_id=approval_id, 
                       action=action.value)
            
        except Exception as e:
            logger.error("Failed to log approval action", 
                        user_id=user_id, 
                        approval_id=approval_id, 
                        error=str(e))