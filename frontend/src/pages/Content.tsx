import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Plus, FileText, Trash2, PenLine, Bot } from 'lucide-react';
import Button from '../components/ui/Button';
import ConnectAgentModal from '../components/ConnectAgentModal';
import { Agent } from '../types';

interface ContentBucket {
  id: string;
  name: string;
  description: string;
  files: ContentFile[];
  agents: Agent[];
  createdAt: Date;
}

interface ContentFile {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
}

const Content: React.FC = () => {
  const [buckets, setBuckets] = useState<ContentBucket[]>([
    {
      id: '1',
      name: 'Product Documentation',
      description: 'Official product documentation and guides',
      files: [
        {
          id: '1',
          name: 'Getting Started Guide.pdf',
          size: 1024 * 1024 * 2.5,
          type: 'application/pdf',
          uploadedAt: new Date(2024, 2, 1),
        },
        {
          id: '2',
          name: 'API Documentation.pdf',
          size: 1024 * 1024 * 1.8,
          type: 'application/pdf',
          uploadedAt: new Date(2024, 2, 15),
        },
      ],
      agents: [
        {
          id: 'qa-agent',
          name: 'Q&A agent',
          description: 'Deflect questions with a knowledge base',
          icon: 'qa',
          category: 'popular',
        },
        {
          id: 'tech-assist',
          name: 'Tech Assist',
          description: 'Troubleshoot issues and guide users to resolve',
          icon: 'tech',
          category: 'support',
        },
      ],
      createdAt: new Date(2024, 1, 15),
    },
  ]);
  
  const [selectedBucket, setSelectedBucket] = useState<ContentBucket | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isConnectingAgent, setIsConnectingAgent] = useState(false);
  const [newBucketName, setNewBucketName] = useState('');
  const [newBucketDescription, setNewBucketDescription] = useState('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (selectedBucket) {
      const newFiles = acceptedFiles.map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        type: file.type,
        uploadedAt: new Date(),
      }));

      setBuckets(buckets.map(bucket => 
        bucket.id === selectedBucket.id
          ? { ...bucket, files: [...bucket.files, ...newFiles] }
          : bucket
      ));
    }
  }, [selectedBucket, buckets]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
    },
  });

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleCreateBucket = () => {
    if (!newBucketName.trim()) return;

    const newBucket: ContentBucket = {
      id: Math.random().toString(36).substr(2, 9),
      name: newBucketName,
      description: newBucketDescription,
      files: [],
      agents: [],
      createdAt: new Date(),
    };

    setBuckets([...buckets, newBucket]);
    setNewBucketName('');
    setNewBucketDescription('');
    setIsCreating(false);
  };

  const handleDeleteFile = (bucketId: string, fileId: string) => {
    setBuckets(buckets.map(bucket =>
      bucket.id === bucketId
        ? { ...bucket, files: bucket.files.filter(file => file.id !== fileId) }
        : bucket
    ));
  };

  const handleConnectAgents = (agents: Agent[]) => {
    if (selectedBucket) {
      setBuckets(buckets.map(bucket =>
        bucket.id === selectedBucket.id
          ? { ...bucket, agents }
          : bucket
      ));
      setSelectedBucket({ ...selectedBucket, agents });
    }
  };

  return (
    <div className="flex h-full flex-col bg-background">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <h1 className="text-xl font-semibold text-text">Content</h1>
        <Button
          variant="primary"
          icon={<Plus className="h-4 w-4" />}
          onClick={() => setIsCreating(true)}
        >
          Create bucket
        </Button>
      </div>

      <div className="flex flex-1">
        <div className="w-80 border-r border-border bg-background p-4">
          <div className="space-y-2">
            {buckets.map(bucket => (
              <button
                key={bucket.id}
                onClick={() => setSelectedBucket(bucket)}
                className={`w-full rounded-lg p-3 text-left transition-colors ${
                  selectedBucket?.id === bucket.id
                    ? 'bg-background-secondary text-primary'
                    : 'text-text hover:bg-background-secondary'
                }`}
              >
                <div className="flex items-center">
                  <FileText className="mr-3 h-5 w-5" />
                  <div>
                    <h3 className="font-medium">{bucket.name}</h3>
                    <p className="text-sm text-text-secondary">
                      {bucket.files.length} files
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 p-6">
          {selectedBucket ? (
            <div>
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-text">
                  {selectedBucket.name}
                </h2>
                <p className="text-sm text-text-secondary">
                  {selectedBucket.description}
                </p>
              </div>

              <div className="mb-6">
                <h3 className="mb-2 text-sm font-medium text-text">
                  Connected Agents
                </h3>
                <div className="flex flex-wrap gap-2">
                  {selectedBucket.agents.map(agent => (
                    <div
                      key={agent.id}
                      className="flex items-center rounded-full bg-background-secondary px-3 py-1"
                    >
                      <Bot className="mr-1 h-4 w-4 text-primary" />
                      <span className="text-sm text-text">{agent.name}</span>
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<Plus className="h-3 w-3" />}
                    onClick={() => setIsConnectingAgent(true)}
                  >
                    Connect agent
                  </Button>
                </div>
              </div>

              <div
                {...getRootProps()}
                className={`mb-6 rounded-lg border-2 border-dashed border-border p-6 text-center transition-colors ${
                  isDragActive ? 'border-primary bg-background-secondary' : ''
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="mx-auto mb-2 h-8 w-8 text-text-secondary" />
                <p className="text-sm text-text">
                  Drag & drop files here, or click to select files
                </p>
                <p className="mt-1 text-xs text-text-secondary">
                  Supported formats: PDF, TXT
                </p>
              </div>

              <div>
                <h3 className="mb-4 text-sm font-medium text-text">Files</h3>
                <div className="space-y-2">
                  {selectedBucket.files.map(file => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between rounded-lg border border-border bg-background-secondary p-4"
                    >
                      <div className="flex items-center">
                        <FileText className="mr-3 h-5 w-5 text-text-secondary" />
                        <div>
                          <h4 className="text-sm font-medium text-text">
                            {file.name}
                          </h4>
                          <p className="text-xs text-text-secondary">
                            {formatFileSize(file.size)} • Uploaded{' '}
                            {file.uploadedAt.toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          className="rounded-md p-1 text-text-secondary hover:bg-background hover:text-text"
                          title="Edit"
                        >
                          <PenLine className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteFile(selectedBucket.id, file.id)}
                          className="rounded-md p-1 text-text-secondary hover:bg-background hover:text-red-500"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <FileText className="mx-auto mb-4 h-12 w-12 text-text-secondary" />
                <h2 className="text-lg font-medium text-text">
                  Select a content bucket
                </h2>
                <p className="text-sm text-text-secondary">
                  Choose a bucket from the sidebar or create a new one
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {isCreating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[90vw] max-w-lg rounded-xl bg-background p-6 shadow-xl">
            <h2 className="mb-4 text-lg font-semibold text-text">
              Create new bucket
            </h2>
            <div className="mb-4">
              <label className="mb-1 block text-sm font-medium text-text">
                Name
              </label>
              <input
                type="text"
                value={newBucketName}
                onChange={(e) => setNewBucketName(e.target.value)}
                className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Enter bucket name"
              />
            </div>
            <div className="mb-6">
              <label className="mb-1 block text-sm font-medium text-text">
                Description
              </label>
              <textarea
                value={newBucketDescription}
                onChange={(e) => setNewBucketDescription(e.target.value)}
                className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Enter bucket description"
                rows={3}
              />
            </div>
            <div className="flex justify-end space-x-3">
              <Button variant="outline" onClick={() => setIsCreating(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleCreateBucket}
                disabled={!newBucketName.trim()}
              >
                Create bucket
              </Button>
            </div>
          </div>
        </div>
      )}

      {selectedBucket && (
        <ConnectAgentModal
          isOpen={isConnectingAgent}
          onClose={() => setIsConnectingAgent(false)}
          onConnect={handleConnectAgents}
          connectedAgents={selectedBucket.agents.map(agent => agent.id)}
        />
      )}
    </div>
  );
};

export default Content;