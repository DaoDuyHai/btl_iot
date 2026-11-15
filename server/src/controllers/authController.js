import { ENV } from '../config/env.js';

export function login(req, res) {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({
      success: false,
      message: 'Vui lòng nhập tên đăng nhập và mật khẩu'
    });
  }

  if (username === ENV.ADMIN_USERNAME && password === ENV.ADMIN_PASSWORD) {
    return res.json({
      success: true,
      message: 'Đăng nhập thành công',
      data: {
        token: `ptit_token_${Date.now()}`,
        user: {
          username: ENV.ADMIN_USERNAME,
          name: 'Thủ thư Trưởng',
          role: 'admin'
        }
      }
    });
  }

  return res.status(401).json({
    success: false,
    message: 'Tên đăng nhập hoặc mật khẩu không chính xác'
  });
}

export function me(req, res) {
  return res.json({
    success: true,
    data: {
      username: ENV.ADMIN_USERNAME,
      name: 'Thủ thư Trưởng',
      role: 'admin'
    }
  });
}

