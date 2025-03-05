import Link from "next/link";

export function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12 mt-auto">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-xl font-semibold mb-4">BioinfoFlow</h3>
            <p className="text-gray-400">
              A bioinformatics workflow engine designed for reproducible, container-native data analysis pipelines.
            </p>
          </div>
          
          <div>
            <h3 className="text-xl font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li><Link href="/docs" className="text-gray-400 hover:text-white">Documentation</Link></li>
              <li><Link href="https://github.com/lewislovelock/bioinfoflow" className="text-gray-400 hover:text-white">GitHub</Link></li>
              <li><Link href="/#features" className="text-gray-400 hover:text-white">Features</Link></li>
              <li><Link href="/#how-it-works" className="text-gray-400 hover:text-white">How It Works</Link></li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-xl font-semibold mb-4">Contact</h3>
            <p className="text-gray-400">
              Have questions or feedback? <br />
              <a href="mailto:info@bioinfoflow.io" className="text-blue-400 hover:text-blue-300">info@bioinfoflow.io</a>
            </p>
          </div>
        </div>
        
        <div className="mt-8 pt-8 border-t border-gray-800 text-center text-gray-500">
          <p>&copy; {new Date().getFullYear()} BioinfoFlow. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
} 