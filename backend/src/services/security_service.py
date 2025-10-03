"""
Security Service for SQL-Guard application
Manages security policies and enforcement
"""
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog

from ..models.user import User, UserRole
from ..models.security_policy import SecurityPolicy, PolicyType, PolicyTarget, PolicyPriority
from ..models.security_policy import SecurityPolicyEvaluation, SecurityPolicyEvaluationResult
from ..models.audit_log import AuditLog, AuditAction, AuditSeverity
from ..security.rbac import RBACService

logger = structlog.get_logger()


class SecurityService:
    """Security policy management and enforcement service"""

    def __init__(self):
        self.rbac_service = RBACService()

    async def create_policy(self, policy_data: Dict[str, Any], user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Create new security policy
        
        Args:
            policy_data: Policy creation data
            user_id: User ID creating the policy
            user_role: User role
            
        Returns:
            Created policy
        """
        try:
            # Check permissions
            if not self.rbac_service.can_configure_policies(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to create security policies")
            
            # Validate policy data
            await self._validate_policy_data(policy_data)
            
            # Create policy
            policy = SecurityPolicy(
                id=str(uuid.uuid4()),
                name=policy_data["name"],
                description=policy_data.get("description"),
                policy_type=PolicyType(policy_data["policy_type"]),
                value=policy_data["value"],
                applies_to=PolicyTarget(policy_data.get("applies_to", PolicyTarget.ALL_USERS)),
                target=policy_data.get("target"),
                priority=PolicyPriority(policy_data.get("priority", PolicyPriority.MEDIUM)),
                is_active=policy_data.get("is_active", True),
                is_enforced=policy_data.get("is_enforced", True),
                created_by=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save policy
            await self._save_policy(policy)
            
            # Log policy creation
            await self._log_security_action(user_id, policy.id, AuditAction.CONFIGURATION_CHANGED, {
                "policy_name": policy.name,
                "policy_type": policy.policy_type.value,
                "applies_to": policy.applies_to.value
            })
            
            logger.info("Security policy created", 
                       policy_id=policy.id, 
                       policy_name=policy.name, 
                       user_id=user_id)
            
            return self._policy_to_dict(policy)
            
        except Exception as e:
            logger.error("Security policy creation failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def update_policy(self, policy_id: str, update_data: Dict[str, Any], 
                          user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Update existing security policy
        
        Args:
            policy_id: Policy ID
            update_data: Update data
            user_id: User ID updating the policy
            user_role: User role
            
        Returns:
            Updated policy
        """
        try:
            # Check permissions
            if not self.rbac_service.can_configure_policies(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to update security policies")
            
            # Get existing policy
            policy = await self._get_policy(policy_id)
            if not policy:
                raise ValueError(f"Policy not found: {policy_id}")
            
            # Validate update data
            if "policy_type" in update_data or "value" in update_data:
                await self._validate_policy_data(update_data)
            
            # Update policy
            updated_policy = SecurityPolicy(
                id=policy_id,
                name=update_data.get("name", policy["name"]),
                description=update_data.get("description", policy["description"]),
                policy_type=PolicyType(update_data.get("policy_type", policy["policy_type"])),
                value=update_data.get("value", policy["value"]),
                applies_to=PolicyTarget(update_data.get("applies_to", policy["applies_to"])),
                target=update_data.get("target", policy["target"]),
                priority=PolicyPriority(update_data.get("priority", policy["priority"])),
                is_active=update_data.get("is_active", policy["is_active"]),
                is_enforced=update_data.get("is_enforced", policy["is_enforced"]),
                created_by=policy["created_by"],
                created_at=policy["created_at"],
                updated_at=datetime.utcnow()
            )
            
            # Save updated policy
            await self._save_policy(updated_policy)
            
            # Log policy update
            await self._log_security_action(user_id, policy_id, AuditAction.CONFIGURATION_CHANGED, {
                "policy_name": updated_policy.name,
                "changes": list(update_data.keys())
            })
            
            logger.info("Security policy updated", 
                       policy_id=policy_id, 
                       user_id=user_id)
            
            return self._policy_to_dict(updated_policy)
            
        except Exception as e:
            logger.error("Security policy update failed", 
                        policy_id=policy_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def delete_policy(self, policy_id: str, user_id: str, user_role: UserRole) -> bool:
        """
        Delete security policy
        
        Args:
            policy_id: Policy ID
            user_id: User ID deleting the policy
            user_role: User role
            
        Returns:
            True if deletion successful
        """
        try:
            # Check permissions
            if not self.rbac_service.can_configure_policies(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to delete security policies")
            
            # Get policy
            policy = await self._get_policy(policy_id)
            if not policy:
                raise ValueError(f"Policy not found: {policy_id}")
            
            # Delete policy
            await self._delete_policy(policy_id)
            
            # Log policy deletion
            await self._log_security_action(user_id, policy_id, AuditAction.CONFIGURATION_CHANGED, {
                "policy_name": policy["name"],
                "action": "deleted"
            })
            
            logger.info("Security policy deleted", 
                       policy_id=policy_id, 
                       user_id=user_id)
            
            return True
            
        except Exception as e:
            logger.error("Security policy deletion failed", 
                        policy_id=policy_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def get_policy(self, policy_id: str, user_id: str, user_role: UserRole) -> Optional[Dict[str, Any]]:
        """
        Get security policy by ID
        
        Args:
            policy_id: Policy ID
            user_id: User ID requesting the policy
            user_role: User role
            
        Returns:
            Policy data
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_system_statistics(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to view security policies")
            
            policy = await self._get_policy(policy_id)
            return policy
            
        except Exception as e:
            logger.error("Security policy retrieval failed", 
                        policy_id=policy_id, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def list_policies(self, user_id: str, user_role: UserRole, 
                          policy_type_filter: Optional[str] = None,
                          target_filter: Optional[str] = None,
                          limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        List security policies
        
        Args:
            user_id: User ID
            user_role: User role
            policy_type_filter: Optional policy type filter
            target_filter: Optional target filter
            limit: Number of policies per page
            offset: Number of policies to skip
            
        Returns:
            List of policies with pagination info
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_system_statistics(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to view security policies")
            
            # Get policies
            policies = await self._get_policies_with_filters(
                policy_type_filter, target_filter, limit, offset
            )
            
            # Get total count
            total_count = await self._get_policy_count_with_filters(
                policy_type_filter, target_filter
            )
            
            return {
                "policies": policies,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error("Security policy listing failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def evaluate_policy(self, evaluation_request: SecurityPolicyEvaluation, 
                            user_id: str, user_role: UserRole) -> SecurityPolicyEvaluationResult:
        """
        Evaluate security policies against a query
        
        Args:
            evaluation_request: Policy evaluation request
            user_id: User ID requesting evaluation
            user_role: User role
            
        Returns:
            Policy evaluation result
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_system_statistics(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to evaluate security policies")
            
            # Get applicable policies
            applicable_policies = await self._get_applicable_policies(
                evaluation_request.user_role, 
                evaluation_request.database_id
            )
            
            # Evaluate policies
            violations = []
            warnings = []
            applied_policies = []
            modifications = {}
            risk_score = 0.0
            
            for policy in applicable_policies:
                if not policy["is_active"] or not policy["is_enforced"]:
                    continue
                
                applied_policies.append(policy["name"])
                
                # Evaluate specific policy type
                policy_result = await self._evaluate_specific_policy(
                    policy, evaluation_request
                )
                
                if policy_result["violation"]:
                    violations.append(policy_result["violation"])
                    risk_score += policy_result["risk_impact"]
                
                if policy_result["warning"]:
                    warnings.append(policy_result["warning"])
                
                if policy_result["modification"]:
                    modifications.update(policy_result["modification"])
            
            # Determine if query is allowed
            allowed = len(violations) == 0
            
            # Log policy evaluation
            await self._log_security_action(user_id, str(uuid.uuid4()), AuditAction.SECURITY_POLICY_VIOLATION, {
                "user_role": evaluation_request.user_role,
                "database_id": evaluation_request.database_id,
                "violations": violations,
                "risk_score": risk_score
            })
            
            return SecurityPolicyEvaluationResult(
                allowed=allowed,
                applied_policies=applied_policies,
                violations=violations,
                warnings=warnings,
                modifications=modifications,
                risk_score=min(risk_score, 1.0)
            )
            
        except Exception as e:
            logger.error("Security policy evaluation failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def get_policy_stats(self, user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Get security policy statistics
        
        Args:
            user_id: User ID requesting stats
            user_role: User role
            
        Returns:
            Policy statistics
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_system_statistics(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to view security policy statistics")
            
            # Get statistics (simulated)
            stats = {
                "total_policies": 15,
                "active_policies": 12,
                "enforced_policies": 10,
                "policies_by_type": {
                    "STATEMENT_TIMEOUT": 3,
                    "MAX_ROWS": 3,
                    "AUTO_LIMIT": 2,
                    "BLOCK_DDL": 2,
                    "BLOCK_DML": 2,
                    "PII_MASKING": 1,
                    "REQUIRE_WHERE_CLAUSE": 1,
                    "IP_WHITELIST": 1
                },
                "policies_by_target": {
                    "ALL_USERS": 8,
                    "ROLE": 5,
                    "USER": 2
                },
                "recent_violations": 5
            }
            
            return stats
            
        except Exception as e:
            logger.error("Security policy statistics retrieval failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def _validate_policy_data(self, policy_data: Dict[str, Any]) -> None:
        """Validate policy data structure"""
        required_fields = ["name", "policy_type", "value"]
        for field in required_fields:
            if field not in policy_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate policy type
        try:
            PolicyType(policy_data["policy_type"])
        except ValueError:
            raise ValueError(f"Invalid policy type: {policy_data['policy_type']}")
        
        # Validate applies_to
        if "applies_to" in policy_data:
            try:
                PolicyTarget(policy_data["applies_to"])
            except ValueError:
                raise ValueError(f"Invalid applies_to: {policy_data['applies_to']}")
        
        # Validate priority
        if "priority" in policy_data:
            try:
                PolicyPriority(policy_data["priority"])
            except ValueError:
                raise ValueError(f"Invalid priority: {policy_data['priority']}")

    async def _evaluate_specific_policy(self, policy: Dict[str, Any], 
                                      evaluation_request: SecurityPolicyEvaluation) -> Dict[str, Any]:
        """Evaluate specific policy against query"""
        policy_type = PolicyType(policy["policy_type"])
        policy_value = policy["value"]
        
        result = {
            "violation": None,
            "warning": None,
            "modification": None,
            "risk_impact": 0.0
        }
        
        if policy_type == PolicyType.STATEMENT_TIMEOUT:
            # Check if query timeout exceeds policy limit
            timeout_limit = policy_value.get("timeout_seconds", 30)
            # This would typically check the actual query timeout
            result["warning"] = f"Query timeout should not exceed {timeout_limit} seconds"
            result["risk_impact"] = 0.1
        
        elif policy_type == PolicyType.MAX_ROWS:
            # Check if query returns too many rows
            max_rows = policy_value.get("max_rows", 1000)
            # This would typically check the actual query result count
            result["warning"] = f"Query should not return more than {max_rows} rows"
            result["risk_impact"] = 0.2
        
        elif policy_type == PolicyType.BLOCK_DDL:
            # Check for DDL statements
            blocked_statements = policy_value.get("blocked_statements", [])
            sql_upper = evaluation_request.sql_query.upper()
            
            for statement in blocked_statements:
                if statement.upper() in sql_upper:
                    result["violation"] = f"DDL statement '{statement}' is blocked by policy"
                    result["risk_impact"] = 0.8
                    break
        
        elif policy_type == PolicyType.BLOCK_DML:
            # Check for DML statements
            blocked_statements = policy_value.get("blocked_statements", [])
            sql_upper = evaluation_request.sql_query.upper()
            
            for statement in blocked_statements:
                if statement.upper() in sql_upper:
                    result["violation"] = f"DML statement '{statement}' is blocked by policy"
                    result["risk_impact"] = 0.6
                    break
        
        elif policy_type == PolicyType.REQUIRE_WHERE_CLAUSE:
            # Check for UPDATE/DELETE without WHERE clause
            sql_upper = evaluation_request.sql_query.upper()
            required_for = policy_value.get("required_for", ["UPDATE", "DELETE"])
            
            for statement in required_for:
                if statement.upper() in sql_upper and "WHERE" not in sql_upper:
                    result["violation"] = f"{statement} statement requires WHERE clause"
                    result["risk_impact"] = 0.9
                    break
        
        return result

    async def _get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Get policy by ID (simulated)"""
        # In real implementation, this would query the database
        if policy_id == "policy-123":
            return {
                "id": policy_id,
                "name": "viewer_timeout",
                "description": "Statement timeout for VIEWER role",
                "policy_type": PolicyType.STATEMENT_TIMEOUT.value,
                "value": {"timeout_seconds": 30},
                "applies_to": PolicyTarget.ROLE.value,
                "target": "VIEWER",
                "priority": PolicyPriority.HIGH.value,
                "is_active": True,
                "is_enforced": True,
                "created_by": "admin-123",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        return None

    async def _get_policies_with_filters(self, policy_type_filter: Optional[str], 
                                       target_filter: Optional[str], 
                                       limit: int, offset: int) -> List[Dict[str, Any]]:
        """Get policies with filters (simulated)"""
        # In real implementation, this would query the database with proper filtering
        policies = [
            {
                "id": "policy-123",
                "name": "viewer_timeout",
                "policy_type": PolicyType.STATEMENT_TIMEOUT.value,
                "applies_to": PolicyTarget.ROLE.value,
                "target": "VIEWER",
                "is_active": True,
                "is_enforced": True
            }
        ]
        
        return policies[offset:offset + limit]

    async def _get_policy_count_with_filters(self, policy_type_filter: Optional[str], 
                                           target_filter: Optional[str]) -> int:
        """Get policy count with filters (simulated)"""
        # In real implementation, this would count policies in database
        return 1

    async def _get_applicable_policies(self, user_role: str, database_id: str) -> List[Dict[str, Any]]:
        """Get policies applicable to user role and database (simulated)"""
        # In real implementation, this would query applicable policies
        return [
            {
                "id": "policy-123",
                "name": "viewer_timeout",
                "policy_type": PolicyType.STATEMENT_TIMEOUT.value,
                "value": {"timeout_seconds": 30},
                "applies_to": PolicyTarget.ROLE.value,
                "target": "VIEWER",
                "is_active": True,
                "is_enforced": True
            }
        ]

    async def _save_policy(self, policy: SecurityPolicy) -> None:
        """Save policy to database (simulated)"""
        # In real implementation, this would save to database
        logger.info("Security policy saved", policy_id=policy.id, name=policy.name)

    async def _delete_policy(self, policy_id: str) -> None:
        """Delete policy from database (simulated)"""
        # In real implementation, this would delete from database
        logger.info("Security policy deleted", policy_id=policy_id)

    def _policy_to_dict(self, policy: SecurityPolicy) -> Dict[str, Any]:
        """Convert policy model to dictionary"""
        return {
            "id": policy.id,
            "name": policy.name,
            "description": policy.description,
            "policy_type": policy.policy_type.value,
            "value": policy.value,
            "applies_to": policy.applies_to.value,
            "target": policy.target,
            "priority": policy.priority.value,
            "is_active": policy.is_active,
            "is_enforced": policy.is_enforced,
            "created_by": policy.created_by,
            "created_at": policy.created_at,
            "updated_at": policy.updated_at
        }

    async def _log_security_action(self, user_id: str, resource_id: str, 
                                 action: AuditAction, details: Dict[str, Any]) -> None:
        """Log security action"""
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type="POLICY",
                resource_id=resource_id,
                details=details,
                timestamp=datetime.utcnow(),
                severity=AuditSeverity.INFO
            )
            
            logger.info("Security action logged", 
                       user_id=user_id, 
                       resource_id=resource_id, 
                       action=action.value)
            
        except Exception as e:
            logger.error("Failed to log security action", 
                        user_id=user_id, 
                        resource_id=resource_id, 
                        error=str(e))