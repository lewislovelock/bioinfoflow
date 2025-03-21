'use client';

import { ReactNode } from 'react';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { Toaster } from '@/components/ui/sonner';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Toaster />
      <div className="flex min-h-screen flex-col">
        <Navbar />
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 p-6 md:p-8">
            {children}
          </main>
        </div>
        <footer className="border-t py-4">
          <div className="container flex items-center justify-center text-center text-sm text-muted-foreground">
            BioinfoFlow &copy; {new Date().getFullYear()} - Scientific Workflow Management for Bioinformatics
          </div>
        </footer>
      </div>
    </div>
  );
} 