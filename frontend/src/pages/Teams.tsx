import React, { useState } from 'react';
import { Plus, Users, Search, Bot } from 'lucide-react';
import Button from '../components/ui/Button';
import CreateTeamModal from '../components/CreateTeamModal';
import TeamRunConfig from './TeamRunConfig';
import TeamRunOutput from './TeamRunOutput';
import { Agent, Team } from '../types';

const Teams: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([
    {
      id: '1',
      name: 'Customer Support',
      description: 'Team of agents handling customer inquiries and support tickets',
      type: 'route',
      agents: [],
      createdAt: new Date(2024, 0, 15),
    },
    {
      id: '2',
      name: 'Sales Operations',
      description: 'Automated sales and lead generation agent team',
      type: 'coordinate',
      agents: [],
      createdAt: new Date(2024, 1, 1),
    },
  ]);

  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [view, setView] = useState<'list' | 'config' | 'output'>('list');

  const handleCreateTeam = (teamData: {
    name: string;
    description: string;
    type: 'route' | 'coordinate' | 'collaborate';
    agents: Agent[];
  }) => {
    const newTeam: Team = {
      id: Date.now().toString(),
      ...teamData,
      createdAt: new Date(),
    };
    setTeams([...teams, newTeam]);
  };

  const handleTeamClick = (team: Team) => {
    setSelectedTeam(team);
    setView('config');
  };

  const handleRunTeam = (config: any) => {
    setView('output');
  };

  const filteredTeams = teams.filter(
    team => 
      team.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      team.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getTypeColor = (type: Team['type']) => {
    switch (type) {
      case 'route':
        return 'text-blue-500 bg-blue-50';
      case 'coordinate':
        return 'text-purple-500 bg-purple-50';
      case 'collaborate':
        return 'text-green-500 bg-green-50';
    }
  };

  if (view === 'config' && selectedTeam) {
    return (
      <TeamRunConfig
        team={selectedTeam}
        onBack={() => {
          setView('list');
          setSelectedTeam(null);
        }}
        onRun={handleRunTeam}
      />
    );
  }

  if (view === 'output' && selectedTeam) {
    return (
      <TeamRunOutput
        team={selectedTeam}
        onBack={() => {
          setView('list');
          setSelectedTeam(null);
        }}
      />
    );
  }

  return (
    <div className="flex h-full flex-col bg-background">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <h1 className="text-xl font-semibold text-text">Agent Teams</h1>
        <Button 
          variant="primary" 
          icon={<Plus className="h-4 w-4" />}
          onClick={() => setIsCreating(true)}
        >
          Create team
        </Button>
      </div>

      <div className="flex-1 p-6">
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
            <input
              type="text"
              placeholder="Search agent teams..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-md border border-border bg-background pl-10 pr-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {filteredTeams.map((team) => (
            <button
              key={team.id}
              onClick={() => handleTeamClick(team)}
              className="rounded-lg border border-border bg-background p-4 text-left hover:border-primary transition-colors"
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Users className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-medium text-text">{team.name}</h3>
                    <p className="text-sm text-text-secondary">
                      Created {team.createdAt.toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <span className={`rounded-full px-2 py-1 text-xs font-medium capitalize ${getTypeColor(team.type)}`}>
                  {team.type}
                </span>
              </div>
              <p className="mb-4 text-sm text-text-secondary">
                {team.description}
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-sm text-text-secondary">
                  <Bot className="h-4 w-4" />
                  <span>{team.agents.length} agents</span>
                </div>
                <span className="text-sm text-primary">Configure & Run →</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <CreateTeamModal
        isOpen={isCreating}
        onClose={() => setIsCreating(false)}
        onSave={handleCreateTeam}
      />
    </div>
  );
};

export default Teams;