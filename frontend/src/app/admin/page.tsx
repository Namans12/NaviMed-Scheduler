import { LoginForm } from "@/components/login-form"

export default function AdminLogin() {
  return (
    <div className="flex min-h-svh w-full flex-col items-center justify-center p-6 md:p-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-center font-satoshi">NaviMed Admin Dashboard</h1>
      </div>
      <div className="w-full max-w-sm">
        <LoginForm />
        
        {/* Test Credentials */}
        <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-md">
          <h3 className="text-sm font-medium text-gray-900 mb-2">Test Credentials</h3>
          <div className="text-sm text-gray-600 space-y-1">
            <div><span className="font-medium">Email:</span> admin@navimed.com</div>
            <div><span className="font-medium">Password:</span> admin123</div>
          </div>
        </div>
      </div>
    </div>
  )
}
