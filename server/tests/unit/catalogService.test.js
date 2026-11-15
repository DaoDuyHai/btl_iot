import { describe, it, expect } from 'vitest';
import { catalogService } from '../../src/services/catalogService.js';

describe('Unit Test: In-Memory Precision Catalog Service', () => {
  it('phải nạp thành công kho sách vào bộ nhớ RAM', () => {
    expect(catalogService.books).toBeDefined();
    expect(catalogService.books.length).toBeGreaterThan(0);
  });

  it('phải nhận diện chính xác Intent ngữ nghĩa theo từ khóa trigger', () => {
    const jpIntent = catalogService.getMatchedIntent('học tiếng nhật');
    expect(jpIntent).toBeDefined();
    expect(jpIntent.intent).toBe('JAPANESE_LANG');

    const enIntent = catalogService.getMatchedIntent('luyện thi ielts cấp tốc');
    expect(enIntent).toBeDefined();
    expect(enIntent.intent).toBe('ENGLISH_LANG');

    const itIntent = catalogService.getMatchedIntent('lập trình python');
    expect(itIntent).toBeDefined();
    expect(itIntent.intent).toBe('IT_PROGRAMMING');
  });

  it('phải tìm kiếm chính xác sách theo từ khóa và sắp xếp theo độ phù hợp', () => {
    const results = catalogService.searchPrecision('tiếng anh', 5);
    expect(results).toBeDefined();
    expect(results.length).toBeGreaterThan(0);
    expect(results.length).toBeLessThanOrEqual(5);

    // Không được trả về sách ngôn ngữ khác như tiếng Trung / tiếng Hàn
    const hasWrongLang = results.some(
      b => (b.title || '').toLowerCase().includes('tiếng trung') || (b.title || '').toLowerCase().includes('hán ngữ')
    );
    expect(hasWrongLang).toBe(false);
  });

  it('phải khử dấu tiếng Việt và hỗ trợ tìm kiếm không dấu', () => {
    const results = catalogService.searchPrecision('lap trinh', 3);
    expect(results).toBeDefined();
    expect(results.length).toBeGreaterThan(0);
  });
});
