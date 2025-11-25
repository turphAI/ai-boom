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

# Create direct database connection using pymysql
try:
    import pymysql
    db_available = True
except ImportError:
    logging.warning("pymysql not available. Install with: pip install pymysql")
    db_available = False

logger = logging.getLogger(__name__)

class PlanetScaleDataService:
    """Service for managing financial data in PlanetScale database."""
    
    def __init__(self):
        if not db_available:
            logger.error("pymysql not available")
            raise RuntimeError("pymysql not available")
        
        # Parse DATABASE_URL
        self.connection_params = self._parse_database_url()
        self.connection = None
        
    def _parse_database_url(self):
        """Parse DATABASE_URL into connection parameters."""
        url = os.getenv('DATABASE_URL', '')
        if not url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Clean up URL - remove any leading "DATABASE_URL=" or quotes
        url = url.strip()
        if url.startswith("DATABASE_URL="):
            url = url[13:].strip()  # Remove "DATABASE_URL="
        if url.startswith("'") and url.endswith("'"):
            url = url[1:-1]  # Remove surrounding single quotes
        if url.startswith('"') and url.endswith('"'):
            url = url[1:-1]  # Remove surrounding double quotes
        
        # Parse mysql://username:password@host:port/database?ssl={"rejectUnauthorized":true}
        if url.startswith('mysql://'):
            url = url[8:]  # Remove mysql://
            
            # Split on @ to separate credentials from host/database
            if '@' in url:
                creds, host_db = url.split('@', 1)
                if ':' in creds:
                    username, password = creds.split(':', 1)
                else:
                    username = creds
                    password = ''
            else:
                username = ''
                password = ''
                host_db = url
            
            # Split host/database part
            if '/' in host_db:
                host_port, database = host_db.split('/', 1)
                # Remove SSL parameters
                if '?' in database:
                    database = database.split('?')[0]
            else:
                host_port = host_db
                database = ''
            
            # Split host and port
            if ':' in host_port:
                host, port = host_port.split(':', 1)
                port = int(port)
            else:
                host = host_port
                port = 3306
            
            return {
                'host': host,
                'port': port,
                'user': username,
                'password': password,
                'database': database,
                'charset': 'utf8mb4',
                'autocommit': True,
                'ssl': {'ssl_disabled': False}
            }
        else:
            raise ValueError(f"Unsupported database URL format: {url}")
    
    def _get_connection(self):
        """Get database connection."""
        if self.connection is None:
            try:
                self.connection = pymysql.connect(**self.connection_params)
                logger.info("Connected to PlanetScale database")
            except Exception as e:
                logger.error(f"Error connecting to PlanetScale: {e}")
                raise
        return self.connection
    
    def _execute_query(self, query, params=None):
        """Execute a query and return results."""
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                cursor.close()
                return results
            else:
                connection.commit()
                cursor.close()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def store_metric_data(self, data_source: str, metric_name: str, data: Dict[str, Any]) -> bool:
        """Store metric data in PlanetScale."""
        try:
            metric_id = f"{data_source}_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Prepare metric data
            import json
            status = self._determine_status(data)
            confidence = str(data.get('confidence', 1.0))
            unit = data.get('unit', '')
            metadata = json.dumps(data.get('metadata', {})) if data.get('metadata') else '{}'
            raw_data = json.dumps(data) if data else '{}'
            
            # Insert or update metric
            query = """
                INSERT INTO metrics (id, data_source, metric_name, value, unit, status, confidence, metadata, raw_data, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    value = VALUES(value),
                    status = VALUES(status),
                    confidence = VALUES(confidence),
                    metadata = VALUES(metadata),
                    raw_data = VALUES(raw_data),
                    updated_at = NOW()
            """
            params = (
                metric_id,
                data_source,
                metric_name,
                str(data['value']),
                unit,
                status,
                confidence,
                metadata,
                raw_data
            )
            
            self._execute_query(query, params)
            
            # Store in history table
            history_id = f"hist_{metric_id}"
            history_query = """
                INSERT INTO metric_history (id, metric_id, value, status, confidence, metadata, raw_data, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            history_params = (
                history_id,
                metric_id,
                str(data['value']),
                status,
                confidence,
                json.dumps(data.get('metadata', {})),
                json.dumps(data)
            )
            
            self._execute_query(history_query, history_params)
            
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
            
            results = self._execute_query(query, params)
            
            metrics_list = []
            for row in results:
                metrics_list.append({
                    'id': row[0],
                    'dataSource': row[1],
                    'metricName': row[2],
                    'value': float(row[3]) if row[3] else 0.0,
                    'unit': row[4] or '',
                    'status': row[5] or 'unknown',
                    'confidence': float(row[6]) if row[6] else 0.0,
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
