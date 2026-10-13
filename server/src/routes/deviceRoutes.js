import { Router } from 'express';
import * as deviceController from '../controllers/deviceController.js';

const router = Router();

router.get('/logs', deviceController.getLogs);
router.post('/:deviceId/command', deviceController.sendCommand);

export default router;

