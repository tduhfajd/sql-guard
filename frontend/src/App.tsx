import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from '@/components/ui/toaster'
import { AuthProvider } from '@/hooks/useAuth'
import Layout from '@/components/Layout'
import Console from '@/pages/Console'
import Templates from '@/pages/Templates'
import Approvals from '@/pages/Approvals'
import Audit from '@/pages/Audit'
import Users from '@/pages/Users'
import Policies from '@/pages/Policies'
import Login from '@/pages/Login'
import './App.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div className="min-h-screen bg-background">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<Layout />}>
                <Route index element={<Console />} />
                <Route path="console" element={<Console />} />
                <Route path="templates" element={<Templates />} />
                <Route path="approvals" element={<Approvals />} />
                <Route path="audit" element={<Audit />} />
                <Route path="users" element={<Users />} />
                <Route path="policies" element={<Policies />} />
              </Route>
            </Routes>
            <Toaster />
          </div>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App