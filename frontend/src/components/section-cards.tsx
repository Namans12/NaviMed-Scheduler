
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { AdminStats, Patient } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"

interface SectionCardsProps {
  adminStats: AdminStats | null
  allPatients: Patient[]
  loading: boolean
  isBackendOnline: boolean
}

export function SectionCards({ adminStats, allPatients, loading, isBackendOnline }: SectionCardsProps) {
  // Calculate stats from available data if adminStats is not available
  // Show real data when backend is online, fallback values when offline
  const totalPatients = loading ? 0 : 
    isBackendOnline ? (adminStats?.total_patients ?? allPatients.length) : 15 // Show mock total when offline
  const waitingPatients = loading ? 0 : 
    isBackendOnline ? (adminStats?.waiting_patients ?? 0) : 5 // Show mock waiting when offline  
  const emergencyCases = loading ? 0 : 
    isBackendOnline ? (adminStats?.emergency_cases_total ?? 
      allPatients.filter(p => p.is_emergency || p.emergency).length) : 2 // Show mock emergency when offline

  return (
    <div className="grid grid-cols-1 gap-4 px-4 sm:grid-cols-2 lg:grid-cols-3 lg:px-6">
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Total Patients</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {loading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              totalPatients
            )}
          </CardTitle>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="text-muted-foreground">
            Total patients in the system
          </div>
        </CardFooter>
      </Card>
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Waiting Patients</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {loading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              waitingPatients
            )}
          </CardTitle>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="text-muted-foreground">
            Patients currently in queue
          </div>
        </CardFooter>
      </Card>
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Emergency Cases</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {loading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              emergencyCases
            )}
          </CardTitle>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="text-muted-foreground">Total emergency cases today</div>
        </CardFooter>
      </Card>
    </div>
  )
}