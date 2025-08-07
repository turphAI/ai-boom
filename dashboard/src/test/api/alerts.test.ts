import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createMocks } from 'node-mocks-http';
import { getServerSession } from 'next-auth';
import alertConfigHandler from '@/pages/api/alerts/config';

// Mock next-auth
vi.mock('next-auth', () => ({
  getServerSession: vi.fn(),
}));

// Mock database
vi.mock('@/lib/db/connection', () => ({
  db: {
    select: vi.fn().mockReturnThis(),
    from: vi.fn().mockReturnThis(),
    where: vi.fn().mockReturnThis(),
    limit: vi.fn(),
    insert: vi.fn().mockReturnThis(),
    values: vi.fn(),
    update: vi.fn().mockReturnThis(),
    set: vi.fn().mockReturnThis(),
    delete: vi.fn().mockReturnThis(),
  },
}));

describe('/api/alerts/config', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should create new alert configuration', async () => {
    vi.mocked(getServerSession).mockResolvedValue({
      user: { id: 'user-1', email: 'test@example.com' },
    } as any);

    const { db } = await import('@/lib/db/connection');
    
    // Mock no existing config
    vi.mocked(db.limit).mockResolvedValueOnce([]);
    
    // Mock successful insert
    vi.mocked(db.values).mockResolvedValueOnce(undefined);
    
    // Mock return of new config
    vi.mocked(db.limit).mockResolvedValueOnce([{
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
    } as any);

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
    } as any);

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
    vi.mocked(db.where).mockResolvedValue(mockConfigs);

    const { req, res } = createMocks({
      method: 'GET',
    });

    await alertConfigHandler(req, res);

    expect(res._getStatusCode()).toBe(200);
    const data = JSON.parse(res._getData());
    expect(data.configs).toEqual(mockConfigs);
  });
});