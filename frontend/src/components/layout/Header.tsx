'use client';

import { useTheme } from 'next-themes';
import { usePathname } from 'next/navigation';
import { Sun, Moon, Bell, User, ChevronRight, LogOut, Settings } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

const ROUTE_LABELS: Record<string, string> = {
  dashboard:     'Dashboard',
  sources:       'Data Sources',
  upload:        'Upload',
  pipelines:     'Pipelines',
  validation:    'Validation',
  'ai-chat':     'AI Assistant',
  analytics:     'Analytics',
  reports:       'Reports',
  notifications: 'Notifications',
  settings:      'Settings',
};

function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);
  return (
    <nav className="flex items-center gap-1 text-sm">
      {segments.map((seg, i) => {
        const label = ROUTE_LABELS[seg] ?? seg;
        const isLast = i === segments.length - 1;
        return (
          <span key={seg} className="flex items-center gap-1">
            {i > 0 && <ChevronRight className="h-3 w-3 text-muted-foreground" />}
            <span className={cn(isLast ? 'font-medium text-foreground' : 'text-muted-foreground')}>
              {label}
            </span>
          </span>
        );
      })}
    </nav>
  );
}

function ProfileMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 p-1.5 rounded-md hover:bg-accent transition-colors"
        aria-label="Profile"
      >
        <div className="h-7 w-7 rounded-full bg-primary flex items-center justify-center">
          <User className="h-3.5 w-3.5 text-primary-foreground" />
        </div>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-48 rounded-lg border border-border bg-card shadow-lg z-50 py-1">
          <div className="px-3 py-2 border-b border-border">
            <p className="text-sm font-medium">Admin User</p>
            <p className="text-xs text-muted-foreground">admin@platform.com</p>
          </div>
          <button className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent transition-colors">
            <Settings className="h-3.5 w-3.5" /> Settings
          </button>
          <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-500 hover:bg-accent transition-colors">
            <LogOut className="h-3.5 w-3.5" /> Sign out
          </button>
        </div>
      )}
    </div>
  );
}

export function Header() {
  const { theme, setTheme } = useTheme();

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-6 shrink-0">
      <Breadcrumbs />

      <div className="flex items-center gap-1">
        {/* Theme toggle */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="p-2 rounded-md hover:bg-accent transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'dark'
            ? <Sun className="h-4 w-4" />
            : <Moon className="h-4 w-4" />
          }
        </button>

        {/* Notifications */}
        <button className="relative p-2 rounded-md hover:bg-accent transition-colors" aria-label="Notifications">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500" />
        </button>

        {/* Profile */}
        <ProfileMenu />
      </div>
    </header>
  );
}
