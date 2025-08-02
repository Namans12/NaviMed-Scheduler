"use client"

import { DataTable } from "@/components/data-table"
import { SectionCards } from "@/components/section-cards"
import { OptimizedQueue } from "@/components/optimized-queue"
import { AvailableDoctors } from "@/components/doctors-available"
import { useBackendStore } from "@/lib/store"

export default function Page() {
  const { 
    adminStats,
    queueData,
    completedPatients,
    allDoctors,
    allPatients,
    loading,
    isBackendOnline
  } = useBackendStore()

  // Transform patient data for DataTable - show empty array when loading
  const transformedPatientData = loading ? [] : allPatients.map((patient, index) => ({
    id: patient.id || index + 1,
    bookingOrder: index + 1,
    name: patient.name,
    email: patient.email || 'N/A',
    phone: patient.phone,
    riskLevel: patient.risk_level || 'Low',
    status: patient.status || 'Active',
  }))

  return (
    <>
      <SectionCards 
        adminStats={adminStats}
        allPatients={allPatients}
        loading={loading}
        isBackendOnline={isBackendOnline}
      />
      <div className='grid grid-cols-1 gap-4 lg:grid-cols-7 px-6 '>
        <AvailableDoctors 
          doctors={allDoctors}
          loading={loading}
          isBackendOnline={isBackendOnline}
        />
        <OptimizedQueue 
          completedPatients={completedPatients}
          queueData={queueData}
          loading={loading}
          isBackendOnline={isBackendOnline}
        />
      </div>
      <DataTable data={transformedPatientData} loading={loading} />
    </>
  )
}
