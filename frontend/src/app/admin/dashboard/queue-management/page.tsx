"use client"

import { useBackendStore } from "@/lib/store"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Loader2, Clock, User, AlertCircle, CheckCircle } from "lucide-react"

export default function QueueManagementPage() {
  const { 
    detailedQueueData,
    loading,
    isBackendOnline,
    queueProcessing,
    nextPatient,
    reorderQueue,
    fetchDetailedQueueData
  } = useBackendStore()

  const getPriorityColor = (priority: number) => {
    if (priority >= 5) return "destructive"
    if (priority >= 4) return "secondary"
    if (priority >= 3) return "default"
    return "outline"
  }

  const getAppointmentTypeColor = (type: string) => {
    switch (type) {
      case 'emergency': return "destructive"
      case 'diagnostics': return "secondary"
      case 'consultation': return "default"
      default: return "outline"
    }
  }

  if (loading && !detailedQueueData) {
    return (
      <div className="space-y-6 px-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    )
  }

  const currentPatient = detailedQueueData?.queue?.[0]
  const nextPatientInQueue = detailedQueueData?.queue?.[1]
  const remainingQueue = detailedQueueData?.queue?.slice(1) || []

  return (
    <div className="space-y-6 px-6">
      {/* Header */}
      {/* <div>
        <h1 className="text-2xl font-bold tracking-tight">🤖 RL-Optimized Queue Management</h1>
        <p className="text-muted-foreground">
          Real-time appointment queue powered by Reinforcement Learning
        </p>
      </div> */}

      {/* Queue Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📊 Queue Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="space-y-1">
              <p className="text-2xl font-bold text-primary">
                {detailedQueueData?.total_patients || 0}
              </p>
              <p className="text-sm text-muted-foreground">Total in Queue</p>
            </div>
            <div className="space-y-1">
              <p className="text-2xl font-bold text-amber-600">
                {detailedQueueData?.average_wait_time || 'N/A'}
              </p>
              <p className="text-sm text-muted-foreground">Average Wait Time</p>
            </div>
            <div className="space-y-1">
              <Badge variant={detailedQueueData?.rl_optimized ? "default" : "secondary"}>
                {detailedQueueData?.rl_optimized ? 'RL Optimization Active' : 'Manual Mode'}
              </Badge>
            </div>
            <div className="space-y-1">
              <Badge variant="outline">
                Last Updated: {detailedQueueData?.last_updated ? new Date(detailedQueueData.last_updated).toLocaleTimeString() : 'Unknown'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current and Next Patient Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Patient Card */}
        <Card className="border-green-200 bg-green-50/50">
          <CardHeader className="border-b border-green-200">
            <CardTitle className="text-green-700 flex items-center gap-2">
              <User className="h-5 w-5" />
              Current Patient
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {currentPatient ? (
              <div className="space-y-4">
                <h3 className="text-2xl font-bold text-green-800">{currentPatient.name}</h3>
                <div className="flex flex-wrap gap-2">
                  <Badge variant={getAppointmentTypeColor(currentPatient.appointment_type)}>
                    {currentPatient.appointment_type}
                  </Badge>
                  {currentPatient.is_emergency && (
                    <Badge variant="destructive">EMERGENCY</Badge>
                  )}
                  <Badge variant={getPriorityColor(currentPatient.priority)}>
                    Priority {currentPatient.priority}
                  </Badge>
                </div>
                <div className="space-y-2 text-sm">
                  <p><span className="font-medium">Age:</span> {currentPatient.age} | <span className="font-medium">Gender:</span> {currentPatient.gender}</p>
                  <p><span className="font-medium">Phone:</span> {currentPatient.phone}</p>
                  {currentPatient.symptoms && (
                    <p><span className="font-medium">Symptoms:</span> {currentPatient.symptoms}</p>
                  )}
                  <p className="text-green-700 font-medium">Status: Ready for consultation</p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <h3 className="font-medium text-muted-foreground">No patients in queue</h3>
                <p className="text-sm text-muted-foreground">Patients will appear here when they book appointments</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Next Patient Card */}
        <Card className="border-amber-200 bg-amber-50/50">
          <CardHeader className="border-b border-amber-200">
            <CardTitle className="text-amber-700 flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Next Patient
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {nextPatientInQueue ? (
              <div className="space-y-4">
                <h3 className="text-2xl font-bold text-amber-800">{nextPatientInQueue.name}</h3>
                <div className="flex flex-wrap gap-2">
                  <Badge variant={getAppointmentTypeColor(nextPatientInQueue.appointment_type)}>
                    {nextPatientInQueue.appointment_type}
                  </Badge>
                  {nextPatientInQueue.is_emergency && (
                    <Badge variant="destructive">EMERGENCY</Badge>
                  )}
                  <Badge variant={getPriorityColor(nextPatientInQueue.priority)}>
                    Priority {nextPatientInQueue.priority}
                  </Badge>
                </div>
                <div className="space-y-2 text-sm">
                  <p><span className="font-medium">Age:</span> {nextPatientInQueue.age} | <span className="font-medium">Gender:</span> {nextPatientInQueue.gender}</p>
                  <p><span className="font-medium">Phone:</span> {nextPatientInQueue.phone}</p>
                  {nextPatientInQueue.symptoms && (
                    <p><span className="font-medium">Symptoms:</span> {nextPatientInQueue.symptoms}</p>
                  )}
                  <p className="text-amber-700 font-medium">
                    Estimated wait: {nextPatientInQueue.estimated_wait || 15} minutes
                  </p>
                  {nextPatientInQueue.appointment_duration && (
                    <p className="text-blue-700">
                      Appointment duration: {nextPatientInQueue.appointment_duration} minutes
                    </p>
                  )}
                </div>
              </div>
            ) : currentPatient ? (
              <div className="text-center py-8">
                <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <h3 className="font-medium text-muted-foreground">Last patient in queue</h3>
                <p className="text-sm text-muted-foreground">No patient waiting after current</p>
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <h3 className="font-medium text-muted-foreground">No next patient</h3>
                <p className="text-sm text-muted-foreground">Queue is empty</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              size="lg"
              onClick={nextPatient}
              disabled={queueProcessing || !currentPatient}
              className="min-w-[250px]"
            >
              {queueProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : currentPatient ? (
                '🔄 Complete Current & Next Patient'
              ) : (
                'No Patients in Queue'
              )}
            </Button>
            
            <Button
              variant="outline"
              size="lg"
              onClick={reorderQueue}
              disabled={queueProcessing || !currentPatient}
            >
              {queueProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : '🤖 RL Reorder Queue'}
            </Button>
            
            <Button
              variant="outline"
              size="lg"
              onClick={fetchDetailedQueueData}
              disabled={loading}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : '🔄 Refresh'}
            </Button>
          </div>
          
          {currentPatient && (
            <p className="text-center text-sm text-muted-foreground mt-4">
              Click &quot;Complete Current & Next Patient&quot; to mark {currentPatient.name} as completed and move to the next patient
            </p>
          )}
        </CardContent>
      </Card>

      {/* Remaining Queue Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            📋 Remaining Queue ({remainingQueue.length} patients waiting)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {remainingQueue.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Position</TableHead>
                  <TableHead>Patient Name</TableHead>
                  <TableHead>Age/Gender</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Emergency</TableHead>
                  <TableHead>Est. Wait</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Contact</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {remainingQueue.map((patient, index) => (
                  <TableRow 
                    key={patient.patient_id}
                    className={index === 0 ? "bg-amber-50" : ""}
                  >
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-lg">#{index + 2}</span>
                        {index === 0 && (
                          <Badge variant="secondary" className="text-xs">NEXT</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{patient.name}</p>
                        {patient.symptoms && (
                          <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                            {patient.symptoms}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p>{patient.age}y</p>
                        <p className="text-xs text-muted-foreground">{patient.gender}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getAppointmentTypeColor(patient.appointment_type)} className="text-xs">
                        {patient.appointment_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getPriorityColor(patient.priority)} className="text-xs">
                        {patient.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={patient.is_emergency ? "destructive" : "outline"} className="text-xs">
                        {patient.is_emergency ? "YES" : "No"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{patient.estimated_wait || (index + 1) * 15} min</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{patient.appointment_duration || 15} min</span>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="text-sm">{patient.phone}</p>
                        {patient.email && patient.email !== `patient${patient.patient_id}@temp.com` && (
                          <p className="text-xs text-muted-foreground truncate max-w-[150px]">
                            {patient.email}
                          </p>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : currentPatient ? (
            <Alert>
              <AlertDescription>
                Only one patient in queue (currently being seen). No patients waiting.
              </AlertDescription>
            </Alert>
          ) : (
            <Alert>
              <AlertDescription>
                Queue is empty. Patients will appear here when they book appointments.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
