import pg from 'pg';
const { Client } = pg;

// Use the exact same URL from your config
const connectionString = process.env.DATABASE_URL || 'postgresql://temporal:temporal@172.31.11.185:5434/temporal';

const client = new Client({ connectionString });

async function testConnection() {
  try {
    console.log('Attempting to connect to the database...');
    await client.connect();
    console.log('✅ Connection successful!');
    const res = await client.query('SELECT NOW()');
    console.log('Query successful. Current time from DB:', res.rows[0].now);
  } catch (err) {
    console.error('❌ Connection failed!');
    console.error(err);
  } finally {
    await client.end();
    console.log('Client has disconnected.');
  }
}

testConnection();