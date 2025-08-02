import { Card, CardHeader, CardTitle, CardContent } from "./ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Patient, QueueData } from "@/lib/utils"

interface OptimizedQueueProps {
  completedPatients: Patient[]
  queueData: QueueData | null
  loading: boolean
  isBackendOnline: boolean
}

export const OptimizedQueue = ({ completedPatients, queueData, loading, isBackendOnline }: OptimizedQueueProps) => {
    return(
        <Card className='col-span-1 lg:col-span-4'>
            <CardHeader>
            <CardTitle>AI-Optimized Patient Queue (Completed)</CardTitle>
            </CardHeader>
            <CardContent className="h-60">
                <RecentSales 
                  completedPatients={completedPatients}
                  queueData={queueData}
                  loading={loading}
                  isBackendOnline={isBackendOnline}
                />
            </CardContent>
        </Card>
    )
}

interface RecentSalesProps {
  completedPatients: Patient[]
  queueData: QueueData | null
  loading: boolean
  isBackendOnline: boolean
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function RecentSales({ completedPatients, queueData, loading, isBackendOnline }: RecentSalesProps) {
  // Only show completed patients, sorted by completion order
  const completedData = completedPatients
    .sort((a, b) => (a.completion_order || 0) - (b.completion_order || 0))
    .slice(0, 15) // Show up to 15 completed patients
    .map((patient, index) => ({
      id: `completed-${patient.patient_id || patient.id || index}`,
      completionOrder: patient.completion_order || 'N/A',
      patientName: patient.name,
      completedAt: patient.completed_at ? 
        new Date(patient.completed_at).toLocaleTimeString() : 
        'Just completed',
      emergency: (patient.is_emergency || patient.emergency) ? "Yes" : "No",
      status: "Completed"
    }))

  // Fallback to mock data if no backend data is available - only completed patients
  const mockData = [
    {
      id: "mock-1",
      completionOrder: 1,
      patientName: "Sarah Williams",
      completedAt: "09:15 AM",
      emergency: "No",
      status: "Completed"
    },
    {
      id: "mock-2",
      completionOrder: 2,
      patientName: "Michael Brown",
      completedAt: "09:45 AM",
      emergency: "Yes",
      status: "Completed"
    },
    {
      id: "mock-3",
      completionOrder: 3,
      patientName: "Emma Davis",
      completedAt: "10:20 AM",
      emergency: "No",
      status: "Completed"
    },
    {
      id: "mock-4",
      completionOrder: 4,
      patientName: "James Wilson",
      completedAt: "10:45 AM",
      emergency: "Yes",
      status: "Completed"
    },
    {
      id: "mock-5",
      completionOrder: 5,
      patientName: "Lisa Anderson",
      completedAt: "11:10 AM",
      emergency: "No",
      status: "Completed"
    }
  ]

  // Show mock data only if backend is offline and not loading
  // If backend is online but no data, show empty state instead of mock data
  const displayData = loading ? [] : 
    isBackendOnline ? completedData : 
    (completedData.length > 0 ? completedData : mockData)

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const getStatusBadge = (status: string) => {
    // Since we only show completed patients now, this will always be "Completed"
    return <Badge variant="default" className="bg-green-500">Completed</Badge>
  }

  const getEmergencyBadge = (emergency: string) => {
    return emergency === "Yes" 
      ? <Badge variant="destructive">Emergency</Badge>
      : <Badge variant="outline" className="text-muted-foreground">Regular</Badge>
  }

  if (loading) {
    return (
      <div className="h-full overflow-auto">
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4">
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-20" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-20">Order</TableHead>
            <TableHead>Patient Name</TableHead>
            <TableHead>Completed At</TableHead>
            <TableHead>Emergency</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayData.map((patient) => (
            <TableRow key={patient.id}>
              <TableCell className="font-medium text-center">
                {typeof patient.completionOrder === 'number' ? 
                  `#${patient.completionOrder}` : 
                  patient.completionOrder
                }
              </TableCell>
              <TableCell className="font-medium">{patient.patientName}</TableCell>
              <TableCell>{patient.completedAt}</TableCell>
              <TableCell>{getEmergencyBadge(patient.emergency)}</TableCell>
              <TableCell>{getStatusBadge(patient.status)}</TableCell>
            </TableRow>
          ))}
          {displayData.length === 0 && (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-muted-foreground">
                No completed patients available
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  )
}
  