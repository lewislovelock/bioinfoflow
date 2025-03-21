'use client';

import { AppLayout } from "@/components/layout/AppLayout";
import { useWorkflow, useRunWorkflow } from "@/lib/api/hooks";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";

interface WorkflowDetailPageProps {
  params: {
    id: string;
  };
}

export default function WorkflowDetailPage({ params }: WorkflowDetailPageProps) {
  const workflowId = parseInt(params.id, 10);
  const router = useRouter();
  const [isRunModalOpen, setIsRunModalOpen] = useState(false);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [parallelism, setParallelism] = useState(1);
  const [enableTimeLimit, setEnableTimeLimit] = useState(false);
  const [defaultTimeLimit, setDefaultTimeLimit] = useState("1h");

  const { data: workflow, isLoading, error } = useWorkflow(workflowId);
  const runWorkflowMutation = useRunWorkflow();

  const handleRunWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const result = await runWorkflowMutation.mutateAsync({
        workflowId,
        params: {
          inputs,
          parallel: parallelism,
          enable_time_limits: enableTimeLimit,
          default_time_limit: defaultTimeLimit,
        },
      });
      
      setIsRunModalOpen(false);
      // Navigate to the run detail page
      router.push(`/runs/${result.id}`);
    } catch (error) {
      console.error("Failed to run workflow:", error);
    }
  };

  if (isLoading) {
    return (
      <AppLayout>
        <div className="py-6 text-center">
          <p className="text-gray-500">Loading workflow...</p>
        </div>
      </AppLayout>
    );
  }

  if (error) {
    return (
      <AppLayout>
        <div className="py-6">
          <div className="bg-red-50 p-4 rounded-md">
            <p className="text-red-700">Error loading workflow: {error.toString()}</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (!workflow) {
    return (
      <AppLayout>
        <div className="py-6">
          <div className="bg-yellow-50 p-4 rounded-md">
            <p className="text-yellow-700">Workflow not found</p>
            <Link
              href="/workflows"
              className="mt-4 inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200"
            >
              Back to workflows
            </Link>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="md:flex md:items-center md:justify-between">
            <div className="flex-1 min-w-0">
              <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                {workflow.name}
                <span className="ml-2 text-sm font-medium text-gray-500">
                  v{workflow.version}
                </span>
              </h2>
              <div className="mt-1 flex flex-col sm:flex-row sm:flex-wrap sm:mt-0 sm:space-x-6">
                <div className="mt-2 flex items-center text-sm text-gray-500">
                  Created {formatDistanceToNow(new Date(workflow.created_at), { addSuffix: true })}
                </div>
                <div className="mt-2 flex items-center text-sm text-gray-500">
                  {workflow.run_count} runs
                </div>
              </div>
            </div>
            <div className="mt-4 flex md:mt-0 md:ml-4">
              <button
                type="button"
                onClick={() => setIsRunModalOpen(true)}
                className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Run Workflow
              </button>
            </div>
          </div>

          {workflow.description && (
            <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">Description</h3>
              </div>
              <div className="border-t border-gray-200">
                <div className="px-4 py-5 sm:p-6 whitespace-pre-line">{workflow.description}</div>
              </div>
            </div>
          )}

          <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Steps</h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">Workflow execution steps</p>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
              <dl className="sm:divide-y sm:divide-gray-200">
                {Object.entries(workflow.steps).map(([stepName, step]) => (
                  <div key={stepName} className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">{stepName}</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      <div className="mb-2">
                        <span className="font-semibold">Container: </span>
                        {step.container}
                      </div>
                      <div className="mb-2">
                        <span className="font-semibold">Command: </span>
                        <code className="bg-gray-100 px-2 py-1 rounded font-mono text-sm">
                          {step.command}
                        </code>
                      </div>
                      {step.resources && Object.keys(step.resources).length > 0 && (
                        <div className="mb-2">
                          <span className="font-semibold">Resources: </span>
                          <ul className="list-disc list-inside pl-2">
                            {step.resources.cpu && (
                              <li>CPU: {step.resources.cpu}</li>
                            )}
                            {step.resources.memory && (
                              <li>Memory: {step.resources.memory}</li>
                            )}
                            {step.resources.time_limit && (
                              <li>Time limit: {step.resources.time_limit}</li>
                            )}
                          </ul>
                        </div>
                      )}
                      {step.after && step.after.length > 0 && (
                        <div>
                          <span className="font-semibold">Depends on: </span>
                          {step.after.join(', ')}
                        </div>
                      )}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Run workflow modal */}
      {isRunModalOpen && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                      Run Workflow
                    </h3>
                    <div className="mt-4">
                      <form onSubmit={handleRunWorkflow}>
                        <div className="mb-4">
                          <label htmlFor="parallelism" className="block text-sm font-medium text-gray-700">
                            Parallelism
                          </label>
                          <input
                            type="number"
                            name="parallelism"
                            id="parallelism"
                            min="1"
                            value={parallelism}
                            onChange={(e) => setParallelism(parseInt(e.target.value, 10))}
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          />
                        </div>

                        <div className="mb-4">
                          <div className="flex items-start">
                            <div className="flex items-center h-5">
                              <input
                                id="enableTimeLimit"
                                name="enableTimeLimit"
                                type="checkbox"
                                checked={enableTimeLimit}
                                onChange={(e) => setEnableTimeLimit(e.target.checked)}
                                className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                              />
                            </div>
                            <div className="ml-3 text-sm">
                              <label htmlFor="enableTimeLimit" className="font-medium text-gray-700">
                                Enable time limits
                              </label>
                            </div>
                          </div>
                        </div>

                        {enableTimeLimit && (
                          <div className="mb-4">
                            <label htmlFor="defaultTimeLimit" className="block text-sm font-medium text-gray-700">
                              Default time limit
                            </label>
                            <input
                              type="text"
                              name="defaultTimeLimit"
                              id="defaultTimeLimit"
                              value={defaultTimeLimit}
                              onChange={(e) => setDefaultTimeLimit(e.target.value)}
                              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                              placeholder="1h, 30m, etc."
                            />
                          </div>
                        )}

                        {/* Input fields based on workflow requirements could be added here */}
                        
                        <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                          <button
                            type="submit"
                            className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                            disabled={runWorkflowMutation.isPending}
                          >
                            {runWorkflowMutation.isPending ? 'Running...' : 'Run'}
                          </button>
                          <button
                            type="button"
                            className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm"
                            onClick={() => setIsRunModalOpen(false)}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
} 