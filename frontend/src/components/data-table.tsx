"use client"

import * as React from "react"
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from "@tanstack/react-table"
import { z } from "zod"

import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export const schema = z.object({
  id: z.number(),
  bookingOrder: z.number(),
  name: z.string(),
  email: z.string(),
  phone: z.string(),
  riskLevel: z.string(),
  status: z.string(),
})



const columns: ColumnDef<z.infer<typeof schema>>[] = [
  {
    accessorKey: "bookingOrder",
    header: "Booking Order",
    cell: ({ row }) => (
      <div className="font-medium text-center">#{row.original.bookingOrder}</div>
    ),
  },
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => (
      <div className="font-medium">{row.original.name}</div>
    ),
  },
  {
    accessorKey: "email",
    header: "Email",
    cell: ({ row }) => (
      <div className="text-muted-foreground">{row.original.email}</div>
    ),
  },
  {
    accessorKey: "phone",
    header: "Phone",
    cell: ({ row }) => (
      <div>{row.original.phone}</div>
    ),
  },
  {
    accessorKey: "riskLevel",
    header: "Risk Level",
    cell: ({ row }) => {
      const getRiskBadge = (risk: string) => {
        switch (risk) {
          case "High":
            return <Badge variant="destructive">High</Badge>
          case "Medium":
            return <Badge variant="default" className="bg-yellow-500">Medium</Badge>
          case "Low":
            return <Badge variant="outline" className="text-green-600">Low</Badge>
          default:
            return <Badge variant="outline">{risk}</Badge>
        }
      }
      return getRiskBadge(row.original.riskLevel)
    },
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const getStatusBadge = (status: string) => {
        switch (status) {
          case "Confirmed":
            return <Badge variant="default" className="bg-green-500">Confirmed</Badge>
          case "Pending":
            return <Badge variant="secondary">Pending</Badge>
          case "Cancelled":
            return <Badge variant="destructive">Cancelled</Badge>
          default:
            return <Badge variant="outline">{status}</Badge>
        }
      }
      return getStatusBadge(row.original.status)
    },
  },
]

export function DataTable({
  data: initialData,
  loading = false,
}: {
  data: z.infer<typeof schema>[]
  loading?: boolean
}) {
  const [sorting, setSorting] = React.useState<SortingState>([])

  const table = useReactTable({
    data: initialData,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div className="w-full px-4 lg:px-6">
      {/* <div className="mb-4 font-bold">All patients</div> */}
      <div className="overflow-hidden rounded-lg border">
        <Table>
          <TableHeader className="bg-muted">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id} colSpan={header.colSpan}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {loading ? (
              // Show skeleton loading rows
              [...Array(5)].map((_, i) => (
                <TableRow key={`skeleton-${i}`}>
                  <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                </TableRow>
              ))
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}