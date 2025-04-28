import React, { useState, useEffect } from 'react';
import { 
  ArrowDown, 
  ArrowUp, 
  ChevronDown, 
  ChevronUp, 
  Download, 
  Search,
  Clock,
  AlertCircle,
  CheckCircle,
  Play,
  Users,
  Bot
} from 'lucide-react';
import { AgentRun, TeamRun } from '../types';
import RunOutput from './RunOutput';

type Run = AgentRun | TeamRun;

const isTeamRun = (run: Run): run is TeamRun => {
  return 'teamId' in run;
};

const mockRuns: Run[] = [
  {
    id: '1',
    agentId: 'agent-1',
    agentName: 'Sales Assistant',
    startTime: new Date(Date.now() - 1000 * 60 * 30),
    endTime: new Date(Date.now() - 1000 * 60 * 25),
    triggeredBy: {
      id: 'user-1',
      name: 'John Doe',
      avatar: 'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg'
    },
    status: 'completed',
    duration: 300,
    logs: ['Starting execution...', 'Processing input...', 'Execution completed'],
    input: { query: 'sales forecast' },
    output: { result: 'Forecast analysis completed' },
    resourceUsage: {
      cpuTime: 2.5,
      memoryUsage: 256,
      apiCalls: 3
    }
  },
  {
    id: '2',
    teamId: 'team-1',
    teamName: 'Customer Support Team',
    teamType: 'route',
    startTime: new Date(Date.now() - 1000 * 60 * 15),
    triggeredBy: {
      id: 'user-2',
      name: 'Jane Smith'
    },
    status: 'running',
    logs: ['Starting team execution...', 'Processing tasks...'],
    input: { ticket: 'support-123' },
    agentRuns: [
      {
        id: 'agent-run-1',
        agentId: 'agent-2',
        agentName: 'Ticket Classifier',
        startTime: new Date(Date.now() - 1000 * 60 * 14),
        endTime: new Date(Date.now() - 1000 * 60 * 13),
        triggeredBy: {
          id: 'user-2',
          name: 'Jane Smith'
        },
        status: 'completed',
        duration: 60,
        logs: ['Classifying ticket...', 'Classification completed'],
        input: { ticket: 'support-123' },
        output: { category: 'billing' }
      }
    ]
  }
];

