import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";

export default function DocsPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="flex-1">
        <div className="container mx-auto py-12 px-4">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-4xl font-bold mb-8">BioinfoFlow Documentation</h1>
            
            <article className="prose lg:prose-xl max-w-none prose-headings:text-gray-900 prose-a:text-blue-600">
              <h2>Getting Started</h2>
              <p>
                BioinfoFlow is a bioinformatics workflow engine designed for reproducible, 
                container-native data analysis pipelines. This documentation will help you 
                get started with creating and running workflows.
              </p>
              
              <h3>Installation</h3>
              <p>You can install BioinfoFlow using pip:</p>
              <pre>
                <code>pip install git+https://github.com/lewislovelock/bioinfoflow.git</code>
              </pre>
              
              <h3>Creating Your First Workflow</h3>
              <p>
                To create a new workflow, you can use the init command:
              </p>
              <pre>
                <code>bioinfoflow init my_workflow --output my_workflow.yaml</code>
              </pre>
              
              <p>
                This will create a template workflow file that you can customize. Here's an example 
                of a simple workflow definition:
              </p>
              
              <pre>
                <code>{`name: simple_workflow
version: "1.0.0"
description: "A simple workflow example"

inputs:
  path: "input/*.txt"

steps:
  hello_world:
    container: "ubuntu:20.04"
    command: "echo 'Hello, BioinfoFlow!' > \${run_dir}/outputs/hello.txt"
    resources:
      cpu: 1
      memory: "1G"
    after: []

  count_words:
    container: "ubuntu:20.04"
    command: "wc -w \${run_dir}/outputs/hello.txt > \${run_dir}/outputs/word_count.txt"
    resources:
      cpu: 1
      memory: "1G"
    after: [hello_world]`}</code>
              </pre>
              
              <h3>Running a Workflow</h3>
              <p>
                To run a workflow, use the run command:
              </p>
              <pre>
                <code>bioinfoflow run my_workflow.yaml</code>
              </pre>
              
              <p>
                You can also specify input paths directly via command line:
              </p>
              <pre>
                <code>bioinfoflow run my_workflow.yaml --input path=/path/to/your/input/*.fastq.gz</code>
              </pre>
              
              <h3>Checking Workflow Status</h3>
              <p>
                To list all workflow runs:
              </p>
              <pre>
                <code>bioinfoflow list</code>
              </pre>
              
              <p>
                To check the status of a specific run:
              </p>
              <pre>
                <code>bioinfoflow status &lt;run_id&gt;</code>
              </pre>
              
              <h2>Advanced Topics</h2>
              <p>
                For more advanced usage, please refer to the following sections:
              </p>
              
              <ul>
                <li>Variable Substitution</li>
                <li>Resource Allocation</li>
                <li>Dependency Management</li>
                <li>Container Configuration</li>
                <li>Error Handling</li>
              </ul>
              
              <p>
                These topics will be covered in detail in upcoming documentation updates.
              </p>
            </article>
            
            <Separator className="my-8" />
            
            <div className="text-center">
              <p className="mb-4">Ready to try BioinfoFlow?</p>
              <Button size="lg" className="bg-blue-500 hover:bg-blue-600" asChild>
                <Link href="https://github.com/lewislovelock/bioinfoflow">View on GitHub</Link>
              </Button>
            </div>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
} 