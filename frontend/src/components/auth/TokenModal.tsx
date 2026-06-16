import { useState } from 'react';

interface TokenModalProps {
  onClose: () => void;
}

export function TokenModal({ onClose }: TokenModalProps) {
  const [token, setToken] = useState('');

  const handleSubmit = () => {
    localStorage.setItem('nwr_token', token);
    onClose();
    window.location.reload();
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-[60]">
      <div className="bg-white rounded-lg shadow-xl p-6 w-80" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-bold mb-2">需要认证</h3>
        <p className="text-sm text-gray-500 mb-4">请输入 API 访问令牌</p>
        <input
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="w-full border rounded px-3 py-2 text-sm mb-4"
          placeholder="输入令牌..."
          autoFocus
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
        />
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-300 text-gray-600 py-2 rounded hover:bg-gray-50 text-sm"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={!token.trim()}
            className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50 text-sm"
          >
            登录
          </button>
        </div>
      </div>
    </div>
  );
}
