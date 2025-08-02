"use client"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Badge } from "./ui/badge"
import { useBackendStore } from "@/lib/store"

export function SiteHeader() {
  const { 
    isBackendOnline, 
    lastRefresh, 
    handleRefresh, 
    isChecking, 
    reorderQueue 
  } = useBackendStore()
  return (
    <header className="flex h-(--header-height) shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator
          orientation="vertical"
          className="mx-2 data-[orientation=vertical]:h-4"
        />
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isBackendOnline ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="font-medium">
                Backend Server: 
                <Badge variant={isBackendOnline ? 'default' : 'destructive'} className="ml-2">
                  {isBackendOnline ? 'Online' : 'Offline'}
                </Badge>
              </span>
              {lastRefresh && (
                <span className="text-sm text-muted-foreground ml-4">
                  Last updated: {lastRefresh.toLocaleTimeString()}
                </span>
                )}
              </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="flex gap-2">
            <Button 
              onClick={handleRefresh} 
              disabled={isChecking}
              variant="outline"
              size="sm"
            >
              {isChecking ? 'Checking...' : 'Refresh'}
            </Button>
            <Button 
              onClick={reorderQueue} 
              disabled={!isBackendOnline}
              variant="default"
              size="sm"
            >
              🤖 Reorder Queue
            </Button>
        </div>
        </div>
      </div>
    </header>
  )
}
