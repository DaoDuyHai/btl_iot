import express from 'express';
import { searchBooks, recommendBooks, getAiStats } from '../controllers/aiController.js';

const router = express.Router();

router.get('/search', searchBooks);
router.get('/recommend', recommendBooks);
router.get('/stats', getAiStats);

export default router;
