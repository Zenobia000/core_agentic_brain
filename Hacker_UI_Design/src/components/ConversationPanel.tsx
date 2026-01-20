import { CheckCircle } from 'lucide-react';

export function ConversationPanel() {
  const messages = [
    {
      role: 'user',
      content: 'Please implement the auth logic.',
    },
    {
      role: 'MANUS',
      content: 'Done: Schema updated, tests passed',
      count: 12,
    },
  ];

  return (
    <div className="flex-1 border-b border-[#00ff00] p-4">
      <div className="space-y-3">
        {messages.map((msg, idx) => (
          <div key={idx} className="flex items-start gap-2">
            <span className="text-[#00ff00] text-glow">
              {msg.role}:
            </span>
            <div className="flex items-center gap-2">
              {msg.role === 'MANUS' && (
                <CheckCircle className="h-4 w-4 text-[#00ff00]" />
              )}
              <span className="text-[#00ff00] text-glow">
                {msg.content}
                {msg.count && (
                  <span className="ml-1 opacity-60">({msg.count})</span>
                )}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
