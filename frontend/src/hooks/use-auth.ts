"use client"

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  email: string
  name: string
  role: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

const HARDCODED_CREDENTIALS = {
  email: 'admin@navimed.com',
  password: 'admin123'
}

const STORAGE_KEYS = {
  USER: 'navimed_user',
  TOKEN: 'navimed_token'
}

export function useAuth() {
  const router = useRouter()
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true
  })

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = () => {
      try {
        const token = localStorage.getItem(STORAGE_KEYS.TOKEN)
        const userData = localStorage.getItem(STORAGE_KEYS.USER)

        if (token && userData) {
          const user = JSON.parse(userData)
          setAuthState({
            user,
            isAuthenticated: true,
            isLoading: false
          })
        } else {
          setAuthState({
            user: null,
            isAuthenticated: false,
            isLoading: false
          })
        }
      } catch (error) {
        console.error('Error checking authentication:', error)
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false
        })
      }
    }

    checkAuth()
  }, [])

  const login = useCallback(async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      // Check hardcoded credentials
      if (email === HARDCODED_CREDENTIALS.email && password === HARDCODED_CREDENTIALS.password) {
        const user: User = {
          email: HARDCODED_CREDENTIALS.email,
          name: 'Admin User',
          role: 'admin'
        }

        // Create a simple token (in a real app, this would come from the server)
        const token = btoa(`${email}:${Date.now()}`)

        // Store in localStorage
        localStorage.setItem(STORAGE_KEYS.TOKEN, token)
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user))

        setAuthState({
          user,
          isAuthenticated: true,
          isLoading: false
        })

        return { success: true }
      } else {
        return { success: false, error: 'Invalid email or password' }
      }
    } catch (error) {
      console.error('Login error:', error)
      return { success: false, error: 'An error occurred during login' }
    }
  }, [])

  const logout = useCallback(() => {
    try {
      // Clear localStorage
      localStorage.removeItem(STORAGE_KEYS.TOKEN)
      localStorage.removeItem(STORAGE_KEYS.USER)

      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false
      })

      // Redirect to admin login page
      router.push('/admin')
    } catch (error) {
      console.error('Logout error:', error)
    }
  }, [router])

  const requireAuth = useCallback(() => {
    if (!authState.isLoading && !authState.isAuthenticated) {
      router.push('/admin')
      return false
    }
    return true
  }, [authState.isLoading, authState.isAuthenticated, router])

  return {
    ...authState,
    login,
    logout,
    requireAuth
  }
}