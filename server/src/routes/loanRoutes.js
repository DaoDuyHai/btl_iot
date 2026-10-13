import { Router } from 'express';
import * as loanController from '../controllers/loanController.js';

const router = Router();

router.post('/borrow', loanController.borrow);
router.post('/return', loanController.returnBook);
router.post('/renew', loanController.renew);
router.post('/pay-fine', loanController.payFine);
router.post('/finish-return', loanController.finishReturn);
router.get('/history', loanController.getHistory);

export default router;

