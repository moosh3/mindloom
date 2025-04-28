import React, { useEffect, useRef, useState } from 'react';
import { ArrowLeft, Download, XCircle, Users } from 'lucide-react';
import Button from '../components/ui/Button';
import { Team, AgentRun } from '../types';

interface TeamRunOutputProps {
  team: Team;
  onBack: () => void;
  onStop?: () => void;
}

const TeamRunOutput: React.FC<TeamRunOutputProps> = ({ team, onBack, onStop }) => {
  const [logs, setLogs] = useState<{ timestamp: Date; level: 'info' | 'warning' | 'error'; message: string }[]>([]);
  const [status, setStatus] = useState<'running' | 'completed' | 'failed'>('running');
  const [progress, setProgress] = useState(0);
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Simulate log streaming
  useEffect(() => {
    const mockLogs = [
      { message: `Initializing team "${team.name}"...`, delay: 500 },
      { message: 'Loading team configuration...', delay: 1000 },
      { message: 'Processing input variables...', delay: 1500 },
      ...team.agents.flatMap((agent, index) => [
        { message: `Starting agent "${agent.name}"...`, delay: 2000 + index * 1000 },
        { message: `Agent "${agent.name}" completed`, delay: 3000 + index * 1000 }
      ]),
      { message: 'Team execution completed successfully', delay: 3000 + team.agents.length * 1000 }
    ];

    mockLogs.forEach(({ message, delay }, index) => {
      setTimeout(() => {
        setLogs(prev => [...prev, {
          timestamp: new Date(),
          level: 'info',
          message
        }]);
        setProgress(((index + 1) / mockLogs.length) * 100);
        
        if (index === mockLogs.length - 1) {
          setStatus('completed');
        }
      }, delay);
    });
  }, [team]);

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const downloadLogs = () => {
    const logText = logs
      .map(log => `[${log.timestamp.toISOString()}] [${log.level}] ${log.message}`)
      .join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `team-run-${new Date().toISOString()}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-full flex-col bg-background">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center">
          <button
            onClick={onBack}
            className="mr-4 rounded-md p-1 hover:bg-background-secondary"
          >
            <ArrowLeft className="h-5 w-5 text-text-secondary" />
          </button>
          <div>
            <h1 className="text-xl font-semibold text-text">{team.name}</h1>
            <p className="text-sm text-text-secondary">{team.description}</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={downloadLogs}
            icon={<Download className="h-4 w-4" />}
          >
            Download Logs
          </Button>
          {status === 'running' && onStop && (
            <Button
              variant="outline"
              onClick={onStop}
              icon={<XCircle className="h-4 w-4" />}
            >
              Stop Execution
            </Button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-hidden p-6">
        <div className="mb-4 rounded-lg border border-border bg-background-secondary p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-text">Progress</span>
            <span className="text-sm text-text-secondary">{Math.round(progress)}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-background">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="rounded-lg border border-border bg-background-secondary">
          <div className="border-b border-border px-4 py-2">
            <h2 className="text-sm font-medium text-text">Team Execution Logs</h2>
          </div>
          <div className="h-[calc(100vh-300px)] overflow-y-auto p-4 font-mono">
            <div className="space-y-1">
              {logs.map((log, index) => (
                <div key={index} className="flex text-sm">
                  <span className="mr-2 text-text-secondary">
                    {log.timestamp.toLocaleTimeString()}
                  </span>
                  <span className={`
                    ${log.level === 'error' ? 'text-red-500' : ''}
                    ${log.level === 'warning' ? 'text-yellow-500' : ''}
                    ${log.level === 'info' ? 'text-text' : ''}
                  `}>
                    {log.message}
                  </span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamRunOutput;