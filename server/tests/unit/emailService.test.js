import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockSendMail = vi.fn().mockResolvedValue({ messageId: 'mock-msg-123' });

vi.mock('nodemailer', () => ({
  default: {
    createTransport: vi.fn(() => ({
      sendMail: mockSendMail
    }))
  }
}));

import { sendReceiptEmail } from '../../src/services/emailService.js';

describe('Unit Test: Email Service (Receipts & Notifications)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSendMail.mockResolvedValue({ messageId: 'mock-msg-123' });
  });

  it('phải bỏ qua gửi email khi bạn đọc không có email hoặc reader null', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    await sendReceiptEmail({ reader: null, items: [], actionType: 'BORROW' });
    expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('Bạn đọc không có email'));

    await sendReceiptEmail({ reader: { name: 'Nguyễn Văn A' }, items: [], actionType: 'BORROW' });
    expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('Bạn đọc không có email'));

    expect(mockSendMail).not.toHaveBeenCalled();
    warnSpy.mockRestore();
  });

  it('phải gửi thành công biên lai mượn tài liệu (BORROW) tới email bạn đọc', async () => {
    const mockReader = {
      name: 'Nguyễn Văn A',
      studentId: 'B21DCCN001',
      email: 'vana@ptit.edu.vn',
      department: 'Khoa Công nghệ thông tin'
    };

    const mockItems = [
      {
        title: 'Lập trình Python Nâng cao',
        author: 'Guido van Rossum',
        dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000)
      }
    ];

    await sendReceiptEmail({
      reader: mockReader,
      items: mockItems,
      actionType: 'BORROW'
    });

    expect(mockSendMail).toHaveBeenCalledTimes(1);
    const mailOptions = mockSendMail.mock.calls[0][0];
    expect(mailOptions.to).toBe('vana@ptit.edu.vn');
    expect(mailOptions.subject).toContain('Biên lai MƯỢN TÀI LIỆU');
    expect(mailOptions.html).toContain('Lập trình Python Nâng cao');
    expect(mailOptions.html).toContain('B21DCCN001');
  });

  it('phải gửi thành công biên lai trả tài liệu (RETURN) với trạng thái hoàn trả', async () => {
    const mockReader = {
      name: 'Trần Thị B',
      studentId: 'B21DCCN002',
      email: 'thib@ptit.edu.vn',
      department: 'Khoa Viễn thông'
    };

    const mockItems = [
      {
        title: 'Mạng máy tính & Truyền thông',
        author: 'Andrew S. Tanenbaum',
        statusText: 'Đã hoàn trả nguyên vẹn'
      }
    ];

    await sendReceiptEmail({
      reader: mockReader,
      items: mockItems,
      actionType: 'RETURN'
    });

    expect(mockSendMail).toHaveBeenCalledTimes(1);
    const mailOptions = mockSendMail.mock.calls[0][0];
    expect(mailOptions.to).toBe('thib@ptit.edu.vn');
    expect(mailOptions.subject).toContain('Biên lai TRẢ TÀI LIỆU');
    expect(mailOptions.html).toContain('Mạng máy tính & Truyền thông');
    expect(mailOptions.html).toContain('Đã hoàn trả nguyên vẹn');
  });
});
