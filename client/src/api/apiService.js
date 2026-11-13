import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

export const apiService = {
  // Sách
  getBooks: (includeDeleted = false) => api.get(`/books?includeDeleted=${includeDeleted}`).then(r => r.data.data),
  getBookByRfid: (rfid) => api.get(`/books/${rfid}`).then(r => r.data.data),
  createBook: (data) => api.post('/books', data).then(r => r.data.data),
  updateBook: (id, data) => api.put(`/books/${id}`, data).then(r => r.data.data),
  deleteBook: (id) => api.delete(`/books/${id}`).then(r => r.data),

  // Độc giả
  getReaders: () => api.get('/readers').then(r => r.data.data),
  getReaderByRfid: (rfid) => api.get(`/readers/${rfid}`).then(r => r.data.data),
  createReader: (data) => api.post('/readers', data).then(r => r.data.data),
  updateReader: (id, data) => api.put(`/readers/${id}`, data).then(r => r.data.data),

  // Mượn / Trả
  borrowBatch: (readerId, bookIds, loanDays = 14) => 
    api.post('/loans/borrow', { readerId, bookIds, loanDays }).then(r => r.data.data),
  getReturnPreview: (bookRfid) =>
    api.post('/loans/return-preview', { bookRfid }).then(r => r.data.data),
  returnBatch: (bookRfids, readerId = null) =>
    api.post('/loans/return-batch', { bookRfids, readerId }).then(r => r.data.data),
  returnBook: (bookRfid) => 
    api.post('/loans/return', { bookRfid }).then(r => r.data.data),
  payFine: (loanId, actor = 'Hệ thống') =>
    api.post('/loans/pay-fine', { loanId, actor }).then(r => r.data.data),
  waiveFine: (loanId, reason = 'Miễn phạt theo quy chế', actor = 'Thủ thư') =>
    api.post('/loans/waive-fine', { loanId, reason, actor }).then(r => r.data.data),
  disputeFine: (loanId, reason = 'Độc giả khiếu nại', actor = 'Độc giả') =>
    api.post('/loans/dispute-fine', { loanId, reason, actor }).then(r => r.data.data),
  finishReturn: (readerId, items) =>
    api.post('/loans/finish-return', { readerId, items }).then(r => r.data.data),
  renewLoans: (loanIds, extraDays = 14) =>
    api.post('/loans/renew', { loanIds, extraDays }).then(r => r.data.data),
  getLoanHistory: (limit = 50) => 
    api.get(`/loans/history?limit=${limit}`).then(r => r.data.data),
  getPendingInspection: () =>
    api.get('/loans/pending-inspection').then(r => r.data.data),
  inspectBook: (data) =>
    api.post('/loans/inspect', data).then(r => r.data.data),
  manualReturn: (data) =>
    api.post('/loans/manual-return', data).then(r => r.data.data),

  // Nhật ký kiểm toán & Thiết bị
  getAudits: (limit = 50) =>
    api.get(`/audits?limit=${limit}`).then(r => r.data.data),
  getDeviceLogs: (limit = 30) => 
    api.get(`/devices/logs?limit=${limit}`).then(r => r.data.data),
  sendDeviceCommand: (deviceId, action, status) => 
    api.post(`/devices/${deviceId}/command`, { action, status }).then(r => r.data),

  // AI Tìm kiếm & Gợi ý sách thông minh
  searchAiBooks: (q, top_k = 6) => 
    api.get('/ai/search', { params: { q, top_k } }).then(r => r.data),
  recommendAiBooks: (params = {}) => 
    api.get('/ai/recommend', { params }).then(r => r.data),
  getAiStats: () => 
    api.get('/ai/stats').then(r => r.data),
  chatWithAiLibrarian: (payload) =>
    api.post('/ai/chat', payload).then(r => r.data),
};
