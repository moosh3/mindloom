import React, { useState } from 'react';
import { Handle, Position } from 'reactflow';
import { Globe, Plus, Trash2 } from 'lucide-react';
import * as Select from '@radix-ui/react-select';

interface APINodeData {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  queryParams: Array<{ key: string; value: string }>;
  headers: Array<{ key: string; value: string }>;
  body: string;
}

const APINode = ({ data, selected }: { data: APINodeData; selected: boolean }) => {
  const [method, setMethod] = useState<APINodeData['method']>(data.method || 'GET');
  const [queryParams, setQueryParams] = useState<Array<{ key: string; value: string }>>(
    data.queryParams || [{ key: '', value: '' }]
  );
  const [headers, setHeaders] = useState<Array<{ key: string; value: string }>>(
    data.headers || [{ key: '', value: '' }]
  );

  const addRow = (type: 'query' | 'header') => {
    if (type === 'query') {
      setQueryParams([...queryParams, { key: '', value: '' }]);
    } else {
      setHeaders([...headers, { key: '', value: '' }]);
    }
  };

  const removeRow = (type: 'query' | 'header', index: number) => {
    if (type === 'query') {
      setQueryParams(queryParams.filter((_, i) => i !== index));
    } else {
      setHeaders(headers.filter((_, i) => i !== index));
    }
  };

  const updateRow = (type: 'query' | 'header', index: number, field: 'key' | 'value', value: string) => {
    if (type === 'query') {
      const newParams = [...queryParams];
      newParams[index][field] = value;
      setQueryParams(newParams);
    } else {
      const newHeaders = [...headers];
      newHeaders[index][field] = value;
      setHeaders(newHeaders);
    }
  };

  return (
    <div className="relative">
      <div className={`min-w-[300px] rounded-lg border ${selected ? 'border-primary' : 'border-border'} bg-background shadow-lg`}>
        <div className="flex items-center space-x-3 border-b border-border p-3">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-purple-500/10">
            <Globe className="h-4 w-4 text-purple-500" />
          </div>
          <span className="text-sm font-medium text-text">API Request</span>
        </div>

        <div className="space-y-4 p-4">
          {/* URL Input */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">
              URL <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={data.url || ''}
              onChange={(e) => data.url = e.target.value}
              placeholder="Enter URL"
              className="w-full rounded border border-border bg-background-secondary px-3 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none"
            />
          </div>

          {/* Method Selector */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">
              Method <span className="text-red-500">*</span>
            </label>
            <Select.Root value={method} onValueChange={(value) => setMethod(value as APINodeData['method'])}>
              <Select.Trigger className="flex w-full items-center justify-between rounded border border-border bg-background-secondary px-3 py-2 text-sm text-text">
                <Select.Value />
              </Select.Trigger>
              <Select.Portal>
                <Select.Content className="overflow-hidden rounded-md border border-border bg-background shadow-lg">
                  <Select.Viewport>
                    {['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].map((m) => (
                      <Select.Item
                        key={m}
                        value={m}
                        className="cursor-pointer px-3 py-2 text-sm text-text outline-none hover:bg-background-secondary data-[highlighted]:bg-background-secondary"
                      >
                        <Select.ItemText>{m}</Select.ItemText>
                      </Select.Item>
                    ))}
                  </Select.Viewport>
                </Select.Content>
              </Select.Portal>
            </Select.Root>
          </div>

          {/* Query Parameters */}
          <div>
            <label className="mb-2 block text-xs font-medium text-text-secondary">Query Params</label>
            <div className="rounded-lg border border-border bg-background-secondary p-2">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="px-2 py-1 text-left text-xs font-medium text-text-secondary">Key</th>
                    <th className="px-2 py-1 text-left text-xs font-medium text-text-secondary">Value</th>
                    <th className="w-8"></th>
                  </tr>
                </thead>
                <tbody>
                  {queryParams.map((param, index) => (
                    <tr key={index}>
                      <td className="px-1 py-1">
                        <input
                          type="text"
                          value={param.key}
                          onChange={(e) => updateRow('query', index, 'key', e.target.value)}
                          placeholder="Key"
                          className="w-full rounded border border-border bg-background px-2 py-1 text-sm text-text placeholder-text-tertiary"
                        />
                      </td>
                      <td className="px-1 py-1">
                        <input
                          type="text"
                          value={param.value}
                          onChange={(e) => updateRow('query', index, 'value', e.target.value)}
                          placeholder="Value"
                          className="w-full rounded border border-border bg-background px-2 py-1 text-sm text-text placeholder-text-tertiary"
                        />
                      </td>
                      <td className="px-1 py-1">
                        <button
                          onClick={() => removeRow('query', index)}
                          className="rounded p-1 hover:bg-background-tertiary"
                        >
                          <Trash2 className="h-4 w-4 text-text-secondary" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button
                onClick={() => addRow('query')}
                className="mt-2 flex w-full items-center justify-center space-x-1 rounded border border-border px-2 py-1 text-xs text-text-secondary hover:bg-background-tertiary"
              >
                <Plus className="h-3 w-3" />
                <span>Add Row</span>
              </button>
            </div>
          </div>

          {/* Headers */}
          <div>
            <label className="mb-2 block text-xs font-medium text-text-secondary">Headers</label>
            <div className="rounded-lg border border-border bg-background-secondary p-2">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="px-2 py-1 text-left text-xs font-medium text-text-secondary">Key</th>
                    <th className="px-2 py-1 text-left text-xs font-medium text-text-secondary">Value</th>
                    <th className="w-8"></th>
                  </tr>
                </thead>
                <tbody>
                  {headers.map((header, index) => (
                    <tr key={index}>
                      <td className="px-1 py-1">
                        <input
                          type="text"
                          value={header.key}
                          onChange={(e) => updateRow('header', index, 'key', e.target.value)}
                          placeholder="Key"
                          className="w-full rounded border border-border bg-background px-2 py-1 text-sm text-text placeholder-text-tertiary"
                        />
                      </td>
                      <td className="px-1 py-1">
                        <input
                          type="text"
                          value={header.value}
                          onChange={(e) => updateRow('header', index, 'value', e.target.value)}
                          placeholder="Value"
                          className="w-full rounded border border-border bg-background px-2 py-1 text-sm text-text placeholder-text-tertiary"
                        />
                      </td>
                      <td className="px-1 py-1">
                        <button
                          onClick={() => removeRow('header', index)}
                          className="rounded p-1 hover:bg-background-tertiary"
                        >
                          <Trash2 className="h-4 w-4 text-text-secondary" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button
                onClick={() => addRow('header')}
                className="mt-2 flex w-full items-center justify-center space-x-1 rounded border border-border px-2 py-1 text-xs text-text-secondary hover:bg-background-tertiary"
              >
                <Plus className="h-3 w-3" />
                <span>Add Row</span>
              </button>
            </div>
          </div>

          {/* Body */}
          <div>
            <label className="mb-2 block text-xs font-medium text-text-secondary">Body</label>
            <textarea
              value={data.body || ''}
              onChange={(e) => data.body = e.target.value}
              placeholder="Enter JSON..."
              rows={4}
              className="w-full rounded border border-border bg-background-secondary px-3 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none"
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

export default APINode;