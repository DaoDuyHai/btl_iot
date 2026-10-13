import nodemailer from 'nodemailer';
import dotenv from 'dotenv';
dotenv.config();

let transporter = null;

function getTransporter() {
  if (transporter) return transporter;

  const emailUser = process.env.EMAIL_USER;
  const emailPass = process.env.EMAIL_PASS;

  if (emailUser && emailPass) {
    // Cấu hình gửi thật qua Gmail SMTP
    transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: emailUser,
        pass: emailPass
      }
    });
    console.log(`📧 [Email Service] Đã cấu hình gửi Gmail thật từ: ${emailUser}`);
  } else {
    // Chế độ mô phỏng khi chưa nhập tài khoản Gmail
    transporter = {
      sendMail: async (options) => {
        console.log('\n=============================================================');
        console.log(`📧 [MOCK EMAIL] ĐÃ GỬI BIÊN LAI ĐIỆN TỬ TỚI: ${options.to}`);
        console.log(`Tiêu đề: ${options.subject}`);
        console.log('Nội dung tóm tắt: Biên lai thư viện PTIT tự phục vụ');
        console.log('=============================================================\n');
        return { messageId: 'mock-email-' + Date.now() };
      }
    };
    console.log('📧 [Email Service] Chạy chế độ Mock Email (chưa có EMAIL_USER trong .env)');
  }

  return transporter;
}

/**
 * Gửi email biên lai mượn / trả / gia hạn sách
 */
export async function sendReceiptEmail({ reader, items, actionType }) {
  if (!reader || !reader.email) {
    console.warn('⚠️ [Email] Bạn đọc không có email, bỏ qua gửi biên lai');
    return;
  }

  const actionName = actionType === 'BORROW' 
    ? 'MƯỢN TÀI LIỆU' 
    : actionType === 'RETURN' 
    ? 'TRẢ TÀI LIỆU' 
    : 'GIA HẠN TÀI LIỆU';

  const dateStr = new Date().toLocaleString('vi-VN');
  const isReturn = actionType === 'RETURN';
  const col3Header = isReturn ? 'Trạng thái hoàn trả' : 'Hạn trả';

  // Tạo bảng danh sách sách HTML
  const itemsHtml = items.map((it, idx) => {
    const bookTitle = it.title || it.bookId?.title || 'Tài liệu thư viện';
    const author = it.author || it.bookId?.author || 'N/A';
    const col3Value = isReturn
      ? (it.statusText || 'Đã hoàn trả')
      : (it.dueDate ? new Date(it.dueDate).toLocaleDateString('vi-VN') : '14 ngày');

    return `
      <tr style="border-bottom: 1px solid #e2e8f0;">
        <td style="padding: 10px; text-align: center; color: #b91c1c; font-weight: bold;">${idx + 1}</td>
        <td style="padding: 10px;">
          <strong>${bookTitle}</strong><br/>
          <small style="color: #64748b;">Tác giả: ${author}</small>
        </td>
        <td style="padding: 10px; text-align: right; font-weight: 600; color: ${isReturn ? '#15803d' : '#1e293b'};">${col3Value}</td>
      </tr>
    `;
  }).join('');

  const htmlContent = `
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; background: #ffffff;">
      <div style="background: linear-gradient(135deg, #991b1b 0%, #dc2626 100%); color: #ffffff; padding: 22px; text-align: center;">
        <h2 style="margin: 0; font-size: 18px; text-transform: uppercase; letter-spacing: 0.5px;">
          HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG
        </h2>
        <p style="margin: 4px 0 0; font-size: 13px; color: #fef08a;">
          TRUNG TÂM THÔNG TIN THƯ VIỆN - TRẠM KIOSK TỰ PHỤC VỤ
        </p>
      </div>

      <div style="padding: 24px;">
        <div style="text-align: center; margin-bottom: 20px;">
          <h3 style="color: #991b1b; font-size: 20px; margin: 0;">
            BIÊN LAI ĐIỆN TỬ: ${actionName}
          </h3>
          <p style="color: #64748b; font-size: 13px; margin: 4px 0 0;">
            Thời gian giao dịch: ${dateStr}
          </p>
        </div>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 20px; font-size: 14px;">
          <div>Họ và tên bạn đọc: <strong>${reader.name}</strong></div>
          <div>Mã sinh viên (MSSV): <strong>${reader.studentId}</strong></div>
          <div>Khoa / Đơn vị: <strong>${reader.department || 'Khoa CNTT - PTIT'}</strong></div>
        </div>

        <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 24px;">
          <thead>
            <tr style="background: #f1f5f9; color: #475569; text-align: left;">
              <th style="padding: 8px 10px; width: 40px; text-align: center;">STT</th>
              <th style="padding: 8px 10px;">Tên tài liệu</th>
              <th style="padding: 8px 10px; text-align: right;">${col3Header}</th>
            </tr>
          </thead>
          <tbody>
            ${itemsHtml}
          </tbody>
        </table>

        <div style="border-top: 1px dashed #cbd5e1; padding-top: 16px; font-size: 12px; color: #64748b; line-height: 1.5;">
          📌 <em>Lưu ý: Bạn đọc vui lòng hoàn trả tài liệu đúng hạn để tránh phát sinh phí trễ hạn. Mọi thắc mắc xin liên hệ quầy thủ thư hoặc qua email thuvien@ptit.edu.vn.</em>
        </div>
      </div>

      <div style="background: #f8fafc; padding: 12px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
        Email này được gửi tự động từ Hệ thống Smart Library Kiosk PTIT. Vui lòng không trả lời thư này.
      </div>
    </div>
  `;

  try {
    const client = getTransporter();
    await client.sendMail({
      from: `"Thư Viện PTIT Kiosk" <${process.env.EMAIL_USER || 'no-reply@ptit.edu.vn'}>`,
      to: reader.email,
      subject: `[PTIT KIOSK] Biên lai ${actionName} - ${reader.studentId}`,
      html: htmlContent
    });
    console.log(`✅ [Email] Đã gửi biên lai thành công tới: ${reader.email}`);
  } catch (err) {
    console.error(`❌ [Email] Lỗi gửi email:`, err.message);
  }
}

