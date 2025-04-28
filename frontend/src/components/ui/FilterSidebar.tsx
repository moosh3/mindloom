import React from 'react';
import { FilterOption } from '../../types';

interface FilterSidebarProps {
  title?: string;
  options: FilterOption[];
  selectedOption: string;
  onOptionSelect: (value: string) => void;
}

const FilterSidebar: React.FC<FilterSidebarProps> = ({
  title,
  options,
  selectedOption,
  onOptionSelect,
}) => {
  return (
    <div className="w-48 py-4">
      {title && (
        <h3 className="mb-2 text-xs font-semibold uppercase text-gray-500">{title}</h3>
      )}
      <ul className="space-y-1">
        {options.map((option) => (
          <li key={option.id}>
            <button
              onClick={() => onOptionSelect(option.value)}
              className={`w-full rounded-md px-3 py-2 text-sm text-left transition-colors ${
                selectedOption === option.value
                  ? 'bg-blue-50 text-blue-600 font-medium'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {option.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default FilterSidebar;