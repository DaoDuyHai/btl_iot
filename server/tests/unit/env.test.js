import { describe, it, expect } from 'vitest';
import { envSchema, validateEnv } from '../../src/config/env.js';

describe('Unit Test: Environment Validation với Zod', () => {
  it('phải validate thành công khi cấu hình đầy đủ biến môi trường hợp lệ', () => {
    const mockEnv = {
      PORT: '5000',
      MONGODB_URI: 'mongodb://localhost:27017/test_kiosk',
      MQTT_BROKER_URL: 'mqtt://localhost:1883',
      KIOSK_DEVICE_ID: 'kiosk_01',
      CLIENT_URL: 'http://localhost:5173',
      FINE_PER_DAY_VND: '5000',
      BANK_BIN: '970422',
      BANK_ACCOUNT: '000124135246'
    };

    const validated = validateEnv(mockEnv);
    expect(validated.PORT).toBe(5000);
    expect(validated.MONGODB_URI).toBe('mongodb://localhost:27017/test_kiosk');
    expect(validated.FINE_PER_DAY_VND).toBe(5000);
    expect(validated.KIOSK_DEVICE_ID).toBe('kiosk_01');
  });

  it('phải ném lỗi khi MONGODB_URI bị rỗng', () => {
    const invalidEnv = {
      MONGODB_URI: ''
    };

    const parseResult = envSchema.safeParse(invalidEnv);
    expect(parseResult.success).toBe(false);
    if (!parseResult.success) {
      const issue = parseResult.error.issues.find((i) => i.path.includes('MONGODB_URI'));
      expect(issue).toBeDefined();
    }
  });

  it('phải gán giá trị mặc định cho các biến tùy chọn khi không khai báo', () => {
    const minimalEnv = {
      MONGODB_URI: 'mongodb://atlas-cloud:27017/kiosk'
    };

    const validated = envSchema.parse(minimalEnv);
    expect(validated.PORT).toBe(5000);
    expect(validated.MQTT_BROKER_URL).toBe('mqtt://localhost:1883');
    expect(validated.KIOSK_DEVICE_ID).toBe('kiosk_01');
    expect(validated.FINE_PER_DAY_VND).toBe(5000);
  });
});

