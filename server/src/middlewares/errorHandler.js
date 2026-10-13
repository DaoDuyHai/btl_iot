export function errorHandler(err, req, res, next) {
  console.error(`💥 [API Error] ${req.method} ${req.url} -`, err.message);

  const statusCode = err.statusCode || 500;
  res.status(statusCode).json({
    success: false,
    message: err.message || 'Lỗi hệ thống máy chủ nội bộ',
    stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
  });
}