const Runs: React.FC = () => {
  const [runs, setRuns] = useState<Run[]>(mockRuns);
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<'startTime' | 'name' | 'status' | 'type'>('startTime');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const itemsPerPage = 20;

  useEffect(() => {
    const interval = setInterval(() => {
      console.log('Fetching updated run data...');
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getStatusIcon = (status: Run['status']) => {
    switch (status) {
      case 'running':
        return <Play className="h-4 w-4 text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const filteredRuns = runs.filter(run => {
    const searchTerm = searchQuery.toLowerCase();
    const name = isTeamRun(run) ? run.teamName : run.agentName;
    return name.toLowerCase().includes(searchTerm) ||
           run.triggeredBy.name.toLowerCase().includes(searchTerm);
  });

  const sortedRuns = [...filteredRuns].sort((a, b) => {
    let comparison = 0;
    switch (sortField) {
      case 'startTime':
        comparison = a.startTime.getTime() - b.startTime.getTime();
        break;
      case 'name':
        comparison = (isTeamRun(a) ? a.teamName : a.agentName).localeCompare(
          isTeamRun(b) ? b.teamName : b.agentName
        );
        break;
      case 'status':
        comparison = a.status.localeCompare(b.status);
        break;
      case 'type':
        comparison = (isTeamRun(a) ? 'team' : 'agent').localeCompare(
          isTeamRun(b) ? 'team' : 'agent'
        );
        break;
    }
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  const paginatedRuns = sortedRuns.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const exportToCsv = () => {
    const headers = ['Name', 'Type', 'Start Time', 'Duration', 'Status', 'Triggered By'];
    const rows = filteredRuns.map(run => [
      isTeamRun(run) ? run.teamName : run.agentName,
      isTeamRun(run) ? 'Team' : 'Agent',
      run.startTime.toLocaleString(),
      run.duration ? formatDuration(run.duration) : '-',
      run.status,
      run.triggeredBy.name
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'runs.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (selectedRun) {
    return (
      <RunOutput
        run={selectedRun}
        onBack={() => setSelectedRun(null)}
      />
    );
  }

  return (
    <div className="flex h-full flex-col bg-background">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <h1 className="text-xl font-semibold text-text">Runs</h1>
        <button
          onClick={exportToCsv}
          className="flex items-center space-x-2 rounded-md border border-border px-3 py-1.5 text-sm font-medium text-text hover:bg-background-secondary"
        >
          <Download className="h-4 w-4" />
          <span>Export CSV</span>
        </button>
      </div>

      <div className="flex-1 overflow-hidden p-6">
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
            <input
              type="text"
              placeholder="Search by name or user..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-md border border-border bg-background pl-10 pr-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        <div className="rounded-lg border border-border">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-background-secondary">
                  <th className="px-6 py-3 text-left">
                    <button
                      onClick={() => handleSort('name')}
                      className="flex items-center space-x-1 text-sm font-medium text-text"
                    >
                      <span>Name</span>
                      {sortField === 'name' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left">
                    <button
                      onClick={() => handleSort('type')}
                      className="flex items-center space-x-1 text-sm font-medium text-text"
                    >
                      <span>Type</span>
                      {sortField === 'type' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left">
                    <button
                      onClick={() => handleSort('startTime')}
                      className="flex items-center space-x-1 text-sm font-medium text-text"
                    >
                      <span>Start Time</span>
                      {sortField === 'startTime' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-text">Duration</th>
                  <th className="px-6 py-3 text-left">
                    <button
                      onClick={() => handleSort('status')}
                      className="flex items-center space-x-1 text-sm font-medium text-text"
                    >
                      <span>Status</span>
                      {sortField === 'status' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-text">Triggered By</th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-text"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {paginatedRuns.map((run) => (
                  <tr 
                    key={run.id} 
                    className="bg-background hover:bg-background-secondary cursor-pointer"
                    onClick={() => setSelectedRun(run)}
                  >
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-text">
                        {isTeamRun(run) ? run.teamName : run.agentName}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {isTeamRun(run) ? (
                          <>
                            <Users className="h-4 w-4 text-primary" />
                            <span className="text-sm text-text-secondary">Team</span>
                          </>
                        ) : (
                          <>
                            <Bot className="h-4 w-4 text-primary" />
                            <span className="text-sm text-text-secondary">Agent</span>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-text-secondary">
                        {run.startTime.toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-text-secondary">
                        {run.duration ? formatDuration(run.duration) : '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(run.status)}
                        <span className="text-sm capitalize text-text-secondary">
                          {run.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-3">
                        {run.triggeredBy.avatar ? (
                          <img
                            src={run.triggeredBy.avatar}
                            alt={run.triggeredBy.name}
                            className="h-6 w-6 rounded-full"
                          />
                        ) : (
                          <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center">
                            <span className="text-xs font-medium text-primary">
                              {run.triggeredBy.name.charAt(0)}
                            </span>
                          </div>
                        )}
                        <span className="text-sm text-text-secondary">
                          {run.triggeredBy.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedRun(expandedRun === run.id ? null : run.id);
                        }}
                        className="text-text-secondary hover:text-text"
                      >
                        {expandedRun === run.id ? (
                          <ChevronUp className="h-5 w-5" />
                        ) : (
                          <ChevronDown className="h-5 w-5" />
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {sortedRuns.length > itemsPerPage && (
            <div className="flex items-center justify-between border-t border-border bg-background px-6 py-3">
              <div className="text-sm text-text-secondary">
                Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, sortedRuns.length)} of {sortedRuns.length} runs
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="rounded-md border border-border px-3 py-1 text-sm font-medium text-text disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage * itemsPerPage >= sortedRuns.length}
                  className="rounded-md border border-border px-3 py-1 text-sm font-medium text-text disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Runs;