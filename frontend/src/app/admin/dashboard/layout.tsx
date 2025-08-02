"use client"

import { useEffect } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { SiteHeader } from "@/components/site-header"
import { useBackendStore } from "@/lib/store"
import { useAuth } from "@/hooks/use-auth"

export default function DashboardLayout({
    children,
  }: Readonly<{
    children: React.ReactNode;
  }>) {
    const {
      checkBackendStatus,
      fetchAdminData,
      fetchDetailedQueueData,
      isBackendOnline,
      setBackendOnline,
      setIsChecking
    } = useBackendStore()

    const { isAuthenticated, isLoading, requireAuth } = useAuth()

    // Check authentication and redirect if not authenticated
    useEffect(() => {
      if (!isLoading) {
        requireAuth()
      }
    }, [isLoading, requireAuth])

    // Initial data fetch on mount - ensures real data loads immediately when page opens
    useEffect(() => {
      if (isAuthenticated && !isLoading) {
        const initializeApp = async () => {
          setIsChecking(true)
          try {
            // Check backend status first
            await checkBackendStatus()
          } catch (error) {
            console.error('Error during app initialization:', error)
            setBackendOnline(false)
          } finally {
            setIsChecking(false)
          }
        }

        initializeApp()
      }
    }, [isAuthenticated, isLoading, checkBackendStatus, setBackendOnline, setIsChecking])

    // Set up periodic backend status checks
    useEffect(() => {
      if (isAuthenticated && !isLoading) {
        const checkStatusOnly = async () => {
          try {
            await checkBackendStatus()
          } catch (error) {
            console.error('Error checking backend status:', error)
            setBackendOnline(false)
          }
        }

        // Start checking status after initial load (every 30 seconds)
        const statusInterval = setInterval(checkStatusOnly, 30000)
        return () => clearInterval(statusInterval)
      }
    }, [isAuthenticated, isLoading, checkBackendStatus, setBackendOnline])

    // Auto-refresh when backend is online
    useEffect(() => {
      if (isAuthenticated && !isLoading && isBackendOnline) {
        const refreshInterval = setInterval(() => {
          fetchAdminData()
          fetchDetailedQueueData()
        }, 30000) // Refresh every 30 seconds
        return () => clearInterval(refreshInterval)
      }
    }, [isAuthenticated, isLoading, isBackendOnline, fetchAdminData, fetchDetailedQueueData])

    // Don't render dashboard content if user is not authenticated or still loading
    if (isLoading) {
      return (
        <div className="flex min-h-svh w-full items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Loading...</p>
          </div>
        </div>
      )
    }

    if (!isAuthenticated) {
      return null // The requireAuth will handle redirection
    }

    return (
        <SidebarProvider
            style={
            {
                "--sidebar-width": "calc(var(--spacing) * 72)",
                "--header-height": "calc(var(--spacing) * 12)",
            } as React.CSSProperties
            }
        >
            <AppSidebar variant="inset" />
            <SidebarInset>
                <SiteHeader />
                <div className="flex flex-1 flex-col">
                  <div className="@container/main flex flex-1 flex-col gap-2">
                    <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
                      {children}
                    </div>
                  </div>
                </div>
            </SidebarInset>
        </SidebarProvider>
    )
  }
  