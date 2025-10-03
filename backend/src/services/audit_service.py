"""
Audit Service for SQL-Guard application
Manages immutable audit logging and compliance reporting
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import structlog
import json

from ..models.user import User, UserRole
from ..models.audit_log import AuditLog, AuditAction, AuditSeverity, AuditResourceType
from ..models.audit_log import AuditLogFilter, AuditLogExport, AuditLogStats
from ..security.pii_masker import PIIMasker
from ..security.rbac import RBACService

logger = structlog.get_logger()


class AuditService:
    """Audit logging and compliance service"""

    def __init__(self):
        self.pii_masker = PIIMasker()
        self.rbac_service = RBACService()

    async def log_event(self, user_id: Optional[str], action: AuditAction, 
                       resource_type: AuditResourceType, resource_id: Optional[str],
                       details: Dict[str, Any], ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None) -> str:
        """
        Log audit event
        
        Args:
            user_id: User ID (nullable for system events)
            action: Audit action
            resource_type: Type of resource affected
            resource_id: Resource ID
            details: Action-specific details
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Audit log ID
        """
        try:
            # Create audit log entry
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                severity=AuditSeverity.INFO
            )
            
            # Mask PII in details if needed
            if self.pii_masker.should_mask_pii(action):
                audit_log.details = self.pii_masker.mask_data(details)
            
            # Save audit log (immutable)
            await self._save_audit_log(audit_log)
            
            logger.info("Audit event logged", 
                       audit_id=audit_log.id, 
                       action=action.value, 
                       user_id=user_id)
            
            return audit_log.id
            
        except Exception as e:
            logger.error("Failed to log audit event", 
                        action=action.value, 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def get_audit_logs(self, user_id: str, user_role: UserRole, 
                           filters: Optional[AuditLogFilter] = None,
                           limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get audit logs with filtering
        
        Args:
            user_id: User ID requesting logs
            user_role: User role
            filters: Optional filters
            limit: Number of logs per page
            offset: Number of logs to skip
            
        Returns:
            List of audit logs with pagination info
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_audit_logs(
                User(id=user_id, role=user_role, is_active=True), 
                None
            ):
                raise PermissionError("Insufficient permissions to view audit logs")
            
            # Apply filters
            if filters:
                # Check if user can view logs for specific user
                if filters.user_id and filters.user_id != user_id:
                    if not self.rbac_service.can_view_all_audit_logs(
                        User(id=user_id, role=user_role, is_active=True)
                    ):
                        raise PermissionError("Insufficient permissions to view other users' logs")
            
            # Get audit logs
            logs = await self._get_audit_logs_with_filters(filters, limit, offset)
            
            # Get total count
            total_count = await self._get_audit_log_count_with_filters(filters)
            
            return {
                "logs": logs,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error("Audit log retrieval failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def export_audit_logs(self, export_request: AuditLogExport, 
                              user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Export audit logs
        
        Args:
            export_request: Export configuration
            user_id: User ID requesting export
            user_role: User role
            
        Returns:
            Export result with file information
        """
        try:
            # Check permissions
            if not self.rbac_service.can_export_audit_logs(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to export audit logs")
            
            # Get logs for export
            logs = await self._get_audit_logs_for_export(export_request)
            
            # Generate export file
            export_id = str(uuid.uuid4())
            file_path = await self._generate_export_file(export_id, logs, export_request.format)
            
            # Log export action
            await self.log_event(
                user_id=user_id,
                action=AuditAction.SYSTEM_ERROR,  # Use appropriate action
                resource_type=AuditResourceType.SYSTEM,
                resource_id=export_id,
                details={
                    "export_format": export_request.format,
                    "record_count": len(logs),
                    "file_path": file_path
                }
            )
            
            return {
                "export_id": export_id,
                "file_path": file_path,
                "format": export_request.format,
                "record_count": len(logs),
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error("Audit log export failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def get_audit_stats(self, user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Get audit statistics
        
        Args:
            user_id: User ID requesting stats
            user_role: User role
            
        Returns:
            Audit statistics
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_system_statistics(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to view audit statistics")
            
            # Get statistics (simulated)
            stats = {
                "total_logs": 15420,
                "logs_by_severity": {
                    "INFO": 12000,
                    "WARNING": 2500,
                    "ERROR": 800,
                    "CRITICAL": 120
                },
                "logs_by_action": {
                    "SQL_EXECUTION": 8000,
                    "USER_LOGIN": 2000,
                    "TEMPLATE_CREATED": 500,
                    "TEMPLATE_APPROVED": 300,
                    "SQL_INJECTION_ATTEMPT": 5
                },
                "logs_by_user": {
                    "user-123": 5000,
                    "user-456": 3000,
                    "user-789": 2000
                },
                "recent_activity": 150,  # Last 24 hours
                "security_events": 25
            }
            
            return stats
            
        except Exception as e:
            logger.error("Audit statistics retrieval failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def search_audit_logs(self, query: str, user_id: str, user_role: UserRole,
                              filters: Optional[AuditLogFilter] = None,
                              limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Search audit logs
        
        Args:
            query: Search query
            user_id: User ID requesting search
            user_role: User role
            filters: Optional filters
            limit: Number of results per page
            offset: Number of results to skip
            
        Returns:
            Search results with pagination info
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_audit_logs(
                User(id=user_id, role=user_role, is_active=True), 
                None
            ):
                raise PermissionError("Insufficient permissions to search audit logs")
            
            # Perform search (simulated)
            results = await self._search_audit_logs(query, filters, limit, offset)
            total_count = await self._get_search_result_count(query, filters)
            
            return {
                "results": results,
                "total": total_count,
                "query": query,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error("Audit log search failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def get_security_events(self, user_id: str, user_role: UserRole,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get security-related audit events
        
        Args:
            user_id: User ID requesting security events
            user_role: User role
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of events
            
        Returns:
            List of security events
        """
        try:
            # Check permissions
            if not self.rbac_service.can_view_all_audit_logs(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to view security events")
            
            # Get security events (simulated)
            security_events = [
                {
                    "id": "audit-123",
                    "action": AuditAction.SQL_INJECTION_ATTEMPT.value,
                    "user_id": "user-456",
                    "timestamp": datetime.utcnow() - timedelta(hours=2),
                    "details": {
                        "sql_query": "SELECT * FROM users WHERE id = 1 OR 1=1",
                        "injection_type": "BOOLEAN_BASED",
                        "ip_address": "192.168.1.100"
                    },
                    "severity": AuditSeverity.CRITICAL.value
                },
                {
                    "id": "audit-124",
                    "action": AuditAction.UNAUTHORIZED_ACCESS.value,
                    "user_id": "user-789",
                    "timestamp": datetime.utcnow() - timedelta(hours=1),
                    "details": {
                        "resource": "admin_panel",
                        "ip_address": "10.0.0.50"
                    },
                    "severity": AuditSeverity.CRITICAL.value
                }
            ]
            
            return security_events[:limit]
            
        except Exception as e:
            logger.error("Security events retrieval failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def cleanup_old_logs(self, retention_days: int, user_id: str, user_role: UserRole) -> Dict[str, Any]:
        """
        Clean up old audit logs based on retention policy
        
        Args:
            retention_days: Number of days to retain logs
            user_id: User ID performing cleanup
            user_role: User role
            
        Returns:
            Cleanup result
        """
        try:
            # Check permissions
            if not self.rbac_service.can_perform_system_administration(
                User(id=user_id, role=user_role, is_active=True)
            ):
                raise PermissionError("Insufficient permissions to cleanup audit logs")
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Get logs to delete
            logs_to_delete = await self._get_logs_older_than(cutoff_date)
            
            # Archive logs before deletion (if configured)
            archived_count = await self._archive_logs(logs_to_delete)
            
            # Delete logs
            deleted_count = await self._delete_logs(logs_to_delete)
            
            # Log cleanup action
            await self.log_event(
                user_id=user_id,
                action=AuditAction.SYSTEM_ERROR,  # Use appropriate action
                resource_type=AuditResourceType.SYSTEM,
                resource_id=str(uuid.uuid4()),
                details={
                    "retention_days": retention_days,
                    "cutoff_date": cutoff_date.isoformat(),
                    "archived_count": archived_count,
                    "deleted_count": deleted_count
                }
            )
            
            return {
                "archived_count": archived_count,
                "deleted_count": deleted_count,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error("Audit log cleanup failed", 
                        user_id=user_id, 
                        error=str(e))
            raise

    async def _save_audit_log(self, audit_log: AuditLog) -> None:
        """Save audit log to database (simulated)"""
        # In real implementation, this would save to immutable audit database
        logger.info("Audit log saved", 
                   audit_id=audit_log.id, 
                   action=audit_log.action.value)

    async def _get_audit_logs_with_filters(self, filters: Optional[AuditLogFilter], 
                                         limit: int, offset: int) -> List[Dict[str, Any]]:
        """Get audit logs with filters (simulated)"""
        # In real implementation, this would query the audit database
        logs = [
            {
                "id": "audit-123",
                "user_id": "user-123",
                "action": AuditAction.SQL_EXECUTION.value,
                "resource_type": AuditResourceType.QUERY.value,
                "resource_id": "query-456",
                "details": {
                    "sql_query": "SELECT * FROM users LIMIT 10",
                    "database_id": "db-789",
                    "row_count": 10
                },
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "timestamp": datetime.utcnow(),
                "severity": AuditSeverity.INFO.value
            }
        ]
        
        return logs[offset:offset + limit]

    async def _get_audit_log_count_with_filters(self, filters: Optional[AuditLogFilter]) -> int:
        """Get audit log count with filters (simulated)"""
        # In real implementation, this would count logs in database
        return 1

    async def _get_audit_logs_for_export(self, export_request: AuditLogExport) -> List[Dict[str, Any]]:
        """Get audit logs for export (simulated)"""
        # In real implementation, this would query logs based on export filters
        return [
            {
                "id": "audit-123",
                "user_id": "user-123",
                "action": AuditAction.SQL_EXECUTION.value,
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"sql_query": "SELECT * FROM users"}
            }
        ]

    async def _generate_export_file(self, export_id: str, logs: List[Dict[str, Any]], 
                                 format: str) -> str:
        """Generate export file (simulated)"""
        # In real implementation, this would generate actual export files
        file_path = f"/tmp/audit_export_{export_id}.{format}"
        
        if format == "json":
            with open(file_path, "w") as f:
                json.dump(logs, f, indent=2)
        elif format == "csv":
            # Generate CSV export
            pass
        elif format == "xlsx":
            # Generate Excel export
            pass
        
        return file_path

    async def _search_audit_logs(self, query: str, filters: Optional[AuditLogFilter], 
                               limit: int, offset: int) -> List[Dict[str, Any]]:
        """Search audit logs (simulated)"""
        # In real implementation, this would perform full-text search
        return []

    async def _get_search_result_count(self, query: str, filters: Optional[AuditLogFilter]) -> int:
        """Get search result count (simulated)"""
        # In real implementation, this would count search results
        return 0

    async def _get_logs_older_than(self, cutoff_date: datetime) -> List[str]:
        """Get log IDs older than cutoff date (simulated)"""
        # In real implementation, this would query logs older than cutoff
        return ["audit-old-1", "audit-old-2"]

    async def _archive_logs(self, log_ids: List[str]) -> int:
        """Archive logs before deletion (simulated)"""
        # In real implementation, this would archive to cold storage
        return len(log_ids)

    async def _delete_logs(self, log_ids: List[str]) -> int:
        """Delete logs (simulated)"""
        # In real implementation, this would delete from audit database
        return len(log_ids)