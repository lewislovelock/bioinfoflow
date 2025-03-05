import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";

// Feature card component
function FeatureCard({ 
  title, 
  description, 
  icon 
}: { 
  title: string; 
  description: string; 
  icon: React.ReactNode;
}) {
  return (
    <Card className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="flex flex-row items-center gap-4 pb-2">
        <div className="bg-blue-50 p-2 rounded-full">{icon}</div>
        <CardTitle className="text-xl">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription className="text-gray-600">{description}</CardDescription>
      </CardContent>
    </Card>
  );
}

// Step card component for How It Works section
function StepCard({ 
  number, 
  title, 
  description 
}: { 
  number: number; 
  title: string; 
  description: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold">
        {number}
      </div>
      <div>
        <h3 className="font-semibold text-lg">{title}</h3>
        <p className="text-gray-600">{description}</p>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main>
        {/* Hero Section */}
        <section className="py-20 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-indigo-50 -z-10"></div>
          <div className="absolute inset-0 opacity-20 -z-10">
            <svg width="100%" height="100%" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                  <path d="M 10 0 L 0 0 0 10" fill="none" stroke="blue" strokeWidth="0.5" opacity="0.2" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
            </svg>
          </div>
          
          <div className="container mx-auto px-4 flex flex-col items-center text-center">
            <h1 className="text-5xl md:text-6xl font-bold mb-6 tracking-tight">
              BioinfoFlow: Simplifying Bioinformatics Workflows
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mb-10">
              Run, manage, and visualize your bioinformatics pipelines with ease.
            </p>
            <div className="flex gap-4">
              <Button size="lg" className="bg-blue-500 hover:bg-blue-600" asChild>
                <Link href="#get-started">Get Started</Link>
              </Button>
              <Button variant="outline" size="lg" asChild>
                <Link href="#features">Learn More</Link>
              </Button>
            </div>
            
            <div className="mt-16 max-w-5xl w-full p-4 rounded-xl bg-white/60 backdrop-blur shadow-xl">
              <Image 
                src="/workflow-example.svg" 
                alt="Workflow Visualization Example" 
                width={900} 
                height={500}
                className="rounded-lg border border-gray-200"
                priority
              />
            </div>
          </div>
        </section>

        <Separator />

        {/* Features Section */}
        <section id="features" className="py-20">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Powerful Features</h2>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <FeatureCard 
                title="Workflow Management" 
                description="Define and execute workflows with a simple YAML configuration."
                icon={
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500">
                    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                }
              />
              
              <FeatureCard 
                title="Visualization" 
                description="See your workflow steps and dependencies at a glance."
                icon={
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <line x1="3" y1="9" x2="21" y2="9"/>
                    <line x1="9" y1="21" x2="9" y2="9"/>
                  </svg>
                }
              />
              
              <FeatureCard 
                title="Containerized Execution" 
                description="Run analyses in isolated, reproducible environments."
                icon={
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                  </svg>
                }
              />
              
              <FeatureCard 
                title="Input/Output Handling" 
                description="Easily manage your data inputs and outputs."
                icon={
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
                  </svg>
                }
              />
            </div>
          </div>
        </section>

        <Separator />

        {/* How It Works Section */}
        <section id="how-it-works" className="py-20 bg-gray-50">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
            
            <div className="max-w-3xl mx-auto space-y-8">
              <StepCard 
                number={1} 
                title="Create a workflow using YAML" 
                description="Define your workflow steps, dependencies, and resources using a simple YAML configuration."
              />
              
              <StepCard 
                number={2} 
                title="Configure inputs via simple forms" 
                description="Specify input data paths and parameters through an intuitive web interface."
              />
              
              <StepCard 
                number={3} 
                title="Run and monitor your pipeline" 
                description="Execute your workflow and track its progress in real-time with detailed logs and status updates."
              />
              
              <StepCard 
                number={4} 
                title="View and download results" 
                description="Access, visualize, and download your analysis results through the web UI."
              />
            </div>
            
            <div className="mt-12 text-center">
              <Button size="lg" className="bg-blue-500 hover:bg-blue-600" id="get-started" asChild>
                <Link href="/docs">Get Started</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
