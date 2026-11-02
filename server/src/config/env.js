import dotenv from 'dotenv';
import { z } from 'zod';

dotenv.config();

export const envSchema = z.object({
  PORT: z.coerce.number().int().positive().default(5000),
  MONGODB_URI: z.string().min(1, 'MONGODB_URI không được để trống'),
  MQTT_BROKER_URL: z.string().min(1, 'MQTT_BROKER_URL không được để trống').default('mqtt://localhost:1883'),
  KIOSK_DEVICE_ID: z.string().default('kiosk_01'),
  CLIENT_URL: z.string().default('http://localhost:5173'),
  FINE_PER_DAY_VND: z.coerce.number().nonnegative().default(5000),
  BANK_BIN: z.string().default('970422'),
  BANK_ACCOUNT: z.string().default('000124135246'),
  EMAIL_USER: z.string().optional().default(''),
  EMAIL_PASS: z.string().optional().default('')
});

export function validateEnv(rawEnv = process.env) {
  const result = envSchema.safeParse(rawEnv);

  if (!result.success) {
    console.error('═══════════════════════════════════════════════════════════════');
    console.error('❌ [FATAL CONFIG ERROR] BIẾN MÔI TRƯỜNG (.ENV) KHÔNG HỢP LỆ:');
    console.error('═══════════════════════════════════════════════════════════════');
    result.error.issues.forEach((issue) => {
      console.error(` 🔴 [${issue.path.join('.')}] - ${issue.message}`);
    });
    console.error('───────────────────────────────────────────────────────────────');
    console.error('⚠️  Hệ thống dừng khởi động để bảo đảm tính an toàn dữ liệu.');
    console.error('═══════════════════════════════════════════════════════════════');
    if (process.env.NODE_ENV !== 'test') {
      process.exit(1);
    }
    throw new Error('Invalid environment configuration');
  }

  return result.data;
}

export const ENV = validateEnv();
