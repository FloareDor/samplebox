import { saveEmail } from '../../lib/db';
import { RateLimiterMemory } from 'rate-limiter-flexible';

// Set up the rate limiter
const rateLimiter = new RateLimiterMemory({
  points: 9, // Number of points
  duration: 60, // Per 60 seconds
});

export default async function handler(req, res) {
  if (req.method === 'POST') {
    try {
      // Getting that IP address
      const forwardedFor = req.headers['x-forwarded-for'];
      const ip = forwardedFor ? forwardedFor.split(',')[0] : req.socket.remoteAddress;

      // Check rate limit
      try {
        await rateLimiter.consume(ip);
      } catch (rateLimitError) {
        return res.status(429).json({ message: 'Too many requests, please try again later.' });
      }

      const { email } = req.body;
      
      if (!email || typeof email !== 'string') {
        return res.status(400).json({ message: 'Invalid email provided' });
      }

      const location = null;

      await saveEmail(email, location);
      res.status(201).json({ message: 'Email saved successfully!' });
    } catch (error) {
      console.error('Error saving email:', error);
      res.status(500).json({ message: 'Something went wrong!' + error });
    }
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}