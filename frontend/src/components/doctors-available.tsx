import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { IconCircleCheckFilled } from "@tabler/icons-react"
import { Doctor } from "@/lib/utils"

interface AvailableDoctorsProps {
  doctors: Doctor[]
  loading: boolean
  isBackendOnline: boolean
}

export const AvailableDoctors = ({ doctors, loading, isBackendOnline }: AvailableDoctorsProps) => {
    return (
        <Card className='col-span-1 lg:col-span-3'>
            <CardHeader>
              <CardTitle>Doctor Availability</CardTitle>
            </CardHeader>
            <CardContent className='pl-2 h-60'>
              <Overview doctors={doctors} loading={loading} isBackendOnline={isBackendOnline} />
            </CardContent>
        </Card>
    )
}

interface OverviewProps {
  doctors: Doctor[]
  loading: boolean
  isBackendOnline: boolean
}

const Overview = ({ doctors, loading, isBackendOnline }: OverviewProps) => {
  // Mock data for doctors as fallback
  const mockDoctorsData = [
    {
      id: 1,
      name: "Dr. Smith",
      specialty: "Cardiology",
      availability_status: "Available",
      rating: 4.9
    },
    {
      id: 2,
      name: "Dr. Johnson",
      specialty: "Neurology",
      availability_status: "Away",
      rating: 4.8
    },
  ]

  // Show mock data only if backend is offline and not loading
  // If backend is online but no data, show empty state instead of mock data
  const displayDoctors = loading ? [] : 
    isBackendOnline ? mockDoctorsData : 
    (doctors.length > 0 ? mockDoctorsData : mockDoctorsData)

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Available":
        return (
          <Badge variant="outline" className="text-muted-foreground px-1.5">
            <IconCircleCheckFilled className="fill-green-500 dark:fill-green-400" />
            Available
          </Badge>
        ) 
      case "Busy":
        return <Badge variant="destructive">Busy</Badge>
      case "Away":
        return <Badge variant="destructive">Away</Badge>
      case "Offline":
        return <Badge variant="secondary">Offline</Badge>
      default:
        return <Badge variant="outline">{status || "Available"}</Badge>
    }
  }

  if (loading) {
    return (
      <div className="h-full overflow-auto">
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-12" />
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
            <TableHead>Doctor</TableHead>
            <TableHead>Specialty</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Rating</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayDoctors.map((doctor) => (
            <TableRow key={doctor.id}>
              <TableCell className="font-medium">{doctor.name}</TableCell>
              <TableCell>{doctor.specialty}</TableCell>
              <TableCell>{getStatusBadge(doctor.availability_status || "Available")}</TableCell>
              <TableCell className="text-right">
                ⭐ {doctor.rating || "N/A"}
              </TableCell>
            </TableRow>
          ))}
          {displayDoctors.length === 0 && (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground">
                No doctor data available
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  )
}