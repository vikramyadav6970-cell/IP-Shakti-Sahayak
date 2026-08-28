import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SceneWrapper } from '@/components/three/SceneWrapper'
import { AppShell } from '@/components/AppShell'
import { IntentSelectionPage } from '@/app/IntentSelectionPage'
import { ContextPage } from '@/app/ContextPage'
import { ChatPage } from '@/app/ChatPage'
import { ClassifyPage } from '@/app/ClassifyPage'
import { AbsPage } from '@/app/AbsPage'
import { SourcesPage } from '@/app/SourcesPage'
import { AdminPage } from '@/app/AdminPage'
import { LoginPage } from '@/app/LoginPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {/* 3D background — behind everything */}
        <SceneWrapper />

        <Routes>
          {/* Landing page — full-screen, no app shell */}
          <Route path="/" element={<IntentSelectionPage />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Pages with app shell (header, nav, disclaimer) */}
          <Route element={<AppShell />}>
            <Route path="/context" element={<ContextPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/classify" element={<ClassifyPage />} />
            <Route path="/abs" element={<AbsPage />} />
            <Route path="/sources" element={<SourcesPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
