const { realDataService } = require('./src/lib/data/real-data-service.ts');

async function testRealData() {
  console.log('Testing real data service...');
  
  try {
    const metrics = await realDataService.getLatestMetrics();
    console.log('Metrics found:', metrics.length);
    console.log('Metrics:', JSON.stringify(metrics, null, 2));
  } catch (error) {
    console.error('Error:', error);
  }
}

testRealData();
