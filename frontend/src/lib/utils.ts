import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import axios from "axios"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Backend API configuration
const BACKEND_URL = 'http://localhost:8000'

// Types for backend data
export interface AdminStats {
  total_patients: number
  waiting_patients: number
  emergency_cases_total: number
}

export interface Patient {
  id?: number
  patient_id?: string
  name: string
  email?: string
  phone: string
  risk_level?: string
  status?: string
  is_emergency?: boolean
  emergency?: boolean
  completion_order?: number
  completed_at?: string
}

export interface Doctor {
  id: number
  name: string
  specialty: string
  availability_status?: string
  rating?: number
}

export interface QueueData {
  patient_queue: Patient[]
  queue_summary: {
    total_patients: number
    waiting_patients: number
    scheduled_patients: number
  }
  scheduling_metrics: {
    average_wait_time: string
    ai_optimization_active: boolean
    appointment_completion_rate?: string
    no_show_rate?: string
    emergency_response_time?: string
    queue_algorithm?: string
  }
}

// New interfaces for detailed queue management
export interface QueuePatient {
  patient_id: number
  name: string
  age: number
  gender: string
  appointment_type: string
  priority: number
  is_emergency: boolean
  symptoms?: string
  phone: string
  email: string
  queue_timestamp: string
  status: string
  current_position?: number
  estimated_wait?: number
  appointment_duration?: number
  in_queue_for?: string
}

export interface DetailedQueueData {
  queue: QueuePatient[]
  total_patients: number
  average_wait_time: string
  next_patient: QueuePatient | null
  rl_optimized: boolean
  last_updated: string
}

export interface BackendData {
  adminStats: AdminStats | null
  queueData: QueueData | null
  detailedQueueData: DetailedQueueData | null
  completedPatients: Patient[]
  allDoctors: Doctor[]
  allPatients: Patient[]
  isBackendOnline: boolean
  lastRefresh: Date | null
  loading: boolean
}

// Backend service class
export class BackendService {
  private static instance: BackendService
  
  public static getInstance(): BackendService {
    if (!BackendService.instance) {
      BackendService.instance = new BackendService()
    }
    return BackendService.instance
  }

  async checkBackendStatus(): Promise<boolean> {
    try {
      await axios.get(`${BACKEND_URL}/health`, { timeout: 5000 })
      return true
    } catch {
      return false
    }
  }

  async autoLogin(): Promise<string | null> {
    try {
      const formData = new FormData()
      formData.append('email', 'admin@navimed.com')
      formData.append('password', 'admin123')
      
      const loginResponse = await axios.post(`${BACKEND_URL}/auth/login`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      
      if (loginResponse.data.access_token) {
        localStorage.setItem('token', loginResponse.data.access_token)
        return loginResponse.data.access_token
      }
    } catch (error) {
      console.warn('Auto-login failed:', error)
    }
    return null
  }

  async fetchAdminData(): Promise<Partial<BackendData>> {
    const data: Partial<BackendData> = {
      adminStats: null,
      queueData: null,
      completedPatients: [],
      allDoctors: [],
      allPatients: [],
    }

    try {
      // Get or create auth token
      let token = localStorage.getItem('token')
      if (!token) {
        token = await this.autoLogin()
      }
      
      const headers = token ? { Authorization: `Bearer ${token}` } : {}

      // Fetch queue status
      try {
        const queueResponse = await axios.get(`${BACKEND_URL}/queue/status`, { timeout: 10000 })
        data.queueData = queueResponse.data
      } catch (error) {
        console.error('Error fetching queue data:', error)
      }

      // Fetch admin statistics
      try {
        const statsResponse = await axios.get(`${BACKEND_URL}/admin/statistics`)
        data.adminStats = statsResponse.data
      } catch (error) {
        console.error('Error fetching admin statistics:', error)
      }

      // Fetch completed patients
      try {
        const completedResponse = await axios.get(`${BACKEND_URL}/completed_patients`)
        data.completedPatients = completedResponse.data.completed_patients || []
      } catch (error) {
        console.error('Error fetching completed patients:', error)
      }

      // Fetch all doctors
      try {
        const doctorsResponse = await axios.get(`${BACKEND_URL}/doctors`)
        data.allDoctors = doctorsResponse.data
      } catch (error) {
        console.error('Error fetching doctors:', error)
      }

      // Fetch all patients
      try {
        const patientsResponse = await axios.get(`${BACKEND_URL}/patients/public`)
        data.allPatients = patientsResponse.data
      } catch (error) {
        console.warn('Public patients endpoint failed, trying authenticated endpoint')
        try {
          const patientsResponse = await axios.get(`${BACKEND_URL}/patients`, { headers })
          data.allPatients = patientsResponse.data
        } catch (authError) {
          console.warn('Auth endpoint also failed, using queue data for patients')
          if (data.queueData?.patient_queue) {
            data.allPatients = data.queueData.patient_queue
          }
        }
      }

    } catch (error) {
      console.error('Error fetching admin data:', error)
    }

    return data
  }

  async reorderQueue(): Promise<{ success: boolean; message: string }> {
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      
      const response = await axios.post(`${BACKEND_URL}/queue/reorder_rl`, {}, { headers })
      
      return {
        success: true,
        message: response.data.reordered 
          ? `✅ ${response.data.message}. Queue optimized with ${response.data.new_queue_size} patients.`
          : `ℹ️ ${response.data.message}`
      }
    } catch (error) {
      console.error('Error triggering RL queue reorder:', error)
      return {
        success: false,
        message: '❌ Failed to reorder queue. Please check backend connection.'
      }
    }
  }

  async fetchDetailedQueueData(): Promise<DetailedQueueData | null> {
    try {
      const response = await axios.get(`${BACKEND_URL}/queue/current`, { timeout: 10000 })
      return response.data
    } catch (error) {
      console.error('Error fetching detailed queue data:', error)
      return null
    }
  }

  async nextPatient(): Promise<{ success: boolean; message: string }> {
    try {
      const response = await axios.get(`${BACKEND_URL}/next_patient`, { timeout: 10000 })
      
      return {
        success: true,
        message: response.data.message || '✅ Patient completed successfully'
      }
    } catch (error: any) {
      console.error('Error moving to next patient:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '❌ Failed to move to next patient'
      }
    }
  }
}
