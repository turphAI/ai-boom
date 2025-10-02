"""
PlanetScale Data Service for storing and retrieving real financial data.

This service manages the storage of credit fund and bank provision data in PlanetScale,
replacing local file storage with a proper database solution.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging

# Add the dashboard directory to the path to import the database schema
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'src'))

try:
    from lib.db.connection import db
    from lib.db.schema import metrics, metricHistory, scraperHealth, NewMetric, NewMetricHistory, NewScraperHealth
except ImportError as e:
    logging.warning(f"Could not import database schema: {e}")
    db = None

logger = logging.getLogger(__name__)

class PlanetScaleDataService:
    """Service for managing financial data in PlanetScale database."""
    
    def __init__(self):
        self.db = db
        if not self.db:
            logger.error("Database connection not available")
            raise RuntimeError("Database connection not available")
    
    def store_metric_data(self, data_source: str, metric_name: str, data: Dict[str, Any]) -> bool:
        """Store metric data in PlanetScale."""
        try:
            metric_id = f"{data_source}_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Prepare metric data
            metric_data: NewMetric = {
                'id': metric_id,
                'dataSource': data_source,
                'metricName': metric_name,
                'value': str(data['value']),
                'unit': data.get('unit', ''),
                'status': self._determine_status(data),
                'confidence': str(data.get('confidence', 1.0)),
                'metadata': data.get('metadata', {}),
                'rawData': data
            }
            
            # Insert or update metric
            result = self.db.execute(
                f"""
                INSERT INTO metrics (id, data_source, metric_name, value, unit, status, confidence, metadata, raw_data, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    value = VALUES(value),
                    status = VALUES(status),
                    confidence = VALUES(confidence),
                    metadata = VALUES(metadata),
                    raw_data = VALUES(raw_data),
                    updated_at = NOW()
                """,
                (
                    metric_data['id'],
                    metric_data['dataSource'],
                    metric_data['metricName'],
                    metric_data['value'],
                    metric_data['unit'],
                    metric_data['status'],
                    metric_data['confidence'],
                    str(metric_data['metadata']) if metric_data['metadata'] else None,
                    str(metric_data['rawData']) if metric_data['rawData'] else None
                )
            )
            
            # Store in history table
            history_data: NewMetricHistory = {
                'id': f"hist_{metric_id}",
                'metricId': metric_id,
                'value': str(data['value']),
                'status': self._determine_status(data),
                'confidence': str(data.get('confidence', 1.0)),
                'metadata': data.get('metadata', {}),
                'rawData': data
            }
            
            self.db.execute(
                f"""
                INSERT INTO metric_history (id, metric_id, value, status, confidence, metadata, raw_data, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    history_data['id'],
                    history_data['metricId'],
                    history_data['value'],
                    history_data['status'],
                    history_data['confidence'],
                    str(history_data['metadata']) if history_data['metadata'] else None,
                    str(history_data['rawData']) if history_data['rawData'] else None
                )
            )
            
            logger.info(f"Successfully stored metric data for {data_source}/{metric_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing metric data: {e}")
            return False
    
    def store_scraper_health(self, scraper_name: str, status: str, execution_time: Optional[int] = None, error_message: Optional[str] = None) -> bool:
        """Store scraper health status in PlanetScale."""
        try:
            health_data: NewScraperHealth = {
                'id': f"health_{scraper_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'scraperName': scraper_name,
                'status': status,
                'lastRun': datetime.now(timezone.utc),
                'nextRun': self._calculate_next_run_time(scraper_name),
                'errorMessage': error_message,
                'executionTime': execution_time,
                'dataQuality': self._determine_data_quality(status)
            }
            
            result = self.db.execute(
                f"""
                INSERT INTO scraper_health (id, scraper_name, status, last_run, next_run, error_message, execution_time, data_quality, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    last_run = VALUES(last_run),
                    next_run = VALUES(next_run),
                    error_message = VALUES(error_message),
                    execution_time = VALUES(execution_time),
                    data_quality = VALUES(data_quality),
                    updated_at = NOW()
                """,
                (
                    health_data['id'],
                    health_data['scraperName'],
                    health_data['status'],
                    health_data['lastRun'],
                    health_data['nextRun'],
                    health_data['errorMessage'],
                    health_data['executionTime'],
                    health_data['dataQuality']
                )
            )
            
            logger.info(f"Successfully stored scraper health for {scraper_name}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing scraper health: {e}")
            return False
    
    def get_latest_metrics(self, data_source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get the latest metrics from PlanetScale."""
        try:
            query = """
                SELECT id, data_source, metric_name, value, unit, status, confidence, metadata, raw_data, created_at, updated_at
                FROM metrics
            """
            params = []
            
            if data_source:
                query += " WHERE data_source = %s"
                params.append(data_source)
            
            query += " ORDER BY updated_at DESC LIMIT 100"
            
            result = self.db.execute(query, params)
            
            metrics_list = []
            for row in result:
                metrics_list.append({
                    'id': row[0],
                    'dataSource': row[1],
                    'metricName': row[2],
                    'value': float(row[3]),
                    'unit': row[4],
                    'status': row[5],
                    'confidence': float(row[6]),
                    'metadata': row[7],
                    'rawData': row[8],
                    'createdAt': row[9],
                    'updatedAt': row[10]
                })
            
            return metrics_list
            
        except Exception as e:
            logger.error(f"Error retrieving latest metrics: {e}")
            return []
    
    def get_metric_history(self, metric_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric."""
        try:
            query = """
                SELECT id, metric_id, value, status, confidence, metadata, raw_data, created_at
                FROM metric_history
                WHERE metric_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY created_at DESC
            """
            
            result = self.db.execute(query, (metric_id, days))
            
            history_list = []
            for row in result:
                history_list.append({
                    'id': row[0],
                    'metricId': row[1],
                    'value': float(row[2]),
                    'status': row[3],
                    'confidence': float(row[4]),
                    'metadata': row[5],
                    'rawData': row[6],
                    'createdAt': row[7]
                })
            
            return history_list
            
        except Exception as e:
            logger.error(f"Error retrieving metric history: {e}")
            return []
    
    def get_scraper_health_status(self) -> List[Dict[str, Any]]:
        """Get current scraper health status."""
        try:
            query = """
                SELECT scraper_name, status, last_run, next_run, error_message, execution_time, data_quality
                FROM scraper_health
                WHERE scraper_name IN ('credit_fund', 'bank_provision', 'bond_issuance', 'bdc_discount')
                ORDER BY last_run DESC
            """
            
            result = self.db.execute(query)
            
            health_list = []
            for row in result:
                health_list.append({
                    'scraperName': row[0],
                    'status': row[1],
                    'lastRun': row[2],
                    'nextRun': row[3],
                    'errorMessage': row[4],
                    'executionTime': row[5],
                    'dataQuality': row[6]
                })
            
            return health_list
            
        except Exception as e:
            logger.error(f"Error retrieving scraper health: {e}")
            return []
    
    def _determine_status(self, data: Dict[str, Any]) -> str:
        """Determine metric status based on data quality and confidence."""
        confidence = data.get('confidence', 1.0)
        metadata = data.get('metadata', {})
        data_quality = metadata.get('data_quality', 'medium')
        
        if confidence >= 0.9 and data_quality == 'high':
            return 'healthy'
        elif confidence >= 0.7 and data_quality in ['high', 'medium']:
            return 'warning'
        elif confidence >= 0.5:
            return 'critical'
        else:
            return 'stale'
    
    def _determine_data_quality(self, status: str) -> str:
        """Determine data quality based on scraper status."""
        if status == 'healthy':
            return 'high'
        elif status == 'degraded':
            return 'medium'
        else:
            return 'low'
    
    def _calculate_next_run_time(self, scraper_name: str) -> datetime:
        """Calculate next run time for a scraper."""
        # Run every hour for credit fund and bank provision scrapers
        if scraper_name in ['credit_fund', 'bank_provision']:
            return datetime.now(timezone.utc) + timedelta(hours=1)
        else:
            return datetime.now(timezone.utc) + timedelta(hours=6)
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """Clean up old metric history data."""
        try:
            # Keep only recent history data
            result = self.db.execute(
                "DELETE FROM metric_history WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)",
                (days_to_keep,)
            )
            
            logger.info(f"Cleaned up metric history data older than {days_to_keep} days")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False
