import { Agent, AgentCategory, FilterOption, TabOption } from '../types';
import { 
  Bot, 
  Code, 
  Database, 
  FileQuestion, 
  HelpCircle, 
  Mail, 
  MessageSquare, 
  PencilRuler, 
  Receipt, 
  Search, 
  ShoppingCart, 
  Ticket, 
  Users 
} from 'lucide-react';

export const agentCategories: FilterOption[] = [
  { id: 'popular', label: 'Popular', value: 'popular' },
  { id: 'use-cases', label: 'Use cases', value: 'use-cases' },
  { id: 'writing', label: 'Writing', value: 'writing' },
  { id: 'automating-tasks', label: 'Automating tasks', value: 'automating-tasks' },
  { id: 'summarization', label: 'Summarization', value: 'summarization' },
  { id: 'data-analysis', label: 'Data analysis', value: 'data-analysis' },
];

export const departmentCategories: FilterOption[] = [
  { id: 'departments', label: 'Departments', value: 'departments' },
  { id: 'it', label: 'IT', value: 'it' },
  { id: 'engineering', label: 'Engineering', value: 'engineering' },
  { id: 'sales', label: 'Sales', value: 'sales' },
  { id: 'support', label: 'Support', value: 'support' },
];

export const tabOptions: TabOption[] = [
  { id: 'all', label: 'All', count: 93 },
  { id: 'scheduled', label: 'Scheduled', count: 2 },
  { id: 'created', label: 'Created by me', count: 6 },
];

export const agentIconMap: Record<string, React.ElementType> = {
  'qa': FileQuestion,
  'ticket': Ticket,
  'lead': ShoppingCart,
  'pull': Code,
  'email': Mail,
  'tech': HelpCircle,
  'meeting': MessageSquare,
  'admin': Database,
  'brand': PencilRuler,
  'buddy': Code,
  'sales': Users,
  'default': Bot,
  'search': Search,
  'receipt': Receipt,
};

export const agentTemplates: Agent[] = [
  {
    id: '1',
    name: 'Q&A agent',
    description: 'Deflect questions with a knowledge base',
    icon: 'qa',
    category: 'popular',
  },
  {
    id: '2',
    name: 'Ticket tracker',
    description: 'Categorize and assign tickets automatically',
    icon: 'ticket',
    category: 'popular',
  },
  {
    id: '3',
    name: 'LeadGenie',
    description: 'Automate identifying and engage leads',
    icon: 'lead',
    category: 'sales',
  },
  {
    id: '4',
    name: 'Pull request reviewer',
    description: 'Automate code reviews according to a guide',
    icon: 'pull',
    category: 'engineering',
  },
  {
    id: '5',
    name: 'Email negotiator',
    description: 'Respond to inquiries on deals automatically',
    icon: 'email',
    category: 'sales',
  },
  {
    id: '6',
    name: 'Tech Assist',
    description: 'Troubleshoot issues and guide users to resolve',
    icon: 'tech',
    category: 'support',
  },
  {
    id: '7',
    name: 'Meeting prep alert',
    description: 'Research an attendee and past conversations',
    icon: 'meeting',
    category: 'popular',
  },
  {
    id: '8',
    name: 'IT Admin Pro',
    description: 'Automate user queries, IT updates, and comms',
    icon: 'admin',
    category: 'it',
  },
  {
    id: '9',
    name: 'Brand voice writer',
    description: 'Creates consistent and engaging brand messaging',
    icon: 'brand',
    category: 'marketing',
  },
  {
    id: '10',
    name: 'Code buddy',
    description: 'Provides coding help and debugging support',
    icon: 'buddy',
    category: 'engineering',
  },
  {
    id: '11',
    name: 'Personalize sales outreach',
    description: 'Help with making great sales outreach emails',
    icon: 'sales',
    category: 'sales',
  },
  {
    id: '12',
    name: 'Data Analyzer',
    description: 'Analyze data and generate insights',
    icon: 'default',
    category: 'data-analysis',
  },
];

export const userAgents: Agent[] = [
  {
    id: '101',
    name: 'Customer Support Bot',
    description: 'Handles common customer queries',
    icon: 'default',
    category: 'support',
    isCustom: true,
    createdAt: new Date(2023, 1, 15),
  },
  {
    id: '102',
    name: 'Sales Email Assistant',
    description: 'Drafts personalized sales emails',
    icon: 'email',
    category: 'sales',
    isCustom: true,
    createdAt: new Date(2023, 2, 10),
  },
  {
    id: '103',
    name: 'Bug Report Analyzer',
    description: 'Categorizes and prioritizes bug reports',
    icon: 'pull',
    category: 'engineering',
    isCustom: true,
    createdAt: new Date(2023, 3, 5),
  },
  {
    id: '104',
    name: 'Meeting Summary Bot',
    description: 'Creates concise meeting summaries',
    icon: 'meeting',
    category: 'popular',
    isCustom: true,
    createdAt: new Date(2023, 3, 20),
  },
  {
    id: '105',
    name: 'Invoice Generator',
    description: 'Creates and manages invoices',
    icon: 'receipt',
    category: 'sales',
    isCustom: true,
    createdAt: new Date(2023, 4, 12),
  },
  {
    id: '106',
    name: 'Document Search',
    description: 'Searches through company documents',
    icon: 'search',
    category: 'it',
    isCustom: true,
    createdAt: new Date(2023, 5, 8),
  },
];