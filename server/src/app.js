import express from 'express';
import cors from 'cors';
import readerRoutes from './routes/readerRoutes.js';
import bookRoutes from './routes/bookRoutes.js';
import loanRoutes from './routes/loanRoutes.js';
import deviceRoutes from './routes/deviceRoutes.js';
import { errorHandler } from './middlewares/errorHandler.js';

const app = express();

app.use(cors());
app.use(express.json());

// API Health Check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'Smart Library Kiosk Server', timestamp: new Date() });
});

// Gắn các module routes
app.use('/api/readers', readerRoutes);
app.use('/api/books', bookRoutes);
app.use('/api/loans', loanRoutes);
app.use('/api/devices', deviceRoutes);

// Bắt lỗi tập trung
app.use(errorHandler);

export default app;

