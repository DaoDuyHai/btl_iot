@echo off
chcp 65001 > nul
title Smart Library Kiosk - Tự Động Kiểm Thử 100 Câu Hỏi AI

echo ===============================================================================
echo     🤖 TỰ ĐỘNG CHẠY BỘ KIỂM THỬ 100 CÂU HỎI THỦ THƯ AI SMART KIOSK PTIT
echo ===============================================================================
echo.
echo  Đang nạp 100 câu hỏi từ TEST_PROMPTS_100.md...
echo  Toàn bộ kết quả hỏi-đáp sẽ tự động ghi vào CONVERSATION_HISTORY.md!
echo.

node scripts/auto_test_prompts.js %*

echo.
echo ===============================================================================
echo  Nhấn phím bất kỳ để đóng cửa sổ này...
echo ===============================================================================
pause > nul
