import { catalogService } from './src/services/catalogService.js';

console.log('================================================================');
console.log('   KIỂM THỬ THỰC TẾ ĐA TRƯỜNG HỢP (SIMULATION BENCHMARK)        ');
console.log('================================================================\n');

const testSuite = [
  {
    name: 'Kiểm thử 1: "tiếng anh" (Khắc phục lỗi người dùng phản ánh)',
    query: 'tiếng anh',
    mustIncludeCategory: 'Giáo dục – Ngoại ngữ',
    forbiddenTitles: ['Người Đàn Ông Mang Tên Ove', 'Boxset Harry Potter']
  },
  {
    name: 'Kiểm thử 2: "tiếng nhật" (Khắc phục lỗi người dùng phản ánh)',
    query: 'tiếng nhật',
    mustIncludeCategory: 'Giáo dục – Ngoại ngữ',
    forbiddenTitles: ['Người Đàn Ông Mang Tên Ove', 'Cô Bé Hàng Xóm Và Bốn Viên Kẹo']
  },
  {
    name: 'Kiểm thử 3: "lập trình python"',
    query: 'lập trình python',
    mustIncludeCategory: 'Công nghệ thông tin',
    forbiddenTitles: ['Người Đàn Ông Mang Tên Ove']
  },
  {
    name: 'Kiểm thử 4: "vi điều khiển esp32 iot"',
    query: 'vi điều khiển esp32 iot',
    mustIncludeCategory: 'Công nghệ thông tin',
    forbiddenTitles: ['Người Đàn Ông Mang Tên Ove']
  },
  {
    name: 'Kiểm thử 5: "dạo này em bị stress mất ngủ và áp lực thi cử"',
    query: 'dạo này em bị stress mất ngủ và áp lực thi cử',
    mustIncludeCategory: 'Phát triển bản thân',
    forbiddenTitles: ['Người Đàn Ông Mang Tên Ove']
  },
  {
    name: 'Kiểm thử 6: "sách làm giàu và đầu tư chứng khoán"',
    query: 'sách làm giàu và đầu tư chứng khoán',
    mustIncludeCategory: 'Kinh tế – Kinh doanh',
    forbiddenTitles: ['Người Đàn Ông Mang Tên Ove']
  },
  {
    name: 'Kiểm thử 7: "an toàn thông tin bảo mật mạng"',
    query: 'an toàn thông tin bảo mật mạng',
    mustIncludeCategory: 'Công nghệ thông tin',
    forbiddenTitles: ['Người Đàn Ông Mang Tên Ove']
  },
  {
    name: 'Kiểm thử 8: "tiểu thuyết kinh điển"',
    query: 'tiểu thuyết kinh điển',
    mustIncludeCategory: 'Văn học – Tiểu thuyết',
    forbiddenTitles: []
  }
];

let allPassed = true;

for (const t of testSuite) {
  const books = catalogService.searchPrecision(t.query, 4);
  console.log(`🔍 [${t.name}]`);
  console.log(`   Query: "${t.query}"`);
  
  let passed = true;
  for (const b of books) {
    console.log(`    -> [${b.bookId}] "${b.title}" | Kệ: ${b.shelf} Tầng: ${b.floor} | ${b.category} (${b.subcategory})`);
    if (t.forbiddenTitles.includes(b.title)) {
      console.error(`       ❌ LỖI: Trả về sách cấm "${b.title}"!`);
      passed = false;
    }
  }

  const hasExpectedCat = books.some(b => b.category.includes(t.mustIncludeCategory));
  if (!hasExpectedCat) {
    console.error(`       ❌ LỖI: Không có sách thuộc thể loại "${t.mustIncludeCategory}"!`);
    passed = false;
  }

  if (passed) {
    console.log(`   ✅ KẾT QUẢ: ĐẠT CHUẨN 100%\n`);
  } else {
    console.log(`   ❌ KẾT QUẢ: KHÔNG ĐẠT\n`);
    allPassed = false;
  }
}

if (allPassed) {
  console.log('🎉 TẤT CẢ 8 BỘ KIỂM THỬ KHẮC NGHIỆT ĐỀU ĐẠT 100% HOÀN HẢO!');
  process.exit(0);
} else {
  console.error('⚠️ Có bài test không đạt.');
  process.exit(1);
}
