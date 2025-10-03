import { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import bcrypt from 'bcryptjs';
import { db } from '@/lib/db/connection';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

export const authOptions: NextAuthOptions = {
  // Only enable debug locally; default false in production
  debug: process.env.NODE_ENV !== 'production',
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials) {
        console.log('🔐 NextAuth authorize called with:', { email: credentials?.email, hasPassword: !!credentials?.password });
        
        if (!credentials?.email || !credentials?.password) {
          console.log('❌ Missing credentials');
          return null;
        }

        try {
          const emailInput = credentials.email;
          const normalizedEmail = emailInput.toLowerCase();
          console.log('🔍 Querying database for user (exact):', emailInput);
          let user = await db
            .select()
            .from(users)
            .where(eq(users.email, emailInput))
            .limit(1);

          if (!user.length) {
            console.log('🔍 Exact match not found, trying lowercase:', normalizedEmail);
            user = await db
              .select()
              .from(users)
              .where(eq(users.email, normalizedEmail))
              .limit(1);
          }

          console.log('📋 Database query result:', user.length > 0 ? 'User found' : 'User not found');
          
          if (!user.length) {
            console.log('❌ No user found with email:', credentials.email);
            return null;
          }

          console.log('🔐 Comparing password for user:', user[0].email);
          const isPasswordValid = await bcrypt.compare(
            credentials.password,
            user[0].passwordHash
          );

          console.log('🔐 Password validation result:', isPasswordValid ? 'VALID' : 'INVALID');

          if (!isPasswordValid) {
            console.log('❌ Invalid password for user:', credentials.email);
            return null;
          }

          const result = {
            id: user[0].id.toString(),
            email: user[0].email,
            name: user[0].name,
          };
          
          console.log('✅ Authentication successful, returning user:', result);
          return result;
        } catch (error) {
          console.error('❌ Auth error:', error);
          return null;
        }
      }
    })
  ],
  session: {
    strategy: 'jwt',
  },
  jwt: {
    secret: process.env.NEXTAUTH_SECRET || 'development-secret-key',
  },

  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (token) {
        session.user.id = token.id as string;
      }
      return session;
    },
  },
};

declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      email: string;
      name?: string;
    };
  }
}