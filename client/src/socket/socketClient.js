import { io } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:5000';

export const socket = io(SOCKET_URL, {
  autoConnect: true,
  reconnection: true,
  reconnectionDelay: 2000
});

socket.on('connect', () => {
  console.log('⚡ [Socket.IO] Đã kết nối thời gian thực tới Backend!');
});

socket.on('disconnect', () => {
  console.warn('⚡ [Socket.IO] Mất kết nối tới Backend, đang tự động kết nối lại...');
});

