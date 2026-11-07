export function errorHandler(err, req, res, _next) {
  console.error(`💥 [API Error] ${req.method} ${req.url} -`, err.message);

  let statusCode = err.statusCode || 500;
  let message = err.message || 'Lỗi hệ thống máy chủ nội bộ';

  if (err.name === 'CastError') {
    statusCode = 400;
    message = `Định dạng mã định danh ID không hợp lệ: ${err.value}`;
  } else if (err.name === 'ValidationError') {
    statusCode = 400;
  }

  res.status(statusCode).json({
    success: false,
    message,
    stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
  });
}

