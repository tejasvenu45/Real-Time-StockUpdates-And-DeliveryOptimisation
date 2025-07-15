import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="bg-gray-800 shadow-md py-3 px-6 flex items-center justify-between">
      <div className="bg-blue-300  px-4 py-2 rounded-lg font-bold text-lg shadow-sm">
        Advanced Warehouse Management System
      </div>

      <div className="flex gap-4">
        <Link href="/">
          <div className="bg-blue-600 text-white px-4 py-2 rounded-md shadow hover:bg-blue-700 transition">
            Home
          </div>
        </Link>
        <Link href="/dashboard">
          <div className="bg-blue-600 text-white px-4 py-2 rounded-md shadow hover:bg-blue-700 transition">
            Dashboard
          </div>
        </Link>

        <Link href="/vehicle">
          <div className="bg-blue-600 text-white px-4 py-2 rounded-md shadow hover:bg-blue-700 transition">
            Vehicles
          </div>
        </Link>

        <Link href="/process">
          <div className="bg-blue-600 text-white px-4 py-2 rounded-md shadow hover:bg-blue-700 transition">
            Process
          </div>
        </Link>

        <Link href="/store">
          <div className="bg-blue-600 text-white px-4 py-2 rounded-md shadow hover:bg-blue-700 transition">
            Stores
          </div>
        </Link>
      </div>
    </nav>
  );
}
