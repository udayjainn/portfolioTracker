import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center py-20 text-center">
      <h1 className="text-6xl font-bold text-gray-200">404</h1>
      <p className="mt-4 text-lg text-gray-600">Page not found</p>
      <Link href="/" className="mt-6 rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700">
        Go Home
      </Link>
    </div>
  );
}
