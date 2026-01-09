import { useEffect, useState } from 'react';
import { FileX } from 'lucide-react';

function PDFViewer({ pdfUrl, currentPage, onPageChange }) {
  const [displayUrl, setDisplayUrl] = useState(null);

  // 當 pdfUrl 改變時更新顯示 URL
  useEffect(() => {
    if (pdfUrl) {
      setDisplayUrl(pdfUrl);
    }
  }, [pdfUrl]);

  // 當 currentPage 改變時，強制重新載入 iframe
  const iframeSrc = displayUrl ? `${displayUrl}#page=${currentPage}` : null;

  if (!displayUrl) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-400">
        <FileX className="w-16 h-16 mb-4 opacity-50" />
        <p className="text-lg font-medium">尚未上傳文件</p>
        <p className="text-sm mt-2">請點擊右上角按鈕上傳 PDF</p>
      </div>
    );
  }

  return (
    <div className="h-full bg-white rounded-lg overflow-hidden">
      <embed
        key={`${displayUrl}-${currentPage}`}
        src={iframeSrc}
        type="application/pdf"
        className="w-full h-full"
      />
    </div>
  );
}

export default PDFViewer;