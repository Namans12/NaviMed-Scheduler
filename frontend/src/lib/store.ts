"use client"

import { create } from 'zustand'
import { toast } from 'sonner'
import { BackendService, BackendData } from '@/lib/utils'

interface BackendStore extends BackendData {
  // Actions
  setBackendData: (data: Partial<BackendData>) => void
  setLoading: (loading: boolean) => void
  setBackendOnline: (isOnline: boolean) => void
  
  // Backend operations
  checkBackendStatus: () => Promise<void>
  fetchAdminData: (forceOnline?: boolean) => Promise<void>
  fetchDetailedQueueData: () => Promise<void>
  reorderQueue: () => Promise<void>
  nextPatient: () => Promise<void>
  handleRefresh: () => void
  
  // Queue management UI state
  queueProcessing: boolean
  setQueueProcessing: (processing: boolean) => void
  
  // General UI state
  isChecking: boolean
  setIsChecking: (isChecking: boolean) => void
}

const backendService = BackendService.getInstance()

export const useBackendStore = create<BackendStore>((set, get) => ({
  // Initial state
  adminStats: null,
  queueData: null,
  detailedQueueData: null,
  completedPatients: [],
  allDoctors: [],
  allPatients: [],
  isBackendOnline: false,
  lastRefresh: null,
  loading: true,
  isChecking: false,
  queueProcessing: false,

  // Actions
  setBackendData: (data) => set((state) => ({ ...state, ...data })),
  setLoading: (loading) => set({ loading }),
  setBackendOnline: (isBackendOnline) => set({ isBackendOnline }),
  setIsChecking: (isChecking) => set({ isChecking }),
  setQueueProcessing: (queueProcessing) => set({ queueProcessing }),

  // Backend operations
  checkBackendStatus: async () => {
    const { setIsChecking, setBackendOnline, fetchAdminData, fetchDetailedQueueData } = get()
    setIsChecking(true)
    try {
      const isOnline = await backendService.checkBackendStatus()
      setBackendOnline(isOnline)
      
      const currentState = get()
      if (isOnline && (!currentState.queueData || !currentState.detailedQueueData)) {
        await Promise.all([
          fetchAdminData(),
          fetchDetailedQueueData()
        ])
      }
    } catch (error) {
      console.error('Error checking backend status:', error)
      setBackendOnline(false)
    } finally {
      setIsChecking(false)
    }
  },

  fetchAdminData: async (forceOnline = false) => {
    const { isBackendOnline, setLoading, setBackendData } = get()
    
    if (!forceOnline && !isBackendOnline) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      
      const data = await backendService.fetchAdminData()
      
      setBackendData({
        ...data,
        lastRefresh: new Date(),
        loading: false,
      })
    } catch (error) {
      console.error('Error fetching admin data:', error)
      setLoading(false)
    }
  },

  fetchDetailedQueueData: async () => {
    const { setLoading, setBackendData } = get()
    
    try {
      setLoading(true)
      const detailedQueueData = await backendService.fetchDetailedQueueData()
      setBackendData({ detailedQueueData })
    } catch (error) {
      console.error('Error fetching detailed queue data:', error)
    } finally {
      setLoading(false)
    }
  },

  reorderQueue: async () => {
    const { fetchAdminData, fetchDetailedQueueData } = get()
    
    try {
      const result = await backendService.reorderQueue()
      
      if (result.success) {
        toast.message(result.message)
        fetchAdminData() // Refresh admin data
        fetchDetailedQueueData() // Refresh detailed queue data
      } else {
        toast.error(result.message)
      }
    } catch (error) {
      console.error('Error reordering queue:', error)
      toast.error('❌ Failed to reorder queue. Please check backend connection.')
    }
  },

  nextPatient: async () => {
    const { setQueueProcessing, fetchAdminData, fetchDetailedQueueData, detailedQueueData } = get()
    
    try {
      setQueueProcessing(true)

      // Get current and next patient names for better messaging
      const currentPatientName = detailedQueueData?.queue && detailedQueueData.queue.length > 0 
        ? detailedQueueData.queue[0].name 
        : 'Unknown Patient'
      
      const nextPatientName = detailedQueueData?.queue && detailedQueueData.queue.length > 1 
        ? detailedQueueData.queue[1].name 
        : null

      const result = await backendService.nextPatient()
      
      if (result.success) {
        const message = nextPatientName 
          ? `✅ ${currentPatientName} completed. ${nextPatientName} is now the current patient.`
          : `✅ ${currentPatientName} completed. Queue is now empty.`
        
        toast.message(message)
        
        // Refresh data after completing patient
        fetchAdminData()
        fetchDetailedQueueData()
      } else {
        toast.error(result.message)
      }
    } catch (error) {
      console.error('Error moving to next patient:', error)
      toast.error('❌ Failed to move to next patient. Please check backend connection.')
    } finally {
      setQueueProcessing(false)
    }
  },

  handleRefresh: () => {
    const { isBackendOnline, checkBackendStatus, fetchAdminData, fetchDetailedQueueData } = get()
    
    if (isBackendOnline) {
      fetchAdminData()
      fetchDetailedQueueData()
    } else {
      checkBackendStatus()
    }
  },
}))