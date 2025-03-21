'use client';

import { AppLayout } from "@/components/layout/AppLayout";
import { useRuns } from "@/lib/api/hooks";
import Link from "next/link";
import { formatDistanceToNow } from 'date-fns';
import { Status } from "@/types/api";

// Helper function to get appropriate status badge color
const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case Status.COMPLETED:
      return 'bg-green-100 text-green-800';
    case Status.RUNNING:
      return 'bg-blue-100 text-blue-800';
    case Status.PENDING:
      return 'bg-yellow-100 text-yellow-800';
    case Status.FAILED:
    case Status.ERROR:
      return 'bg-red-100 text-red-800';
    case Status.TERMINATED_TIME_LIMIT:
      return 'bg-orange-100 text-orange-800';
    case Status.SKIPPED:
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export default function RunsPage() {
  const { data: runs, isLoading, error } = useRuns();

  return (
    <AppLayout>
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-semibold text-gray-900">Workflow Runs</h1>

          <div className="mt-8">
            {isLoading ? (
              <div className="text-center py-10">
                <p className="text-gray-500">Loading runs...</p>
              </div>
            ) : error ? (
              <div className="bg-red-50 p-4 rounded-md">
                <p className="text-red-700">Error loading runs: {error.toString()}</p>
              </div>
            ) : runs?.length === 0 ? (
              <div className="bg-white shadow overflow-hidden sm:rounded-md p-6 text-center">
                <p className="text-gray-500 mb-4">No workflow runs found</p>
                <Link
                  href="/workflows"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200"
                >
                  Go to workflows
                </Link>
              </div>
            ) : (
              <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                  {runs?.map((run) => (
                    <li key={run.id}>
                      <Link href={`/runs/${run.id}`} className="block hover:bg-gray-50">
                        <div className="px-4 py-4 sm:px-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <p className="text-lg font-medium text-blue-600 truncate">
                                {run.workflow_name}
                              </p>
                              <div className="ml-2 flex-shrink-0 flex">
                                <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                                  v{run.workflow_version}
                                </p>
                              </div>
                            </div>
                            <div className="ml-2 flex-shrink-0 flex">
                              <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(run.status)}`}>
                                {run.status}
                              </p>
                            </div>
                          </div>
                          <div className="mt-2 sm:flex sm:justify-between">
                            <div className="sm:flex">
                              <p className="flex items-center text-sm text-gray-500">
                                Run ID: {run.run_id}
                              </p>
                            </div>
                            <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                              <p>
                                Started{' '}
                                {formatDistanceToNow(new Date(run.start_time), {
                                  addSuffix: true,
                                })}
                              </p>
                              {run.duration && (
                                <p className="ml-4">
                                  Duration: {run.duration}
                                </p>
                              )}
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