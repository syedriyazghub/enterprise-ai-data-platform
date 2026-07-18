'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { cn, formatBytes } from '@/lib/utils';
import { ingestionApi } from '@/lib/api';
import toast from 'react-hot-toast';

interface UploadedFile {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  result?: Record<string, unknown>;
  error?: string;
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);

  const onDrop = useCallback((accepted: File[]) => {
    setFiles(prev => [...prev, ...accepted.map(f => ({ file: f, status: 'pending' as const }))]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/json': ['.json'],
      'application/xml': ['.xml'],
      'application/pdf': ['.pdf'],
    },
    maxSize: 500 * 1024 * 1024,
  });

  const uploadAll = async () => {
    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== 'pending') continue;
      setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: 'uploading' } : f));
      try {
        const result = await ingestionApi.uploadFile(files[i].file);
        setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: 'success', result } : f));
        toast.success(`${files[i].file.name} ingested`);
      } catch (err: unknown) {
        const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Upload failed';
        setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: 'error', error: msg } : f));
        toast.error(msg);
      }
    }
  };

  const statusIcon = (s: UploadedFile['status']) => {
    if (s === 'uploading') return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    if (s === 'success')   return <CheckCircle className="h-4 w-4 text-green-500" />;
    if (s === 'error')     return <XCircle className="h-4 w-4 text-red-500" />;
    return <FileText className="h-4 w-4 text-muted-foreground" />;
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Upload Data</h1>
        <p className="text-muted-foreground">Drag & drop files. Supports CSV, Excel, JSON, XML, PDF, Parquet.</p>
      </div>

      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors',
          isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
        <p className="text-sm font-medium">
          {isDragActive ? 'Drop files here…' : 'Drag & drop files here, or click to select'}
        </p>
        <p className="text-xs text-muted-foreground mt-1">Max 500 MB per file</p>
      </div>

      {files.length > 0 && (
        <div className="rounded-lg border border-border bg-card">
          <div className="px-5 py-3 border-b border-border flex items-center justify-between">
            <span className="text-sm font-medium">{files.length} file(s) selected</span>
            <button
              onClick={uploadAll}
              className="px-4 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              Upload All
            </button>
          </div>
          <ul className="divide-y divide-border">
            {files.map((f, i) => (
              <li key={i} className="flex items-center gap-3 px-5 py-3">
                {statusIcon(f.status)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{f.file.name}</p>
                  <p className="text-xs text-muted-foreground">{formatBytes(f.file.size)}</p>
                  {f.result && (
                    <p className="text-xs text-green-500">
                      {(f.result as { records_ingested?: number }).records_ingested ?? 0} records ingested
                    </p>
                  )}
                  {f.error && <p className="text-xs text-red-500">{f.error}</p>}
                </div>
                <span className="text-xs text-muted-foreground capitalize">{f.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
