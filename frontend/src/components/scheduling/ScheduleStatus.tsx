import React from 'react';
import { Play, Pause, Clock, AlertCircle } from 'lucide-react';
import { Schedule } from '../../types';

interface ScheduleStatusProps {
  schedule: Schedule;
  status: 'active' | 'paused' | 'error';
  onToggle: () => void;
}

const ScheduleStatus: React.FC<ScheduleStatusProps> = ({
  schedule,
  status,
  onToggle,
}) => {
  const formatNextRun = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(date);
  };

  const getStatusColor = () => {
    switch (status) {
      case 'active':
        return 'text-green-500';
      case 'paused':
        return 'text-gray-400';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'active':
        return <Clock className="h-4 w-4" />;
      case 'paused':
        return <Pause className="h-4 w-4" />;
      case 'error':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  return (
    <div className="flex items-center space-x-4">
      <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
        {getStatusIcon()}
        <span className="text-sm font-medium capitalize">{status}</span>
      </div>
      
      {schedule.nextRun && (
        <div className="text-sm text-gray-400">
          Next run: {formatNextRun(schedule.nextRun)}
        </div>
      )}

      <button
        onClick={onToggle}
        className="ml-auto rounded-md p-1 hover:bg-drw-dark-light"
      >
        {status === 'paused' ? (
          <Play className="h-4 w-4 text-drw-gold" />
        ) : (
          <Pause className="h-4 w-4 text-drw-gold" />
        )}
      </button>
    </div>
  );
};

export default ScheduleStatus;