import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <div className="glass rounded-lg p-6 border-l-4 border-red-500">
      <div className="flex items-center space-x-3">
        <AlertCircle className="w-6 h-6 text-red-500" />
        <div>
          <h3 className="text-lg font-semibold text-white">Error</h3>
          <p className="text-gray-400">{message}</p>
        </div>
      </div>
    </div>
  );
}
