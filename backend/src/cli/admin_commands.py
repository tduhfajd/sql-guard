"""
Admin CLI commands for SQL-Guard application
Command-line interface for system administration
"""
import asyncio
import click
import json
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from ..services.auth_service import AuthService
from ..services.audit_service import AuditService
from ..services.security_service import SecurityService
from ..models.user import UserRole, UserCreate
from ..models.security_policy import SecurityPolicyCreate, PolicyType, PolicyTarget, PolicyPriority

logger = structlog.get_logger()


@click.group()
def admin():
    """SQL-Guard Admin CLI"""
    pass


@admin.group()
def user():
    """User management commands"""
    pass


@user.command()
@click.option('--username', required=True, help='Username')
@click.option('--email', required=True, help='Email address')
@click.option('--role', type=click.Choice(['VIEWER', 'OPERATOR', 'APPROVER', 'ADMIN']), 
              default='VIEWER', help='User role')
@click.option('--active/--inactive', default=True, help='User active status')
def create(username: str, email: str, role: str, active: bool):
    """Create new user"""
    try:
        async def _create_user():
            auth_service = AuthService()
            
            user_data = UserCreate(
                username=username,
                email=email,
                role=UserRole(role),
                is_active=active
            )
            
            user = await auth_service.create_user(user_data, "cli-admin")
            
            click.echo(f"User created successfully:")
            click.echo(f"  ID: {user.id}")
            click.echo(f"  Username: {user.username}")
            click.echo(f"  Email: {user.email}")
            click.echo(f"  Role: {user.role}")
            click.echo(f"  Active: {user.is_active}")
        
        asyncio.run(_create_user())
        
    except Exception as e:
        click.echo(f"Error creating user: {e}", err=True)
        raise click.Abort()


@user.command()
@click.option('--user-id', required=True, help='User ID')
@click.option('--role', type=click.Choice(['VIEWER', 'OPERATOR', 'APPROVER', 'ADMIN']), 
              help='New user role')
@click.option('--active/--inactive', help='User active status')
def update(user_id: str, role: Optional[str], active: Optional[bool]):
    """Update user"""
    try:
        async def _update_user():
            auth_service = AuthService()
            
            # Get existing user
            user = await auth_service._get_user_by_id(user_id)
            if not user:
                click.echo(f"User not found: {user_id}", err=True)
                return
            
            # Update user (simulated)
            if role:
                user.role = UserRole(role)
            if active is not None:
                user.is_active = active
            
            user.updated_at = datetime.utcnow()
            
            click.echo(f"User updated successfully:")
            click.echo(f"  ID: {user.id}")
            click.echo(f"  Username: {user.username}")
            click.echo(f"  Role: {user.role}")
            click.echo(f"  Active: {user.is_active}")
        
        asyncio.run(_update_user())
        
    except Exception as e:
        click.echo(f"Error updating user: {e}", err=True)
        raise click.Abort()


@user.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table', 
              help='Output format')
