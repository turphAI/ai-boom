const fs = require('fs');
const path = require('path');

async function debugRealData() {
  const dataDir = path.join(process.cwd(), 'data');
  console.log('🔍 Data directory:', dataDir);
  
  try {
    const files = await fs.promises.readdir(dataDir);
    const jsonFiles = files.filter(file => file.endsWith('.json'));
    console.log('📁 JSON files found:', jsonFiles);
    
    for (const file of jsonFiles) {
      const filePath = path.join(dataDir, file);
      console.log(`\n📖 Reading: ${file}`);
      
      const content = await fs.promises.readFile(filePath, 'utf-8');
      const data = JSON.parse(content);
      
      console.log(`📊 Data type: ${Array.isArray(data) ? 'Array' : 'Object'}`);
      console.log(`📊 Data length: ${Array.isArray(data) ? data.length : 'N/A'}`);
      
      if (Array.isArray(data) && data.length > 0) {
        const first = data[0];
        console.log(`📈 First item:`, {
          data_source: first.data_source,
          metric_name: first.metric_name,
          timestamp: first.timestamp,
          value: first.data?.value
        });
      }
    }
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

debugRealData();
