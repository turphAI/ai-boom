import { beforeAll, afterAll, afterEach } from 'vitest';

// Mock environment variables
beforeAll(() => {
  process.env.NEXTAUTH_SECRET = 'test-secret';
  process.env.DATABASE_HOST = 'test-host';
  process.env.DATABASE_USERNAME = 'test-user';
  process.env.DATABASE_PASSWORD = 'test-password';
});

// Clean up after each test
afterEach(() => {
  // Reset any global state if needed
});

afterAll(() => {
  // Clean up resources
});