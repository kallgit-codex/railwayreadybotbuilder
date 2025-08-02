"""
Health monitoring utilities for LLM Bot Builder
Provides system health checks and monitoring
"""
import time
import psutil
from datetime import datetime, timedelta
from config import get_config

config = get_config()

class HealthMonitor:
    """System health monitoring"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.config = config
    
    def get_system_health(self):
        """Get comprehensive system health status"""
        try:
            health_data = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'uptime': self._get_uptime(),
                'database': self._check_database(),
                'memory': self._get_memory_info(),
                'disk': self._get_disk_info(),
                'bots': self._get_bot_stats(),
                'deployments': self._get_deployment_stats(),
                'version': '1.0.0'
            }
            
            # Determine overall health status
            if not health_data['database']['healthy']:
                health_data['status'] = 'unhealthy'
            elif health_data['memory']['percent'] > 90:
                health_data['status'] = 'warning'
            elif health_data['disk']['percent'] > 90:
                health_data['status'] = 'warning'
            
            return health_data
            
        except Exception as e:
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def _get_uptime(self):
        """Get system uptime"""
        uptime = datetime.utcnow() - self.start_time
        return {
            'seconds': int(uptime.total_seconds()),
            'human_readable': str(uptime).split('.')[0]
        }
    
    def _check_database(self):
        """Check database connectivity and stats"""
        try:
            from flask import current_app
            from app import db
            
            with current_app.app_context():
                # Simple database connectivity test
                result = db.session.execute(db.text('SELECT 1')).fetchone()
                
                return {
                    'healthy': result is not None,
                    'connection_pool': {
                        'size': db.engine.pool.size(),
                        'checked_in': db.engine.pool.checkedin(),
                        'checked_out': db.engine.pool.checkedout()
                    }
                }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _get_memory_info(self):
        """Get memory usage information"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            }
        except Exception:
            return {'error': 'Memory info unavailable'}
    
    def _get_disk_info(self):
        """Get disk usage information"""
        try:
            disk = psutil.disk_usage('/')
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            }
        except Exception:
            return {'error': 'Disk info unavailable'}
    
    def _get_bot_stats(self):
        """Get bot statistics"""
        try:
            from flask import current_app
            from models import Bot, Client
            
            with current_app.app_context():
                total_bots = Bot.query.count()
                active_clients = Client.query.count()
            
            return {
                'total_bots': total_bots,
                'active_clients': active_clients
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_deployment_stats(self):
        """Get deployment statistics"""
        try:
            from flask import current_app
            from models import Deployment
            
            with current_app.app_context():
                total_deployments = Deployment.query.count()
                active_deployments = Deployment.query.filter(
                    Deployment.status == 'active'
                ).count()
            
            return {
                'total_deployments': total_deployments,
                'active_deployments': active_deployments
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_quick_health(self):
        """Get quick health check for rapid monitoring"""
        try:
            from flask import current_app
            from app import db
            
            with current_app.app_context():
                # Quick database check
                db.session.execute(db.text('SELECT 1')).fetchone()
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': int((datetime.utcnow() - self.start_time).total_seconds())
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }

# Global health monitor instance
health_monitor = HealthMonitor()