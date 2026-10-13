import { Server } from 'socket.io';
import { ENV } from '../config/env.js';

let ioInstance = null;

export function initSocketIO(httpServer) {
  ioInstance = new Server(httpServer, {
    cors: {
      origin: '*',
      methods: ['GET', 'POST']
    }
  });

  ioInstance.on('connection', (socket) => {
    console.log(`🔌 [Socket.IO] Client kết nối: ${socket.id}`);

    socket.on('disconnect', () => {
      console.log(`🔌 [Socket.IO] Client ngắt kết nối: ${socket.id}`);
    });
  });

  return ioInstance;
}

export function getIO() {
  return ioInstance;
}

export function emitToAll(event, payload) {
  if (ioInstance) {
    ioInstance.emit(event, payload);
  }
}

