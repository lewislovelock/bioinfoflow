'use client';

import { AppLayout } from "@/components/layout/AppLayout";
import { useCreateWorkflow } from "@/lib/api/hooks";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ChangeEvent, FormEvent } from "react";

export default function CreateWorkflowPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [version, setVersion] = useState('1.0.0');
  const [description, setDescription] = useState('');
  const [yamlContent, setYamlContent] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const createWorkflowMutation = useCreateWorkflow();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError(null);

    if (!name.trim()) {
      setFormError('Workflow name is required');
      return;
    }

    if (!version.trim()) {
      setFormError('Version is required');
      return;
    }

    if (!yamlContent.trim()) {
      setFormError('Workflow YAML content is required');
      return;
    }

    try {
      const result = await createWorkflowMutation.mutateAsync({
        name,
        version,
        description,
        yaml_content: yamlContent,
      });
      
      // Navigate to the workflow detail page
      router.push(`/workflows/${result.id}`);
    } catch (error) {
      console.error("Error creating workflow:", error);
      setFormError(`Failed to create workflow: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  return (
    <AppLayout>
      <div className="flex flex-col gap-8">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" onClick={() => router.push('/workflows')}>
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <h1 className="text-3xl font-bold tracking-tight">Create Workflow</h1>
            </div>
            <p className="text-muted-foreground">
              Define a new bioinformatics workflow pipeline
            </p>
          </div>
        </div>

        {formError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              {formError}
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>Workflow Information</CardTitle>
              <CardDescription>
                Provide basic information about your workflow
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name">Workflow Name</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
                    placeholder="e.g., RNA-Seq Analysis Pipeline"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="version">Version</Label>
                  <Input
                    id="version"
                    value={version}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setVersion(e.target.value)}
                    placeholder="e.g., 1.0.0"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setDescription(e.target.value)}
                  placeholder="Describe what this workflow does..."
                  rows={3}
                />
                <p className="text-sm text-muted-foreground">
                  Provide a clear description of the workflow's purpose and functionality.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="yaml-content">Workflow YAML Definition</Label>
                <Textarea
                  id="yaml-content"
                  value={yamlContent}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setYamlContent(e.target.value)}
                  placeholder="Paste your workflow YAML here..."
                  className="font-mono h-[300px]"
                />
                <p className="text-sm text-muted-foreground">
                  Paste your workflow YAML definition. This should define the workflow steps,
                  their dependencies, container images, and commands.
                </p>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Button 
                variant="outline" 
                onClick={() => router.push('/workflows')}
              >
                Cancel
              </Button>
              <Button 
                type="submit"
                disabled={createWorkflowMutation.isPending}
              >
                {createWorkflowMutation.isPending ? 'Creating...' : 'Create Workflow'}
              </Button>
            </CardFooter>
          </Card>
        </form>
      </div>
    </AppLayout>
  );
} 