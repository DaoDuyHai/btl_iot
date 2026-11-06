import { Router } from 'express';
import AuditLog from '../models/AuditLog.js';

const router = Router();

router.get('/', async (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit, 10) || 50;
    const logs = await AuditLog.find().sort({ timestamp: -1 }).limit(limit);
    res.json({ success: true, data: logs });
  } catch (err) {
    next(err);
  }
});

export default router;
