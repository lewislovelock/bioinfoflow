'use client';

import { AppLayout } from "@/components/layout/AppLayout";
import { useRuns } from "@/lib/api/hooks";
import Link from "next/link";
import { formatDistanceToNow } from 'date-fns';
import { Status } from "@/types/api";
import { Play, Plus, Search, ExternalLink, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// Helper function to get appropriate status badge variant
const getStatusBadgeVariant = (status: string): "default" | "destructive" | "outline" | "secondary" | "success" | "warning" => {
  switch (status) {
    case Status.COMPLETED:
      return 'success';
    case Status.RUNNING:
      return 'default';
    case Status.PENDING:
      return 'secondary';
    case Status.FAILED:
    case Status.ERROR:
      return 'destructive';
    case Status.TERMINATED_TIME_LIMIT:
      return 'warning';
    case Status.SKIPPED:
      return 'outline';
    default:
      return 'outline';
  }
};

export default function RunsPage() {
  const { data: runs, isLoading, error } = useRuns();

  return (
    <AppLayout>
      <div className="flex flex-col gap-8">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Workflow Runs</h1>
            <p className="text-muted-foreground">
              Monitor and manage your workflow executions
            </p>
          </div>
          <Button asChild>
            <Link href="/workflows">
              <Play className="mr-2 h-4 w-4" />
              Run a Workflow
            </Link>
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>All Runs</CardTitle>
            <CardDescription>
              View the status and details of all workflow executions
            </CardDescription>
            <div className="flex items-center gap-2 pt-4">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search runs..."
                  className="pl-8"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex h-[200px] items-center justify-center">
                <p className="text-muted-foreground">Loading runs...</p>
              </div>
            ) : error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-red-700">Error loading runs: {error.toString()}</p>
              </div>
            ) : runs?.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-8">
                <div className="rounded-full bg-primary/10 p-3">
                  <Play className="h-6 w-6 text-primary" />
                </div>
                <h2 className="mt-4 text-xl font-semibold">No workflow runs found</h2>
                <p className="mb-4 mt-2 text-center text-muted-foreground">
                  Start by running one of your workflows
                </p>
                <Button asChild>
                  <Link href="/workflows">
                    <Play className="mr-2 h-4 w-4" />
                    Go to Workflows
                  </Link>
                </Button>
              </div>
            ) : (
              <div className="relative w-full overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Workflow</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Run ID</TableHead>
                      <TableHead>Started</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead className="w-[80px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {runs?.map((run) => (
                      <TableRow key={run.id}>
                        <TableCell className="font-medium">
                          {run.workflow_name}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">v{run.workflow_version}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(run.status)}>
                            {run.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {run.run_id}
                        </TableCell>
                        <TableCell>
                          {formatDistanceToNow(new Date(run.start_time), {
                            addSuffix: true,
                          })}
                        </TableCell>
                        <TableCell>
                          {run.duration || '—'}
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" asChild>
                            <Link href={`/runs/${run.id}`}>
                              <ExternalLink className="h-4 w-4" />
                              <span className="sr-only">View</span>
                            </Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
} 