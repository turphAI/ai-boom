const Database = require('better-sqlite3');
const path = require('path');

// Create/connect to local SQLite database
const dbPath = path.join(__dirname, '..', 'local.db');
const db = new Database(dbPath);

// Create metrics_data table if it doesn't exist
db.exec(`
  CREATE TABLE IF NOT EXISTS metrics_data (
    id TEXT PRIMARY KEY,
    data_source TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
`);

// Create index for efficient queries
db.exec(`
  CREATE INDEX IF NOT EXISTS idx_metrics_data_source_name 
  ON metrics_data(data_source, metric_name);
`);

db.exec(`
  CREATE INDEX IF NOT EXISTS idx_metrics_data_timestamp 
  ON metrics_data(timestamp);
`);

// Generate historical data with appropriate frequencies
function generateHistoricalData() {
  const now = new Date();
  const data = [];
  
  // Base values and volatility for each metric
  const metrics = {
    bond_issuance: { base: 3000000000, volatility: 0.3, unit: 'currency', frequency: 'daily' },
    bdc_discount: { base: 8.0, volatility: 0.2, unit: 'percent', frequency: 'daily' },
    credit_fund: { base: 120000000000, volatility: 0.05, unit: 'currency', frequency: 'quarterly' },
    bank_provision: { base: 11.5, volatility: 0.15, unit: 'percent', frequency: 'quarterly' }
  };

  // Generate data for different frequencies
  Object.entries(metrics).forEach(([metricName, config]) => {
    if (config.frequency === 'daily') {
      // Generate 365 days of daily data
      for (let i = 365; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        
        // Add realistic variation
        const variation = (Math.random() - 0.5) * config.volatility * config.base;
        const value = Math.max(0, config.base + variation);
        
        // Add some trend (gradual increase/decrease over time)
        const trendFactor = 1 + (i / 365) * 0.15; // 15% change over 365 days
        const finalValue = value * trendFactor;
        
        data.push({
          id: `${metricName}_${date.toISOString().split('T')[0]}`,
          data_source: 'scraper',
          metric_name: metricName,
          timestamp: date.toISOString(),
          value: finalValue,
          unit: config.unit,
          confidence: 0.9 + Math.random() * 0.1,
          metadata: JSON.stringify({
            source: 'historical_population',
            frequency: 'daily',
            trend_factor: trendFactor,
            variation: variation
          })
        });
      }
    } else if (config.frequency === 'quarterly') {
      // Generate 16 quarters (4 years) of quarterly data
      for (let i = 16; i >= 0; i--) {
        const date = new Date(now);
        date.setMonth(date.getMonth() - (i * 3)); // 3 months per quarter
        
        // Set to end of quarter (last day of March, June, September, December)
        const quarter = Math.floor(date.getMonth() / 3);
        const quarterEndMonth = (quarter + 1) * 3 - 1; // 2, 5, 8, 11 (March, June, September, December)
        date.setMonth(quarterEndMonth);
        date.setDate(new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()); // Last day of month
        
        // Add realistic variation
        const variation = (Math.random() - 0.5) * config.volatility * config.base;
        const value = Math.max(0, config.base + variation);
        
        // Add some trend (gradual increase/decrease over quarters)
        const trendFactor = 1 + (i / 16) * 0.3; // 30% change over 16 quarters
        const finalValue = value * trendFactor;
        
        data.push({
          id: `${metricName}_${date.toISOString().split('T')[0]}`,
          data_source: 'scraper',
          metric_name: metricName,
          timestamp: date.toISOString(),
          value: finalValue,
          unit: config.unit,
          confidence: 0.95 + Math.random() * 0.05, // Higher confidence for quarterly data
          metadata: JSON.stringify({
            source: 'historical_population',
            frequency: 'quarterly',
            quarter: quarter + 1,
            trend_factor: trendFactor,
            variation: variation
          })
        });
      }
    }
  });
  
  return data;
}

// Insert historical data
function insertHistoricalData() {
  const data = generateHistoricalData();
  
  const insert = db.prepare(`
    INSERT OR REPLACE INTO metrics_data 
    (id, data_source, metric_name, timestamp, value, unit, confidence, metadata, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
  `);
  
  const insertMany = db.transaction((data) => {
    for (const record of data) {
      insert.run(
        record.id,
        record.data_source,
        record.metric_name,
        record.timestamp,
        record.value,
        record.unit,
        record.confidence,
        record.metadata
      );
    }
  });
  
  insertMany(data);
  console.log(`✅ Inserted ${data.length} historical data points`);
}

// Main execution
console.log('🚀 Populating historical metrics data...');
insertHistoricalData();

// Show some sample data
console.log('\n📊 Sample data:');
const sample = db.prepare(`
  SELECT * FROM metrics_data 
  ORDER BY timestamp DESC 
  LIMIT 10
`).all();

sample.forEach(record => {
  console.log(`${record.metric_name}: ${record.value} ${record.unit} (${record.timestamp})`);
});

console.log('\n✅ Historical data population complete!');
db.close();
