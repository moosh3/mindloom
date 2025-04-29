import React, { useState } from 'react';
import { Handle, Position } from 'reactflow';
import { GitBranch, Plus, ChevronUp, ChevronDown, Trash2 } from 'lucide-react';

interface Condition {
  id: string;
  type: 'if' | 'else if' | 'else';
  condition: string;
}

interface DecisionNodeData {
  label: string;
  conditions: Condition[];
}

const DecisionNode = ({ data, selected }: { data: DecisionNodeData; selected: boolean }) => {
  const [conditions, setConditions] = useState<Condition[]>(data.conditions || [
    { id: '1', type: 'if', condition: '' }
  ]);
  const [expandedConditions, setExpandedConditions] = useState<Set<string>>(new Set(['1']));

  const toggleCondition = (id: string) => {
    const newExpanded = new Set(expandedConditions);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedConditions(newExpanded);
  };

  const addConditionAfter = (afterId: string) => {
    const index = conditions.findIndex(c => c.id === afterId);
    if (index === -1) return;

    const newCondition = {
      id: Date.now().toString(),
      type: 'else if' as const,
      condition: ''
    };

    const newConditions = [...conditions];
    newConditions.splice(index + 1, 0, newCondition);
    setConditions(newConditions);
    setExpandedConditions(new Set([...expandedConditions, newCondition.id]));
  };

  const removeCondition = (id: string) => {
    if (conditions.length > 1) {
      setConditions(conditions.filter(c => c.id !== id));
      const newExpanded = new Set(expandedConditions);
      newExpanded.delete(id);
      setExpandedConditions(newExpanded);
    }
  };

  const updateCondition = (id: string, value: string) => {
    setConditions(conditions.map(c => 
      c.id === id ? { ...c, condition: value } : c
    ));
  };

  return (
    <div className="relative">
      <div className={`min-w-[300px] rounded-lg border ${selected ? 'border-primary' : 'border-border'} bg-background shadow-lg`}>
        <div className="flex items-center space-x-3 border-b border-border p-3">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-amber-500/10">
            <GitBranch className="h-4 w-4 text-amber-500" />
          </div>
          <span className="text-sm font-medium text-text">{data.label || 'Condition'}</span>
        </div>

        <div className="space-y-2 p-3">
          {conditions.map((condition, index) => (
            <div
              key={condition.id}
              className="rounded-lg border border-border bg-background-secondary"
            >
              <div className="flex items-center justify-between border-b border-border px-3 py-2">
                <span className="text-sm text-text">
                  {index === 0 ? 'if' : condition.type}
                </span>
                {condition.type !== 'else' && (
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => addConditionAfter(condition.id)}
                      className="rounded p-1 hover:bg-background-tertiary"
                    >
                      <Plus className="h-4 w-4 text-text-secondary" />
                    </button>
                    {conditions.length > 1 && (
                      <button
                        onClick={() => removeCondition(condition.id)}
                        className="rounded p-1 hover:bg-background-tertiary"
                      >
                        <Trash2 className="h-4 w-4 text-text-secondary" />
                      </button>
                    )}
                    <button
                      onClick={() => toggleCondition(condition.id)}
                      className="rounded p-1 hover:bg-background-tertiary"
                    >
                      {expandedConditions.has(condition.id) ? (
                        <ChevronUp className="h-4 w-4 text-text-secondary" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-text-secondary" />
                      )}
                    </button>
                  </div>
                )}
              </div>

              {expandedConditions.has(condition.id) && (
                <div className="p-3">
                  <textarea
                    value={condition.condition}
                    onChange={(e) => updateCondition(condition.id, e.target.value)}
                    placeholder={condition.type === 'else' ? 'Add action...' : '<response> === true'}
                    className="w-full rounded border border-border bg-background px-3 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none"
                    rows={2}
                  />
                </div>
              )}
            </div>
          ))}

          {!conditions.some(c => c.type === 'else') && (
            <button
              onClick={() => setConditions([...conditions, { id: Date.now().toString(), type: 'else', condition: '' }])}
              className="flex w-full items-center justify-center space-x-2 rounded border border-border bg-background-secondary px-3 py-2 text-sm text-text-secondary hover:bg-background-tertiary"
            >
              <Plus className="h-4 w-4" />
              <span>Add else block</span>
            </button>
          )}
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
      <Handle
        type="source"
        position={Position.Right}
        className="!border-border !bg-background-secondary"
      />
    </div>
  );
};

export default DecisionNode;