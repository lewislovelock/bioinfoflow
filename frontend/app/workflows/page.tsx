'use client';

import { AppLayout } from "@/components/layout/AppLayout";
import { useWorkflows } from "@/lib/api/hooks";
import Link from "next/link";
import { formatDistanceToNow } from 'date-fns';
import { Network, Plus, Search, ExternalLink } from "lucide-react";
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

export default function WorkflowsPage() {
  const { data: workflows, isLoading, error } = useWorkflows();

  return (
    <AppLayout>
      <div className="flex flex-col gap-8">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Workflows</h1>
            <p className="text-muted-foreground">
              Manage your bioinformatics processing pipelines
            </p>
          </div>
          <Button asChild>
            <Link href="/workflows/new">
              <Plus className="mr-2 h-4 w-4" />
              Create Workflow
            </Link>
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>All Workflows</CardTitle>
            <CardDescription>
              Browse and manage your defined workflow pipelines
            </CardDescription>
            <div className="flex items-center gap-2 pt-4">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search workflows..."
                  className="pl-8"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex h-[200px] items-center justify-center">
                <p className="text-muted-foreground">Loading workflows...</p>
              </div>
            ) : error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-red-700">Error loading workflows: {error.toString()}</p>
              </div>
            ) : workflows?.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-8">
                <div className="rounded-full bg-primary/10 p-3">
                  <Network className="h-6 w-6 text-primary" />
                </div>
                <h2 className="mt-4 text-xl font-semibold">No workflows found</h2>
                <p className="mb-4 mt-2 text-center text-muted-foreground">
                  Get started by creating your first workflow pipeline
                </p>
                <Button asChild>
                  <Link href="/workflows/new">
                    <Plus className="mr-2 h-4 w-4" />
                    Create Workflow
                  </Link>
                </Button>
              </div>
            ) : (
              <div className="relative w-full overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Runs</TableHead>
                      <TableHead className="w-[80px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {workflows?.map((workflow) => (
                      <TableRow key={workflow.id}>
                        <TableCell className="font-medium">
                          {workflow.name}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">v{workflow.version}</Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {workflow.description || 'No description'}
                        </TableCell>
                        <TableCell>
                          {formatDistanceToNow(new Date(workflow.created_at), {
                            addSuffix: true,
                          })}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">
                            {workflow.run_count} runs
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" asChild>
                            <Link href={`/workflows/${workflow.id}`}>
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