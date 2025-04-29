import React, { useState } from 'react';
import { Handle, Position } from 'reactflow';
import { Code } from 'lucide-react';
import Editor from '@monaco-editor/react';

interface FunctionNodeData {
  code: string;
}

const FunctionNode = ({ data, selected }: { data: FunctionNodeData; selected: boolean }) => {
  const [code, setCode] = useState(data.code || 'def process(input):\n    # Your code here\n    return input');

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      data.code = value;
      setCode(value);
    }
  };

  return (
    <div className="relative">
      <div className={`min-w-[300px] rounded-lg border ${selected ? 'border-primary' : 'border-border'} bg-background shadow-lg`}>
        <div className="flex items-center space-x-3 border-b border-border p-3">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-orange-500/10">
            <Code className="h-4 w-4 text-orange-500" />
          </div>
          <span className="text-sm font-medium text-text">Function</span>
        </div>

        <div className="p-4">
          <div className="rounded-lg border border-border bg-background-secondary overflow-hidden">
            <Editor
              height="200px"
              defaultLanguage="python"
              theme="light"
              value={code}
              onChange={handleEditorChange}
              options={{
                minimap: { enabled: false },
                fontSize: 12,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                tabSize: 4,
                lineHeight: 21,
                folding: false,
                glyphMargin: false,
                automaticLayout: true,
                padding: { top: 8, bottom: 8 },
                lineNumbersMinChars: 2,
                lineDecorationsWidth: 4,
                renderLineHighlight: 'none',
                overviewRulerBorder: false,
                scrollbar: {
                  vertical: 'hidden',
                  horizontal: 'hidden'
                },
                overviewRulerLanes: 0
              }}
            />
          </div>
        </div>
      </div>

      <Handle
        type="target"
        position={Position.Top}
        className="!border-border !bg-background-secondary"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!border-border !bg-background-secondary"
      />
    </div>
  );
};

export default FunctionNode;