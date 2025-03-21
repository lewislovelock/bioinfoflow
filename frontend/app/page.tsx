import { AppLayout } from "@/components/layout/AppLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Activity, ArrowRight, CheckCircle, Clock, Network, PlayCircle, XCircle } from "lucide-react";

export default function Dashboard() {
  // This would be fetched from backend in a real implementation
  const stats = {
    totalWorkflows: 12,
    activeRuns: 3,
    completedRuns: 18,
    failedRuns: 2,
  };

  // This would also be fetched from backend
  const recentActivities = [
    {
      id: 1,
      type: "run_completed",
      workflowName: "RNA-Seq Analysis",
      timestamp: "Today at 10:23 AM",
      status: "completed",
    },
    {
      id: 2,
      type: "run_started",
      workflowName: "Variant Calling Pipeline",
      timestamp: "Today at 09:15 AM",
      status: "running",
    },
    {
      id: 3,
      type: "workflow_created",
      workflowName: "Metagenomics Assembly",
      timestamp: "Yesterday at 2:45 PM",
      status: "none",
    },
    {
      id: 4,
      type: "run_failed",
      workflowName: "ChIP-Seq Analysis",
      timestamp: "Yesterday at 11:32 AM",
      status: "failed",
    },
  ];

  return (
    <AppLayout>
      <div className="flex flex-col gap-8">
        <div className="flex flex-col">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor your bioinformatics workflows and executions
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Workflows
              </CardTitle>
              <Network className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalWorkflows}</div>
              <p className="text-xs text-muted-foreground">
                Defined processing pipelines
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Active Runs
              </CardTitle>
              <PlayCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.activeRuns}</div>
              <p className="text-xs text-muted-foreground">
                Currently executing
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Completed Runs
              </CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.completedRuns}</div>
              <p className="text-xs text-muted-foreground">
                Successfully finished
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Failed Runs
              </CardTitle>
              <XCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.failedRuns}</div>
              <p className="text-xs text-muted-foreground">
                Terminated with errors
              </p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="activities" className="space-y-4">
          <TabsList>
            <TabsTrigger value="activities">Recent Activities</TabsTrigger>
            <TabsTrigger value="quick-actions">Quick Actions</TabsTrigger>
          </TabsList>
          <TabsContent value="activities" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activities</CardTitle>
                <CardDescription>
                  The latest events from your workflows and runs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivities.map((activity) => (
                    <div
                      key={activity.id}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        <div className="p-2 rounded-full bg-muted">
                          {activity.type === "run_completed" && (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          )}
                          {activity.type === "run_started" && (
                            <Clock className="h-4 w-4 text-blue-500" />
                          )}
                          {activity.type === "workflow_created" && (
                            <Network className="h-4 w-4 text-purple-500" />
                          )}
                          {activity.type === "run_failed" && (
                            <XCircle className="h-4 w-4 text-red-500" />
                          )}
                        </div>
                        <div>
                          <div className="font-medium">{activity.workflowName}</div>
                          <div className="text-sm text-muted-foreground">
                            {activity.timestamp}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {activity.status === "completed" && (
                          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                            Completed
                          </Badge>
                        )}
                        {activity.status === "running" && (
                          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                            Running
                          </Badge>
                        )}
                        {activity.status === "failed" && (
                          <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                            Failed
                          </Badge>
                        )}
                        <Button variant="outline" size="icon" asChild>
                          <Link href={activity.type.includes("run") ? `/runs/${activity.id}` : `/workflows/${activity.id}`}>
                            <ArrowRight className="h-4 w-4" />
                          </Link>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="quick-actions" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>
                  Common tasks for managing your workflows
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                <Link href="/workflows/new">
                  <div className="flex flex-col items-center gap-4 rounded-lg border p-4 hover:bg-accent">
                    <div className="p-2 rounded-full bg-primary/10">
                      <Network className="h-6 w-6 text-primary" />
                    </div>
                    <div className="text-center">
                      <h3 className="font-medium">Create New Workflow</h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        Define a new processing pipeline
                      </p>
                    </div>
                  </div>
                </Link>
                <Link href="/runs">
                  <div className="flex flex-col items-center gap-4 rounded-lg border p-4 hover:bg-accent">
                    <div className="p-2 rounded-full bg-primary/10">
                      <PlayCircle className="h-6 w-6 text-primary" />
                    </div>
                    <div className="text-center">
                      <h3 className="font-medium">View All Runs</h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        Monitor workflow executions
                      </p>
                    </div>
                  </div>
                </Link>
                <Link href="/workflows">
                  <div className="flex flex-col items-center gap-4 rounded-lg border p-4 hover:bg-accent">
                    <div className="p-2 rounded-full bg-primary/10">
                      <Activity className="h-6 w-6 text-primary" />
                    </div>
                    <div className="text-center">
                      <h3 className="font-medium">Browse Workflows</h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        See all available pipelines
                      </p>
                    </div>
                  </div>
                </Link>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
