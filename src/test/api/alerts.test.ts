import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createMocks } from 'node-mocks-http';
import { getServerSession } from 'next-auth';
import alertConfigHandler from '@/pages/api/alerts/config';

// Mock next-auth
vi.mock('next-auth', () => ({
  getServerSession: vi.fn(),
}));

// Mock database - use factory function to avoid hoisting issues
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

describe('/api/alerts/config', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should create new alert configuration', async () => {
    vi.mocked(getServerSession).mockResolvedValue({
      user: { id: 'user-1', email: 'test@example.com' },
    } as never);

    const { db } = await import('@/lib/db/connection');
    const mockDb = db as unknown as Record<string, ReturnType<typeof vi.fn>>;
    
    // Reset chainable behavior
    Object.keys(mockDb).forEach(key => {
      mockDb[key].mockReturnValue(mockDb);
    });

    // Mock no existing config
    mockDb.limit.mockResolvedValueOnce([]);
    
    // Mock successful insert
    mockDb.values.mockResolvedValueOnce(undefined);
    
    // Mock return of new config
    mockDb.limit.mockResolvedValueOnce([{
      id: 'config-1',
      userId: 'user-1',
      dataSource: 'bond_issuance',
      metricName: 'weekly',
      thresholdType: 'absolute',
      thresholdValue: 5000000000,
      comparisonPeriod: 7,
      enabled: true,
      notificationChannels: ['email']
    }]);

    const { req, res } = createMocks({
      method: 'POST',
      body: {
        dataSource: 'bond_issuance',
        metricName: 'weekly',
        thresholdType: 'absolute',
        thresholdValue: 5000000000,
        comparisonPeriod: 7,
        enabled: true,
        notificationChannels: ['email']
      },
    });

    await alertConfigHandler(req, res);

    expect(res._getStatusCode()).toBe(201);
    const data = JSON.parse(res._getData());
    expect(data.config.dataSource).toBe('bond_issuance');
  });

  it('should return 401 for unauthenticated user', async () => {
    vi.mocked(getServerSession).mockResolvedValue(null);

    const { req, res } = createMocks({
      method: 'GET',
    });

    await alertConfigHandler(req, res);

    expect(res._getStatusCode()).toBe(401);
    const data = JSON.parse(res._getData());
    expect(data.error).toBe('Unauthorized');
  });

  it('should validate alert configuration data', async () => {
    vi.mocked(getServerSession).mockResolvedValue({
      user: { id: 'user-1', email: 'test@example.com' },
    } as never);

    const { req, res } = createMocks({
      method: 'POST',
      body: {
        dataSource: 'bond_issuance',
        // Missing required fields
      },
    });

    await alertConfigHandler(req, res);

    expect(res._getStatusCode()).toBe(500); // Zod validation error
  });

  it('should get user alert configurations', async () => {
    vi.mocked(getServerSession).mockResolvedValue({
      user: { id: 'user-1', email: 'test@example.com' },
    } as never);

    const mockConfigs = [
      {
        id: 'config-1',
        userId: 'user-1',
        dataSource: 'bond_issuance',
        metricName: 'weekly',
        thresholdType: 'absolute',
        thresholdValue: 5000000000,
        comparisonPeriod: 7,
        enabled: true,
        notificationChannels: ['email']
      }
    ];

    const { db } = await import('@/lib/db/connection');
    const mockDb = db as unknown as Record<string, ReturnType<typeof vi.fn>>;
    
    // Reset chainable behavior
    Object.keys(mockDb).forEach(key => {
      mockDb[key].mockReturnValue(mockDb);
    });

    mockDb.where.mockResolvedValueOnce(mockConfigs);

    const { req, res } = createMocks({
      method: 'GET',
    });

    await alertConfigHandler(req, res);

    expect(res._getStatusCode()).toBe(200);
    const data = JSON.parse(res._getData());
    expect(data.configs).toEqual(mockConfigs);
  });
});
