'use client';

import { AppLayout } from "@/components/layout/AppLayout";
import { useCreateWorkflow } from "@/lib/api/hooks";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function CreateWorkflowPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [version, setVersion] = useState('1.0.0');
  const [description, setDescription] = useState('');
  const [yamlContent, setYamlContent] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const createWorkflowMutation = useCreateWorkflow();

  const handleSubmit = async (e: React.FormEvent) => {
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
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="md:flex md:items-center md:justify-between">
            <div className="flex-1 min-w-0">
              <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                Create New Workflow
              </h2>
            </div>
            <div className="mt-4 flex md:mt-0 md:ml-4">
              <Link
                href="/workflows"
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </Link>
            </div>
          </div>

          <div className="mt-6 bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
            {formError && (
              <div className="mb-4 bg-red-50 p-4 rounded-md">
                <p className="text-red-700">{formError}</p>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="space-y-6">
                <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                  <div className="sm:col-span-3">
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                      Workflow Name
                    </label>
                    <div className="mt-1">
                      <input
                        type="text"
                        name="name"
                        id="name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder="e.g., DNA Alignment Pipeline"
                      />
                    </div>
                  </div>

                  <div className="sm:col-span-3">
                    <label htmlFor="version" className="block text-sm font-medium text-gray-700">
                      Version
                    </label>
                    <div className="mt-1">
                      <input
                        type="text"
                        name="version"
                        id="version"
                        value={version}
                        onChange={(e) => setVersion(e.target.value)}
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder="e.g., 1.0.0"
                      />
                    </div>
                  </div>

                  <div className="sm:col-span-6">
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                      Description
                    </label>
                    <div className="mt-1">
                      <textarea
                        id="description"
                        name="description"
                        rows={3}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border border-gray-300 rounded-md"
                        placeholder="Describe what this workflow does..."
                      />
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                      Brief description of the workflow purpose and functionality.
                    </p>
                  </div>

                  <div className="sm:col-span-6">
                    <label htmlFor="yaml-content" className="block text-sm font-medium text-gray-700">
                      Workflow YAML
                    </label>
                    <div className="mt-1">
                      <textarea
                        id="yaml-content"
                        name="yaml-content"
                        rows={12}
                        value={yamlContent}
                        onChange={(e) => setYamlContent(e.target.value)}
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border border-gray-300 rounded-md font-mono"
                        placeholder="Paste your workflow YAML here..."
                      />
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                      Paste your workflow YAML definition here. The YAML should define the workflow steps,
                      their dependencies, container images, and commands.
                    </p>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => router.push('/workflows')}
                    className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createWorkflowMutation.isPending}
                    className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    {createWorkflowMutation.isPending ? 'Creating...' : 'Create Workflow'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </AppLayout>
  );
} 