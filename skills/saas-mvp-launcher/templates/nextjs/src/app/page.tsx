export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8">{{PROJECT_NAME}}</h1>
        <p className="text-xl mb-4">
          Next.js 15 + React 19 + TypeScript
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
          <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
            <h2 className="mb-3 text-2xl font-semibold">
              Features
            </h2>
            <ul className="m-0 max-w-[30ch] text-sm opacity-50 list-disc pl-4">
              <li>TypeScript</li>
              <li>Tailwind CSS</li>
              <li>App Router</li>
              <li>Server Components</li>
            </ul>
          </div>
          <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
            <h2 className="mb-3 text-2xl font-semibold">
              Get Started
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              Edit src/app/page.tsx to customize this page.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
