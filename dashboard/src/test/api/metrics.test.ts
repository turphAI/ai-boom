import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createMocks } from 'node-mocks-http';
import { getServerSession } from 'next-auth';
import currentMetricsHandler from '@/pages/api/metrics/current';
import historicalMetricsHandler from '@/pages/api/metrics/historical';

// Mock next-auth
vi.mock('next-auth', () => ({
  getServerSession: vi.fn(),
}));

// Mock database connection to prevent PlanetScale configuration errors
vi.mock('@/lib/db/connection', () => {
  const createChainableMock = () => {
    const mock: Record<string, ReturnType<typeof vi.fn>> = {};
    const chainMethods = ['select', 'from', 'where', 'limit', 'insert', 'values', 'update', 'set', 'delete'];
    
    chainMethods.forEach(method => {
      mock[method] = vi.fn().mockReturnValue(mock);
    });
    
    return mock;
  };

  return {
    db: createChainableMock(),
  };
});

// Mock state store client
vi.mock('@/lib/data/state-store-client', () => ({
  stateStoreClient: {
    getCurrentMetrics: vi.fn(),
    getHistoricalData: vi.fn(),
  },
}));

describe('/api/metrics/current', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return current metrics for authenticated user', async () => {
    // Mock authentication
    vi.mocked(getServerSession).mockResolvedValue({
      user: { id: 'user-1', email: 'test@example.com' },
    } as never);

    // Mock state store response
    const mockMetrics = [
      {
        dataSource: 'bond_issuance',
        metricName: 'weekly',
        value: 12500000000,
        timestamp: '2024-01-15T06:00:00Z',
        confidence: 0.95,
        metadata: { companies: ['MSFT'] }
      }
    ];

    const { stateStoreClient } = await import('@/lib/data/state-store-client');
    vi.mocked(stateStoreClient.getCurrentMetrics).mockResolvedValue(mockMetrics);

    const { req, res } = createMocks({
      method: 'GET',
    });

    await currentMetricsHandler(req, res);

    expect(res._getStatusCode()).toBe(200);
    const data = JSON.parse(res._getData());
    expect(data.metrics).toEqual(mockMetrics);
    expect(data.count).toBe(1);
  });

  it('should return 401 for unauthenticated user', async () => {
    vi.mocked(getServerSession).mockResolvedValue(null);

    const { req, res } = createMocks({
      method: 'GET',
    });

    await currentMetricsHandler(req, res);

    expect(res._getStatusCode()).toBe(401);
    const data = JSON.parse(res._getData());
    expect(data.error).toBe('Unauthorized');
  });

  it('should filter metrics by dataSource', async () => {
    vi.mocked(getServerSession).mockResolvedValue({
      user: { id: 'user-1', email: 'test@example.com' },
    } as never);

    const mockMetrics = [
      {
        dataSource: 'bond_issuance',
        metricName: 'weekly',
        value: 12500000000,
        timestamp: '2024-01-15T06:00:00Z',
        confidence: 0.95,
        metadata: {}
      },
      {
        dataSource: 'bdc_discount',
        metricName: 'average_discount',
        value: -0.08,
        timestamp: '2024-01-15T06:00:00Z',
        confidence: 0.92,
        metadata: {}
      }
    ];

    const { stateStoreClient } = await import('@/lib/data/state-store-client');
    vi.mocked(stateStoreClient.getCurrentMetrics).mockResolvedValue(mockMetrics);

    const { req, res } = createMocks({
      method: 'GET',
      query: { dataSource: 'bond_issuance' },
    });

    await currentMetricsHandler(req, res);

    expect(res._getStatusCode()).toBe(200);
    const data = JSON.parse(res._getData());
    expect(data.metrics).toHaveLength(1);
    expect(data.metrics[0].dataSource).toBe('bond_issuance');
  });
});

describe('/api/metrics/historical', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return historical data with aggregation', async () => {
    vi.mocked(getServerSession).mockResolvedValue({
      user: { id: 'user-1', email: 'test@example.com' },
    } as never);

    const mockHistoricalData = [
      {
        timestamp: '2024-01-01T00:00:00Z',
        value: 100,
        confidence: 0.9,
        metadata: {}
      },
      {
        timestamp: '2024-01-02T00:00:00Z',
        value: 110,
        confidence: 0.9,
        metadata: {}
      }
    ];

    const { stateStoreClient } = await import('@/lib/data/state-store-client');
    vi.mocked(stateStoreClient.getHistoricalData).mockResolvedValue(mockHistoricalData);

    const { req, res } = createMocks({
      method: 'GET',
      query: {
        dataSource: 'bond_issuance',
        metricName: 'weekly',
        days: '7'
      },
    });

    await historicalMetricsHandler(req, res);

    expect(res._getStatusCode()).toBe(200);
    const data = JSON.parse(res._getData());
    expect(data.dataSource).toBe('bond_issuance');
    expect(data.metricName).toBe('weekly');
    expect(data.data).toEqual(mockHistoricalData);
    expect(data.aggregation).toHaveProperty('avg');
    expect(data.aggregation).toHaveProperty('trend');
  });

  it('should validate days parameter', async () => {
    vi.mocked(getServerSession).mockResolvedValue({
      user: { id: 'user-1', email: 'test@example.com' },
    } as never);

    const { req, res } = createMocks({
      method: 'GET',
      query: {
        dataSource: 'bond_issuance',
        metricName: 'weekly',
        days: '500' // Invalid: > 365
      },
    });

    await historicalMetricsHandler(req, res);

    expect(res._getStatusCode()).toBe(400);
    const data = JSON.parse(res._getData());
    expect(data.error).toBe('Days must be between 1 and 365');
  });
});
