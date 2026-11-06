import { Router } from 'express';
import * as loanController from '../controllers/loanController.js';

const router = Router();

router.post('/borrow', loanController.borrow);
router.post('/return-preview', loanController.getReturnPreview);
router.post('/return-batch', loanController.returnBatch);
router.post('/return', loanController.returnBook);
router.post('/renew', loanController.renew);
router.post('/pay-fine', loanController.payFine);
router.post('/waive-fine', loanController.waiveFine);
router.post('/dispute-fine', loanController.disputeFine);
router.get('/pending-inspection', loanController.getPendingInspection);
router.post('/inspect', loanController.inspect);
router.post('/manual-return', loanController.manualReturn);
router.post('/finish-return', loanController.finishReturn);
router.get('/history', loanController.getHistory);

export default router;
