import { AppLayout } from "@/components/layout/AppLayout";
import Link from "next/link";

export default function Home() {
  return (
    <AppLayout>
      <div className="py-10">
        <header>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold leading-tight text-gray-900">
              Welcome to BioinfoFlow
            </h1>
          </div>
        </header>
        <main>
          <div className="max-w-7xl mx-auto sm:px-6 lg:px-8">
            <div className="px-4 py-8 sm:px-0">
              <div className="border-4 border-dashed border-gray-200 rounded-lg p-6 bg-white">
                <p className="text-lg text-gray-600 mb-6">
                  BioinfoFlow is a modern workflow manager for bioinformatics,
                  designed to help you manage complex analysis pipelines.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-blue-50 p-6 rounded-lg">
                    <h2 className="text-xl font-semibold text-blue-700 mb-2">
                      Workflows
                    </h2>
                    <p className="mb-4">
                      Create, manage, and run your bioinformatics workflows with ease.
                    </p>
                    <Link
                      href="/workflows"
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                    >
                      Browse Workflows
                    </Link>
                  </div>
                  <div className="bg-green-50 p-6 rounded-lg">
                    <h2 className="text-xl font-semibold text-green-700 mb-2">
                      Runs
                    </h2>
                    <p className="mb-4">
                      View and manage your workflow executions, monitor progress,
                      and access results.
                    </p>
                    <Link
                      href="/runs"
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700"
                    >
                      View Runs
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </AppLayout>
  );
}
