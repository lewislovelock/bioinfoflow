'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Network, 
  Play, 
  Settings, 
  PlusCircle 
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export function Sidebar() {
  const pathname = usePathname();

  const routes = [
    {
      name: 'Dashboard',
      href: '/',
      icon: LayoutDashboard,
    },
    {
      name: 'Workflows',
      href: '/workflows',
      icon: Network,
    },
    {
      name: 'Runs',
      href: '/runs',
      icon: Play,
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
    },
  ];

  return (
    <div className="hidden border-r bg-muted/40 md:block md:w-64 lg:w-72">
      <div className="flex h-full flex-col gap-2 p-4">
        <Link 
          href="/workflows/new" 
          className="mb-4"
        >
          <Button className="w-full justify-start gap-1">
            <PlusCircle className="h-4 w-4" />
            <span>New Workflow</span>
          </Button>
        </Link>
        
        <nav className="grid gap-1 px-2 group-[[data-collapsed=true]]:justify-center">
          {routes.map((route) => (
            <Link
              key={route.href}
              href={route.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium",
                "hover:bg-accent hover:text-accent-foreground",
                pathname === route.href 
                  ? "bg-accent text-accent-foreground" 
                  : "text-muted-foreground"
              )}
            >
              <route.icon className="h-4 w-4" />
              <span>{route.name}</span>
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
} 