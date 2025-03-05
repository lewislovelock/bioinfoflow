"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export function Header() {
  const pathname = usePathname();
  
  return (
    <header className="border-b sticky top-0 bg-white/80 backdrop-blur-sm z-10">
      <div className="container mx-auto py-4 flex justify-between items-center">
        <Link href="/" className="flex items-center gap-2">
          <div className="bg-blue-500 text-white p-1 rounded">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 9a3 3 0 0 1 0 6v-6Z" /><path d="M14 4a6 6 0 0 1 0 16" />
              <path d="M22 9a3 3 0 0 0 0 6v-6Z" /><path d="M10 4a6 6 0 0 0 0 16" />
            </svg>
          </div>
          <span className="font-bold text-xl">BioinfoFlow</span>
        </Link>
        
        {/* Desktop Navigation */}
        <nav className="hidden md:flex gap-8">
          <Link 
            href="/#features" 
            className={`${pathname === "/" ? "text-gray-900" : "text-gray-600 hover:text-gray-900"}`}
          >
            Features
          </Link>
          <Link 
            href="/#how-it-works" 
            className={`${pathname === "/" ? "text-gray-900" : "text-gray-600 hover:text-gray-900"}`}
          >
            How It Works
          </Link>
          <Link 
            href="https://github.com/lewislovelock/bioinfoflow" 
            className="text-gray-600 hover:text-gray-900"
          >
            GitHub
          </Link>
          <Link 
            href="/docs" 
            className={`${pathname.startsWith("/docs") ? "text-gray-900 font-semibold" : "text-gray-600 hover:text-gray-900"}`}
          >
            Documentation
          </Link>
        </nav>
        
        <div className="flex items-center gap-4">
          {/* CTA Button */}
          <div className="hidden sm:block">
            {pathname === "/" ? (
              <Button className="bg-blue-500 hover:bg-blue-600" asChild>
                <Link href="#get-started">Get Started</Link>
              </Button>
            ) : (
              <Button className="bg-blue-500 hover:bg-blue-600" asChild>
                <Link href="/">Back to Home</Link>
              </Button>
            )}
          </div>
          
          {/* Mobile Menu */}
          <div className="md:hidden">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon" className="h-9 w-9">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="4" x2="20" y1="12" y2="12" />
                    <line x1="4" x2="20" y1="6" y2="6" />
                    <line x1="4" x2="20" y1="18" y2="18" />
                  </svg>
                  <span className="sr-only">Toggle menu</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="right">
                <div className="flex flex-col gap-6 mt-8">
                  <Link 
                    href="/#features" 
                    className="text-lg font-medium"
                  >
                    Features
                  </Link>
                  <Link 
                    href="/#how-it-works" 
                    className="text-lg font-medium"
                  >
                    How It Works
                  </Link>
                  <Link 
                    href="https://github.com/lewislovelock/bioinfoflow" 
                    className="text-lg font-medium"
                  >
                    GitHub
                  </Link>
                  <Link 
                    href="/docs" 
                    className="text-lg font-medium"
                  >
                    Documentation
                  </Link>
                  
                  {pathname === "/" ? (
                    <Button className="bg-blue-500 hover:bg-blue-600 mt-4" asChild>
                      <Link href="#get-started">Get Started</Link>
                    </Button>
                  ) : (
                    <Button className="bg-blue-500 hover:bg-blue-600 mt-4" asChild>
                      <Link href="/">Back to Home</Link>
                    </Button>
                  )}
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
} 