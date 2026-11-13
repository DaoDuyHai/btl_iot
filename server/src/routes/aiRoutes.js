import express from 'express';
import { searchBooks, recommendBooks, getAiStats, chatWithAgent } from '../controllers/aiController.js';

const router = express.Router();

router.get('/search', searchBooks);
router.get('/recommend', recommendBooks);
router.get('/stats', getAiStats);
router.post('/chat', chatWithAgent);

export default router;
