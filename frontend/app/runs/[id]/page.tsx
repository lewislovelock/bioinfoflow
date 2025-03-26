'use client';

import { AppLayout } from "@/components/layout/AppLayout";
import { useRun, useRunLogs, useCancelRun, useResumeRun } from "@/lib/api/hooks";
import { Status } from "@/types/api";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { useState, use } from "react";

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

interface RunDetailPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function RunDetailPage({ params }: RunDetailPageProps) {
  const unwrappedParams = use(params);
  const runId = unwrappedParams.id;
  const [selectedStep, setSelectedStep] = useState<string | null>(null);

  const { data: run, isLoading, error } = useRun(runId);
  const { data: logs } = useRunLogs(runId, selectedStep || '');
  
  const cancelRunMutation = useCancelRun();
  const resumeRunMutation = useResumeRun();

  const handleCancelRun = async () => {
    if (window.confirm('Are you sure you want to cancel this run?')) {
      try {
        await cancelRunMutation.mutateAsync(runId);
      } catch (error) {
        console.error('Failed to cancel run:', error);
      }
    }
  };

  const handleResumeRun = async () => {
    try {
      await resumeRunMutation.mutateAsync({
        runId,
        params: {
          parallel: 1,
          enable_time_limits: false
        }
      });
    } catch (error) {
      console.error('Failed to resume run:', error);
    }
  };

  if (isLoading) {
    return (
      <AppLayout>
        <div className="py-6 text-center">
          <p className="text-gray-500">Loading run details...</p>
        </div>
      </AppLayout>
    );
  }

  if (error) {
    return (
      <AppLayout>
        <div className="py-6">
          <div className="bg-red-50 p-4 rounded-md">
            <p className="text-red-700">Error loading run details: {error.toString()}</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (!run) {
    return (
      <AppLayout>
        <div className="py-6">
          <div className="bg-yellow-50 p-4 rounded-md">
            <p className="text-yellow-700">Run not found</p>
            <Link
              href="/runs"
              className="mt-4 inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200"
            >
              Back to runs
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
              <div className="flex items-center">
                <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                  {run.workflow_name}
                </h2>
                <span className="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                  v{run.workflow_version}
                </span>
                <span className={`ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(run.status)}`}>
                  {run.status}
                </span>
              </div>
              <div className="mt-1 flex flex-col sm:flex-row sm:flex-wrap sm:mt-0 sm:space-x-6">
                <div className="mt-2 flex items-center text-sm text-gray-500">
                  Run ID: {run.run_id}
                </div>
                <div className="mt-2 flex items-center text-sm text-gray-500">
                  Started {formatDistanceToNow(new Date(run.start_time), { addSuffix: true })}
                </div>
                {run.duration && (
                  <div className="mt-2 flex items-center text-sm text-gray-500">
                    Duration: {run.duration}
                  </div>
                )}
              </div>
            </div>
            <div className="mt-4 flex md:mt-0 md:ml-4">
              <Link
                href={`/workflows/${run.workflow_id}`}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                View Workflow
              </Link>
              {run.status === Status.FAILED && (
                <button
                  type="button"
                  onClick={handleResumeRun}
                  disabled={resumeRunMutation.isPending}
                  className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  {resumeRunMutation.isPending ? 'Resuming...' : 'Resume Run'}
                </button>
              )}
              {run.status === Status.RUNNING && (
                <button
                  type="button"
                  onClick={handleCancelRun}
                  disabled={cancelRunMutation.isPending}
                  className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  {cancelRunMutation.isPending ? 'Cancelling...' : 'Cancel Run'}
                </button>
              )}
            </div>
          </div>

          {run.inputs && Object.keys(run.inputs).length > 0 && (
            <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">Inputs</h3>
              </div>
              <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
                <dl className="sm:divide-y sm:divide-gray-200">
                  {Object.entries(run.inputs).map(([key, value]) => (
                    <div key={key} className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                      <dt className="text-sm font-medium text-gray-500">{key}</dt>
                      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                        {typeof value === 'string' ? value : JSON.stringify(value)}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
          )}

          <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Steps</h3>
            </div>
            <div className="border-t border-gray-200">
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th
                        scope="col"
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Step Name
                      </th>
                      <th
                        scope="col"
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Status
                      </th>
                      <th
                        scope="col"
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Start Time
                      </th>
                      <th
                        scope="col"
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Duration
                      </th>
                      <th
                        scope="col"
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Exit Code
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {Object.entries(run.steps).map(([stepName, step]) => (
                      <tr 
                        key={stepName} 
                        className={`cursor-pointer hover:bg-gray-50 ${selectedStep === stepName ? 'bg-blue-50' : ''}`}
                        onClick={() => setSelectedStep(stepName)}
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {step.step_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(step.status)}`}>
                            {step.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {step.start_time ? formatDistanceToNow(new Date(step.start_time), { addSuffix: true }) : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {step.duration || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {step.exit_code !== undefined ? step.exit_code : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {selectedStep && run.steps[selectedStep] && (
            <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Logs for step: {selectedStep}
                </h3>
              </div>
              <div className="border-t border-gray-200">
                <div className="p-4">
                  {run.steps[selectedStep].error ? (
                    <div className="bg-red-50 p-4 rounded mb-4">
                      <p className="text-red-700">{run.steps[selectedStep].error}</p>
                    </div>
                  ) : null}
                  
                  {logs ? (
                    <pre className="bg-gray-100 p-4 rounded-md overflow-x-auto whitespace-pre-wrap text-sm font-mono">
                      {logs}
                    </pre>
                  ) : (
                    <p className="text-gray-500">No logs available</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
} 