import { Router } from 'express';
import * as readerController from '../controllers/readerController.js';

const router = Router();

router.get('/', readerController.getAllReaders);
router.get('/by-rfid/:rfid', readerController.getReaderByRfid);
router.post('/', readerController.createReader);

export default router;

