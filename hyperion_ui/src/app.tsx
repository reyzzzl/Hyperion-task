import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from '@/components/theme-provider'
import Layout from '@/components/layout/Layout'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import Workflows from '@/pages/Workflows'
import WorkflowEditorPage from '@/pages/WorkflowEditorPage'
import Executions from '@/pages/Executions'
import Settings from '@/pages/Settings'
import { useAuth } from '@/hooks/useAuth'
import { ErrorBoundary } from '@/components/ErrorBoundary'

function App() {
  const { isAuthenticated } = useAuth()

  return (
    <ThemeProvider defaultTheme="dark" storageKey="hyperion-theme">
      <BrowserRouter>
        <ErrorBoundary>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}>
              <Route index element={<Dashboard />} />
              <Route path="workflows" element={<Workflows />} />
              <Route path="workflows/new" element={<WorkflowEditorPage />} />
              <Route path="workflows/:id" element={<WorkflowEditorPage />} />
              <Route path="executions" element={<Executions />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </ErrorBoundary>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App