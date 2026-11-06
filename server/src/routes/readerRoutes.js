import { Router } from 'express';
import * as readerController from '../controllers/readerController.js';

const router = Router();

router.get('/', readerController.getAllReaders);
router.get('/:rfid', readerController.getReaderByRfid);
router.post('/', readerController.createReader);
router.put('/:id', readerController.updateReader);

export default router;
