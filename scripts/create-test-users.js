const bcrypt = require('bcryptjs');

// This script can be run locally to create test users in PlanetScale
// Make sure DATABASE_URL is set to your PlanetScale connection string

async function createTestUsers() {
  try {
    // Import the database connection
    const { db } = require('../src/lib/db/connection');
    const { users } = require('../src/lib/db/schema');

    // Test user data
    const testUsers = [
      {
        email: 'demo@example.com',
        password: 'demo123',
        name: 'Demo User'
      },
      {
        email: 'admin@example.com',
        password: 'admin123',
        name: 'Admin User'
      }
    ];

    for (const userData of testUsers) {
      // Hash the password
      const passwordHash = await bcrypt.hash(userData.password, 12);

      // Insert user
      await db.insert(users).values({
        email: userData.email,
        passwordHash,
        name: userData.name,
        role: userData.email === 'admin@example.com' ? 'admin' : 'user'
      });

      console.log(`✅ Created user: ${userData.email}`);
    }

    console.log('🎉 All test users created successfully!');
  } catch (error) {
    console.error('❌ Error creating test users:', error);
  }
}

// Run the script
createTestUsers();
