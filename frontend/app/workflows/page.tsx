'use client';

import { AppLayout } from "@/components/layout/AppLayout";
import { useWorkflows } from "@/lib/api/hooks";
import Link from "next/link";
import { formatDistanceToNow } from 'date-fns';

export default function WorkflowsPage() {
  const { data: workflows, isLoading, error } = useWorkflows();

  return (
    <AppLayout>
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-semibold text-gray-900">Workflows</h1>
            <Link
              href="/workflows/new"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            >
              Create Workflow
            </Link>
          </div>

          <div className="mt-8">
            {isLoading ? (
              <div className="text-center py-10">
                <p className="text-gray-500">Loading workflows...</p>
              </div>
            ) : error ? (
              <div className="bg-red-50 p-4 rounded-md">
                <p className="text-red-700">Error loading workflows: {error.toString()}</p>
              </div>
            ) : workflows?.length === 0 ? (
              <div className="bg-white shadow overflow-hidden sm:rounded-md p-6 text-center">
                <p className="text-gray-500 mb-4">No workflows found</p>
                <Link
                  href="/workflows/new"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200"
                >
                  Create your first workflow
                </Link>
              </div>
            ) : (
              <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                  {workflows?.map((workflow) => (
                    <li key={workflow.id}>
                      <Link href={`/workflows/${workflow.id}`} className="block hover:bg-gray-50">
                        <div className="px-4 py-4 sm:px-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <p className="text-lg font-medium text-blue-600 truncate">
                                {workflow.name}
                              </p>
                              <div className="ml-2 flex-shrink-0 flex">
                                <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                                  v{workflow.version}
                                </p>
                              </div>
                            </div>
                            <div className="ml-2 flex-shrink-0 flex">
                              <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                {workflow.run_count} runs
                              </p>
                            </div>
                          </div>
                          <div className="mt-2 sm:flex sm:justify-between">
                            <div className="sm:flex">
                              <p className="flex items-center text-sm text-gray-500">
                                {workflow.description || 'No description'}
                              </p>
                            </div>
                            <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                              <p>
                                Created{' '}
                                {formatDistanceToNow(new Date(workflow.created_at), {
                                  addSuffix: true,
                                })}
                              </p>
                            </div>
                          </div>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
} 