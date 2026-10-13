import { Router } from 'express';
import * as bookController from '../controllers/bookController.js';

const router = Router();

router.get('/', bookController.getAllBooks);
router.get('/by-rfid/:rfid', bookController.getBookByRfid);
router.post('/', bookController.createBook);
router.delete('/:id', bookController.deleteBook);

export default router;

