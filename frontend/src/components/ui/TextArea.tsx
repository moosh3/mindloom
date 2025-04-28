import React from 'react';

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
}

const TextArea: React.FC<TextAreaProps> = ({ className = '', error, ...props }) => {
  return (
    <div className="w-full">
      <textarea
        className={`w-full rounded-md border border-border bg-background px-4 py-2 text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary ${className}`}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
};

export default TextArea;