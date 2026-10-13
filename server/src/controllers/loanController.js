import * as loanService from '../services/loanService.js';
import { emitToAll } from '../sockets/index.js';

export async function borrow(req, res, next) {
  try {
    const { readerId, bookIds, loanDays } = req.body;
    const result = await loanService.borrowBatch({ readerId, bookIds, loanDays });
    
    emitToAll('loans:changed', { action: 'borrow', result });
    res.status(201).json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function returnBook(req, res, next) {
  try {
    const { bookRfid } = req.body;
    if (!bookRfid) {
      return res.status(400).json({ success: false, message: 'Vui lòng cung cấp bookRfid' });
    }

    const result = await loanService.returnBookByRfid(bookRfid);
    emitToAll('loans:changed', { action: 'return', result });
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function renew(req, res, next) {
  try {
    const { loanIds, extraDays } = req.body;
    const result = await loanService.renewLoans({ loanIds, extraDays });
    emitToAll('loans:changed', { action: 'renew', result });
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function payFine(req, res, next) {
  try {
    const { loanId } = req.body;
    if (!loanId) {
      return res.status(400).json({ success: false, message: 'Vui lòng cung cấp loanId' });
    }
    const result = await loanService.payFine(loanId);
    emitToAll('loans:changed', { action: 'payFine', result });
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function finishReturn(req, res, next) {
  try {
    const { readerId, items } = req.body;
    const result = await loanService.sendReturnBatchReceipt({ readerId, items });
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function getHistory(req, res, next) {
  try {
    const limit = parseInt(req.query.limit, 10) || 50;
    const loans = await loanService.getLoanHistory(limit);
    res.json({ success: true, data: loans });
  } catch (err) {
    next(err);
  }
}

