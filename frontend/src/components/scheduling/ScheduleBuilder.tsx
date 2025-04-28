import React, { useState, useEffect } from 'react';
import { Clock, Calendar, AlertCircle } from 'lucide-react';
import { Schedule, ScheduleValidationError } from '../../types';

interface ScheduleBuilderProps {
  value: Schedule;
  onChange: (schedule: Schedule) => void;
  onValidationError?: (errors: ScheduleValidationError[]) => void;
}

const ScheduleBuilder: React.FC<ScheduleBuilderProps> = ({
  value,
  onChange,
  onValidationError,
}) => {
  const [schedule, setSchedule] = useState<Schedule>(value);
  const [errors, setErrors] = useState<ScheduleValidationError[]>([]);

  const timezones = Intl.supportedValuesOf('timeZone');

  useEffect(() => {
    validateSchedule(schedule);
  }, [schedule]);

  const validateSchedule = (schedule: Schedule) => {
    const newErrors: ScheduleValidationError[] = [];

    if (schedule.enabled) {
      if (!schedule.frequency) {
        newErrors.push({ field: 'frequency', message: 'Frequency is required' });
      }
      if (schedule.interval < 1) {
        newErrors.push({ field: 'interval', message: 'Interval must be at least 1' });
      }
      if (schedule.frequency !== 'hourly' && !schedule.time) {
        newErrors.push({ field: 'time', message: 'Time is required' });
      }
      if (schedule.frequency === 'weekly' && (!schedule.days || schedule.days.length === 0)) {
        newErrors.push({ field: 'days', message: 'At least one day must be selected' });
      }
      if (schedule.frequency === 'monthly' && !schedule.date) {
        newErrors.push({ field: 'date', message: 'Date is required' });
      }
    }

    setErrors(newErrors);
    if (onValidationError) {
      onValidationError(newErrors);
    }
  };

  const handleChange = (changes: Partial<Schedule>) => {
    const newSchedule = { ...schedule, ...changes };
    setSchedule(newSchedule);
    onChange(newSchedule);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-text">Enable Scheduling</label>
        <label className="relative inline-flex cursor-pointer items-center">
          <input
            type="checkbox"
            checked={schedule.enabled}
            onChange={(e) => handleChange({ enabled: e.target.checked })}
            className="peer sr-only"
          />
          <div className="h-6 w-11 rounded-full bg-background-tertiary after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-border after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:ring-2 peer-focus:ring-primary"></div>
        </label>
      </div>

      {schedule.enabled && (
        <>
          <div>
            <label className="mb-1 block text-sm font-medium text-text">Frequency</label>
            <select
              value={schedule.frequency}
              onChange={(e) => handleChange({ frequency: e.target.value as Schedule['frequency'] })}
              className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text">
              {schedule.frequency === 'hourly' ? 'Every X Hours' : 'Repeat Every'}
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="number"
                min="1"
                value={schedule.interval}
                onChange={(e) => handleChange({ interval: parseInt(e.target.value) })}
                className="w-20 rounded-md border border-border bg-background px-4 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <span className="text-sm text-text-secondary">
                {schedule.frequency === 'hourly' ? 'Hours' :
                 schedule.frequency === 'daily' ? 'Days' :
                 schedule.frequency === 'weekly' ? 'Weeks' : 'Months'}
              </span>
            </div>
          </div>

          {schedule.frequency !== 'hourly' && (
            <div>
              <label className="mb-1 block text-sm font-medium text-text">Time</label>
              <input
                type="time"
                value={schedule.time}
                onChange={(e) => handleChange({ time: e.target.value })}
                className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          )}

          {schedule.frequency === 'weekly' && (
            <div>
              <label className="mb-1 block text-sm font-medium text-text">Days</label>
              <div className="flex flex-wrap gap-2">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, index) => (
                  <button
                    key={day}
                    onClick={() => {
                      const days = schedule.days || [];
                      const newDays = days.includes(index)
                        ? days.filter(d => d !== index)
                        : [...days, index];
                      handleChange({ days: newDays });
                    }}
                    className={`rounded-full px-3 py-1 text-sm ${
                      schedule.days?.includes(index)
                        ? 'bg-primary text-white'
                        : 'bg-background-tertiary text-text'
                    }`}
                  >
                    {day}
                  </button>
                ))}
              </div>
            </div>
          )}

          {schedule.frequency === 'monthly' && (
            <div>
              <label className="mb-1 block text-sm font-medium text-text">Date</label>
              <select
                value={schedule.date}
                onChange={(e) => handleChange({ date: parseInt(e.target.value) })}
                className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">Select date</option>
                {Array.from({ length: 31 }, (_, i) => i + 1).map(date => (
                  <option key={date} value={date}>
                    {date}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-text">Timezone</label>
            <select
              value={schedule.timezone}
              onChange={(e) => handleChange({ timezone: e.target.value })}
              className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {timezones.map(timezone => (
                <option key={timezone} value={timezone}>
                  {timezone}
                </option>
              ))}
            </select>
          </div>

          {errors.length > 0 && (
            <div className="rounded-md bg-red-50 p-3">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    Please fix the following errors:
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    <ul className="list-inside list-disc space-y-1">
                      {errors.map((error, index) => (
                        <li key={index}>{error.message}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ScheduleBuilder;