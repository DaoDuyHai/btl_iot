import * as loanService from '../services/loanService.js';
import { emitToAll } from '../sockets/index.js';

export async function borrow(req, res, next) {
  try {
    const { readerId, bookIds, loanDays } = req.body;
    if (!readerId || !bookIds || !Array.isArray(bookIds) || bookIds.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'readerId và bookIds (danh sách sách) là bắt buộc'
      });
    }

    const result = await loanService.borrowBatch({ readerId, bookIds, loanDays });
    
    emitToAll('loans:changed', { action: 'borrow', result });
    res.status(201).json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function getReturnPreview(req, res, next) {
  try {
    const { bookRfid } = req.body;
    if (!bookRfid) {
      return res.status(400).json({ success: false, message: 'Vui lòng cung cấp bookRfid' });
    }

    const result = await loanService.getReturnPreview(bookRfid);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function returnBatch(req, res, next) {
  try {
    const { bookRfids, readerId } = req.body;
    if (!bookRfids || !Array.isArray(bookRfids) || bookRfids.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'Danh sách bookRfids là bắt buộc'
      });
    }

    const result = await loanService.returnBatch({ bookRfids, readerId });
    emitToAll('loans:changed', { action: 'returnBatch', result });
    res.json({ success: true, data: result });
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

export async function inspect(req, res, next) {
  try {
    const { loanId, result, damageType, damageDescription, damageFine, actor, inspectionNotes } = req.body;
    if (!loanId || !result) {
      return res.status(400).json({ success: false, message: 'loanId và result là bắt buộc' });
    }

    const inspectionResult = await loanService.inspectBook({
      loanId,
      result,
      damageType,
      damageDescription,
      damageFine,
      actor: actor || 'Thủ thư',
      inspectionNotes
    });

    emitToAll('loans:changed', { action: 'inspect', result: inspectionResult });
    res.json({ success: true, data: inspectionResult });
  } catch (err) {
    next(err);
  }
}

export async function manualReturn(req, res, next) {
  try {
    const { loanId, actor, reason } = req.body;
    if (!loanId) {
      return res.status(400).json({ success: false, message: 'Vui lòng cung cấp loanId' });
    }

    const result = await loanService.manualReturn({
      loanId,
      actor: actor || 'Thủ thư',
      reason
    });

    emitToAll('loans:changed', { action: 'manualReturn', result });
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function getPendingInspection(_req, res, next) {
  try {
    const loans = await loanService.getPendingInspectionBooks();
    res.json({ success: true, data: loans });
  } catch (err) {
    next(err);
  }
}

export async function payFine(req, res, next) {
  try {
    const { loanId, actor } = req.body;
    if (!loanId) {
      return res.status(400).json({ success: false, message: 'Vui lòng cung cấp loanId' });
    }
    const result = await loanService.payFine(loanId, actor);
    emitToAll('loans:changed', { action: 'payFine', result });
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function waiveFine(req, res, next) {
  try {
    const { loanId, reason, actor } = req.body;
    if (!loanId) {
      return res.status(400).json({ success: false, message: 'Vui lòng cung cấp loanId' });
    }
    const result = await loanService.waiveFine(loanId, reason, actor);
    emitToAll('loans:changed', { action: 'waiveFine', result });
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function disputeFine(req, res, next) {
  try {
    const { loanId, reason, actor } = req.body;
    if (!loanId) {
      return res.status(400).json({ success: false, message: 'Vui lòng cung cấp loanId' });
    }
    const result = await loanService.disputeFine(loanId, reason, actor);
    emitToAll('loans:changed', { action: 'disputeFine', result });
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
