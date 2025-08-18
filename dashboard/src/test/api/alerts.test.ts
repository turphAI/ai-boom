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
    select: vi.fn(() => ({
      from: vi.fn(() => ({
        where: vi.fn(() => ({
          limit: vi.fn(() => Promise.resolve([])),
        })),
      })),
    })),
    insert: vi.fn(() => ({
      values: vi.fn(() => Promise.resolve({ insertId: 'config-1' })),
    })),
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
    
    // Mock the query chain for select
    const mockSelectChain = {
      from: vi.fn(() => ({
        where: vi.fn(() => ({
          limit: vi.fn(() => Promise.resolve([])),
        })),
      })),
    };
    vi.mocked(db.select).mockReturnValue(mockSelectChain);
    
    // Mock the query chain for insert
    const mockInsertChain = {
      values: vi.fn(() => Promise.resolve({ insertId: 'config-1' })),
    };
    vi.mocked(db.insert).mockReturnValue(mockInsertChain);

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
    
    // Mock the query chain for select with where
    const mockSelectChain = {
      from: vi.fn(() => ({
        where: vi.fn(() => Promise.resolve(mockConfigs)),
      })),
    };
    vi.mocked(db.select).mockReturnValue(mockSelectChain);

    const { req, res } = createMocks({
      method: 'GET',
    });

    await alertConfigHandler(req, res);

    expect(res._getStatusCode()).toBe(200);
    const data = JSON.parse(res._getData());
    expect(data.configs).toEqual(mockConfigs);
  });
});