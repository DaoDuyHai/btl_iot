import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

export const apiService = {
  // Sách
  getBooks: () => api.get('/books').then(r => r.data.data),
  getBookByRfid: (rfid) => api.get(`/books/by-rfid/${rfid}`).then(r => r.data.data),
  createBook: (data) => api.post('/books', data).then(r => r.data.data),
  deleteBook: (id) => api.delete(`/books/${id}`).then(r => r.data),

  // Độc giả
  getReaders: () => api.get('/readers').then(r => r.data.data),
  getReaderByRfid: (rfid) => api.get(`/readers/by-rfid/${rfid}`).then(r => r.data.data),
  createReader: (data) => api.post('/readers', data).then(r => r.data.data),

  // Mượn / Trả
  borrowBatch: (readerId, bookIds, loanDays = 14) => 
    api.post('/loans/borrow', { readerId, bookIds, loanDays }).then(r => r.data.data),
  returnBook: (bookRfid) => 
    api.post('/loans/return', { bookRfid }).then(r => r.data.data),
  payFine: (loanId) =>
    api.post('/loans/pay-fine', { loanId }).then(r => r.data.data),
  finishReturn: (readerId, items) =>
    api.post('/loans/finish-return', { readerId, items }).then(r => r.data.data),
  renewLoans: (loanIds, extraDays = 14) =>
    api.post('/loans/renew', { loanIds, extraDays }).then(r => r.data.data),
  getLoanHistory: (limit = 50) => 
    api.get(`/loans/history?limit=${limit}`).then(r => r.data.data),

  // Thiết bị Kiosk
  getDeviceLogs: (limit = 30) => 
    api.get(`/devices/logs?limit=${limit}`).then(r => r.data.data),
  sendDeviceCommand: (deviceId, action, status) => 
    api.post(`/devices/${deviceId}/command`, { action, status }).then(r => r.data),
};

