import React, { useEffect, useRef, useState } from 'react';
import { ArrowLeft, Download, XCircle, Users, Bot } from 'lucide-react';
import Button from '../components/ui/Button';
import { AgentRun, TeamRun } from '../types';

type Run = AgentRun | TeamRun;

const isTeamRun = (run: Run): run is TeamRun => {
  return 'teamId' in run;
};

interface RunOutputProps {
  run: Run;
  onBack: () => void;
  onStop?: () => void;
}

const RunOutput: React.FC<RunOutputProps> = ({ run, onBack, onStop }) => {
  const [status, setStatus] = useState<'running' | 'completed' | 'failed'>(run.status);
  const [progress, setProgress] = useState(run.status === 'completed' ? 100 : 0);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (run.status === 'running') {
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval);
            setStatus('completed');
            return 100;
          }
          return prev + 10;
        });
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [run.status]);

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [run.logs]);

  const downloadLogs = () => {
    const logText = run.logs.join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `run-${run.id}-${new Date().toISOString()}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
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
          <div className="flex items-center">
            <div className="mr-3 flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              {isTeamRun(run) ? (
                <Users className="h-4 w-4 text-primary" />
              ) : (
                <Bot className="h-4 w-4 text-primary" />
              )}
            </div>
            <div>
              <h1 className="text-xl font-semibold text-text">
                {isTeamRun(run) ? run.teamName : run.agentName}
              </h1>
              <p className="text-sm text-text-secondary">
                Started {run.startTime.toLocaleString()}
              </p>
            </div>
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
            <h2 className="text-sm font-medium text-text">Execution Logs</h2>
          </div>
          <div className="h-[calc(100vh-300px)] overflow-y-auto p-4 font-mono">
            <div className="space-y-1">
              {run.logs.map((log, index) => (
                <div key={index} className="text-sm text-text">
                  {log}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>

        {isTeamRun(run) && run.agentRuns && (
          <div className="mt-4 rounded-lg border border-border bg-background-secondary">
            <div className="border-b border-border px-4 py-2">
              <h2 className="text-sm font-medium text-text">Agent Runs</h2>
            </div>
            <div className="p-4">
              <div className="space-y-2">
                {run.agentRuns.map((agentRun) => (
                  <div
                    key={agentRun.id}
                    className="rounded-lg border border-border bg-background p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Bot className="h-4 w-4 text-primary" />
                        <div>
                          <div className="font-medium text-text">
                            {agentRun.agentName}
                          </div>
                          <div className="text-sm text-text-secondary">
                            {agentRun.duration
                              ? `Completed in ${formatDuration(agentRun.duration)}`
                              : 'Running...'}
                          </div>
                        </div>
                      </div>
                      <div className="text-sm text-text-secondary">
                        {agentRun.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RunOutput;