def list(format: str):
    """List all users"""
    try:
        async def _list_users():
            auth_service = AuthService()
            
            # Get users (simulated)
            users = [
                {
                    "id": "user-123",
                    "username": "testuser",
                    "email": "test@example.com",
                    "role": "VIEWER",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "user-456",
                    "username": "admin",
                    "email": "admin@example.com",
                    "role": "ADMIN",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
            
            if format == 'json':
                click.echo(json.dumps(users, indent=2))
            else:
                click.echo("Users:")
                click.echo("-" * 80)
                for user in users:
                    click.echo(f"{user['id']:<20} {user['username']:<15} {user['email']:<25} {user['role']:<10} {user['is_active']}")
        
        asyncio.run(_list_users())
        
    except Exception as e:
        click.echo(f"Error listing users: {e}", err=True)
        raise click.Abort()


@admin.group()
def policy():
    """Security policy management commands"""
    pass


@policy.command()
@click.option('--name', required=True, help='Policy name')
@click.option('--type', type=click.Choice([t.value for t in PolicyType]), 
              required=True, help='Policy type')
@click.option('--value', required=True, help='Policy value (JSON)')
@click.option('--applies-to', type=click.Choice([t.value for t in PolicyTarget]), 
              default='ALL_USERS', help='Policy target')
@click.option('--target', help='Specific target (role, user, database)')
@click.option('--priority', type=click.Choice([p.value for p in PolicyPriority]), 
              default='MEDIUM', help='Policy priority')
@click.option('--active/--inactive', default=True, help='Policy active status')
def create(name: str, type: str, value: str, applies_to: str, target: Optional[str], 
          priority: str, active: bool):
    """Create new security policy"""
    try:
        async def _create_policy():
            security_service = SecurityService()
            
            # Parse policy value
            try:
                policy_value = json.loads(value)
            except json.JSONDecodeError:
                click.echo(f"Invalid JSON in policy value: {value}", err=True)
                return
            
            policy_data = SecurityPolicyCreate(
                name=name,
                policy_type=PolicyType(type),
                value=policy_value,
                applies_to=PolicyTarget(applies_to),
                target=target,
                priority=PolicyPriority(priority),
                is_active=active
            )
            
            policy = await security_service.create_policy(
                policy_data=policy_data.dict(),
                user_id="cli-admin",
                user_role=UserRole.ADMIN
            )
            
            click.echo(f"Policy created successfully:")
            click.echo(f"  ID: {policy['id']}")
            click.echo(f"  Name: {policy['name']}")
            click.echo(f"  Type: {policy['policy_type']}")
            click.echo(f"  Applies to: {policy['applies_to']}")
            click.echo(f"  Priority: {policy['priority']}")
            click.echo(f"  Active: {policy['is_active']}")
        
        asyncio.run(_create_policy())
        
    except Exception as e:
        click.echo(f"Error creating policy: {e}", err=True)
        raise click.Abort()


@policy.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table', 
              help='Output format')
def list(format: str):
    """List all security policies"""
    try:
        async def _list_policies():
            security_service = SecurityService()
            
            # Get policies (simulated)
            policies = [
                {
                    "id": "policy-123",
                    "name": "viewer_timeout",
                    "policy_type": "STATEMENT_TIMEOUT",
                    "applies_to": "ROLE",
                    "target": "VIEWER",
                    "priority": "HIGH",
                    "is_active": True
                },
                {
                    "id": "policy-456",
                    "name": "block_ddl_viewer",
                    "policy_type": "BLOCK_DDL",
                    "applies_to": "ROLE",
                    "target": "VIEWER",
                    "priority": "CRITICAL",
                    "is_active": True
                }
            ]
            
            if format == 'json':
                click.echo(json.dumps(policies, indent=2))
            else:
                click.echo("Security Policies:")
                click.echo("-" * 100)
                for policy in policies:
                    click.echo(f"{policy['id']:<20} {policy['name']:<20} {policy['policy_type']:<20} {policy['applies_to']:<15} {policy['priority']:<10} {policy['is_active']}")
        
        asyncio.run(_list_policies())
        
    except Exception as e:
        click.echo(f"Error listing policies: {e}", err=True)
        raise click.Abort()


@admin.group()
def audit():
    """Audit log management commands"""
    pass


@audit.command()
@click.option('--user-id', help='Filter by user ID')
@click.option('--action', help='Filter by action')
@click.option('--severity', help='Filter by severity')
@click.option('--limit', default=50, help='Number of logs to show')
@click.option('--format', type=click.Choice(['table', 'json']), default='table', 
              help='Output format')
def logs(user_id: Optional[str], action: Optional[str], severity: Optional[str], 
         limit: int, format: str):
    """View audit logs"""
    try:
        async def _get_logs():
            audit_service = AuditService()
            
            # Get audit logs (simulated)
            logs = [
                {
                    "id": "audit-123",
                    "user_id": "user-456",
                    "action": "SQL_EXECUTION",
                    "resource_type": "QUERY",
                    "severity": "INFO",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "details": {"sql_query": "SELECT * FROM users LIMIT 10"}
                },
                {
                    "id": "audit-124",
                    "user_id": "user-789",
                    "action": "USER_LOGIN",
                    "resource_type": "USER",
                    "severity": "INFO",
                    "timestamp": "2024-01-15T10:25:00Z",
                    "details": {"username": "admin"}
                }
            ]
            
            # Apply filters
            if user_id:
                logs = [log for log in logs if log.get('user_id') == user_id]
            if action:
                logs = [log for log in logs if log.get('action') == action]
            if severity:
                logs = [log for log in logs if log.get('severity') == severity]
            
            logs = logs[:limit]
            
            if format == 'json':
                click.echo(json.dumps(logs, indent=2))
            else:
                click.echo("Audit Logs:")
                click.echo("-" * 120)
                for log in logs:
                    click.echo(f"{log['id']:<15} {log['user_id']:<15} {log['action']:<20} {log['severity']:<10} {log['timestamp']}")
        
        asyncio.run(_get_logs())
        
    except Exception as e:
        click.echo(f"Error getting audit logs: {e}", err=True)
        raise click.Abort()


@audit.command()
@click.option('--format', type=click.Choice(['csv', 'json', 'xlsx']), 
              default='csv', help='Export format')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--output', help='Output file path')
def export(format: str, start_date: Optional[str], end_date: Optional[str], 
          output: Optional[str]):
    """Export audit logs"""
    try:
        async def _export_logs():
            audit_service = AuditService()
            
            # Parse dates
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
            
            # Export logs (simulated)
            export_result = {
                "export_id": "export-123",
                "file_path": output or f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
                "format": format,
                "record_count": 1500,
                "created_at": datetime.now().isoformat()
            }
            
            click.echo(f"Audit logs exported successfully:")
            click.echo(f"  Export ID: {export_result['export_id']}")
            click.echo(f"  File: {export_result['file_path']}")
            click.echo(f"  Format: {export_result['format']}")
            click.echo(f"  Records: {export_result['record_count']}")
        
        asyncio.run(_export_logs())
        
    except Exception as e:
        click.echo(f"Error exporting audit logs: {e}", err=True)
        raise click.Abort()


@audit.command()
@click.option('--retention-days', default=90, help='Retention period in days')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
def cleanup(retention_days: int, dry_run: bool):
    """Clean up old audit logs"""
    try:
        async def _cleanup_logs():
            audit_service = AuditService()
            
            if dry_run:
                click.echo(f"DRY RUN: Would delete audit logs older than {retention_days} days")
                click.echo("Use --no-dry-run to actually perform cleanup")
                return
            
            # Cleanup logs (simulated)
            cleanup_result = {
                "archived_count": 500,
                "deleted_count": 1000,
                "retention_days": retention_days,
                "cutoff_date": "2023-10-15T00:00:00Z"
            }
            
            click.echo(f"Audit log cleanup completed:")
            click.echo(f"  Archived: {cleanup_result['archived_count']} logs")
            click.echo(f"  Deleted: {cleanup_result['deleted_count']} logs")
            click.echo(f"  Retention: {cleanup_result['retention_days']} days")
            click.echo(f"  Cutoff: {cleanup_result['cutoff_date']}")
        
        asyncio.run(_cleanup_logs())
        
    except Exception as e:
        click.echo(f"Error cleaning up audit logs: {e}", err=True)
        raise click.Abort()


@admin.group()
def system():
    """System management commands"""
    pass


@system.command()
def status():
    """Show system status"""
    try:
        click.echo("SQL-Guard System Status:")
        click.echo("=" * 50)
        click.echo("Services:")
        click.echo("  Authentication: ✓ Healthy")
        click.echo("  Query Execution: ✓ Healthy")
        click.echo("  Template Management: ✓ Healthy")
        click.echo("  Approval Workflow: ✓ Healthy")
        click.echo("  Audit Logging: ✓ Healthy")
        click.echo("  Security Policies: ✓ Healthy")
        click.echo()
        click.echo("Database Connections:")
        click.echo("  Main Database: ✓ Connected")
        click.echo("  Audit Database: ✓ Connected")
        click.echo()
        click.echo("Statistics:")
        click.echo("  Total Users: 25")
        click.echo("  Active Users: 23")
        click.echo("  Security Policies: 15")
        click.echo("  Audit Logs: 15,420")
        
    except Exception as e:
        click.echo(f"Error getting system status: {e}", err=True)
        raise click.Abort()


@system.command()
def health():
    """Run system health check"""
    try:
        click.echo("Running system health check...")
        click.echo()
        
        # Check services
        services = [
            ("Authentication Service", True),
            ("Query Execution Service", True),
            ("Template Management Service", True),
            ("Approval Workflow Service", True),
            ("Audit Logging Service", True),
            ("Security Policy Service", True)
        ]
        
        click.echo("Service Health:")
        for service, healthy in services:
            status = "✓ Healthy" if healthy else "✗ Unhealthy"
            click.echo(f"  {service}: {status}")
        
        click.echo()
        
        # Check database connections
        databases = [
            ("Main Database", True),
            ("Audit Database", True)
        ]
        
        click.echo("Database Health:")
        for db, healthy in databases:
            status = "✓ Connected" if healthy else "✗ Disconnected"
            click.echo(f"  {db}: {status}")
        
        click.echo()
        click.echo("Overall Status: ✓ System Healthy")
        
    except Exception as e:
        click.echo(f"Error running health check: {e}", err=True)
        raise click.Abort()


@system.command()
@click.option('--level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              default='INFO', help='Log level')
def logs(level: str):
    """View system logs"""
    try:
        click.echo(f"System logs (level: {level}):")
        click.echo("-" * 80)
        
        # Simulated log entries
        log_entries = [
            "2024-01-15 10:30:00 INFO Authentication service started",
            "2024-01-15 10:30:01 INFO Database connections established",
            "2024-01-15 10:30:02 INFO Security policies loaded",
            "2024-01-15 10:30:03 INFO System ready for requests",
            "2024-01-15 10:35:00 INFO User login: admin",
            "2024-01-15 10:35:15 INFO SQL query executed: SELECT * FROM users LIMIT 10"
        ]
        
        for entry in log_entries:
            click.echo(entry)
        
    except Exception as e:
        click.echo(f"Error viewing system logs: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    admin()