import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import http from 'http';
import { io as ClientIO } from 'socket.io-client';
import { initSocketIO, emitToAll } from '../../src/sockets/index.js';

describe('Integration Test: Realtime WebSocket với Socket.IO & socket.io-client', () => {
  let httpServer;
  let clientSocket;
  let serverPort;

  beforeAll(async () => {
    // Khởi tạo một HTTP server tạm thời trên cổng động ngẫu nhiên (Port 0)
    httpServer = http.createServer();
    initSocketIO(httpServer);

    await new Promise((resolve) => {
      httpServer.listen(0, () => {
        serverPort = httpServer.address().port;
        resolve();
      });
    });

    // Client kết nối tới WebSocket server
    clientSocket = ClientIO(`http://localhost:${serverPort}`, {
      transports: ['websocket'],
      forceNew: true
    });

    await new Promise((resolve) => {
      clientSocket.on('connect', resolve);
    });
  });

  afterAll(() => {
    if (clientSocket && clientSocket.connected) {
      clientSocket.disconnect();
    }
    if (httpServer) {
      httpServer.close();
    }
  });

  it('client phải thiết lập kết nối WebSocket thành công và nhận Socket ID', () => {
    expect(clientSocket.connected).toBe(true);
    expect(clientSocket.id).toBeDefined();
  });

  it('client phải nhận được sự kiện kiosk:event phát từ server thời gian thực', async () => {
    const mockPayload = {
      type: 'READER_AUTHENTICATED',
      data: {
        studentId: 'B21DCCN001',
        name: 'Đào Duy Hải',
        active: true
      }
    };

    const receivedPromise = new Promise((resolve) => {
      clientSocket.on('kiosk:event', (eventData) => {
        resolve(eventData);
      });
    });

    // Server phát bản tin tới toàn bộ observer clients
    emitToAll('kiosk:event', mockPayload);

    const receivedData = await receivedPromise;
    expect(receivedData).toEqual(mockPayload);
    expect(receivedData.type).toBe('READER_AUTHENTICATED');
    expect(receivedData.data.name).toBe('Đào Duy Hải');
  });
});

