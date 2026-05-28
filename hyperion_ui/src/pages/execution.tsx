import { useQuery } from '@tanstack/react-query'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { formatDistanceToNow } from 'date-fns'
import api from '@/services/api'

export default function Executions() {
  const { data: executions, isLoading } = useQuery({
    queryKey: ['executions'],
    queryFn: () => api.get('/executions').then(res => res.data),
  })

  if (isLoading) return <div>Loading...</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Executions</h1>
        <p className="text-muted-foreground">View all workflow execution history</p>
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Workflow ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Started</TableHead>
              <TableHead>Depth</TableHead>
              <TableHead>Errors</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {executions?.map((exec: any) => (
              <TableRow key={exec.execution_id}>
                <TableCell className="font-medium">{exec.workflow_id?.slice(0, 8)}</TableCell>
                <TableCell>
                  <Badge variant={exec.status === 'completed' ? 'default' : 'destructive'}>
                    {exec.status}
                  </Badge>
                </TableCell>
                <TableCell>{formatDistanceToNow(new Date(exec.started_at), { addSuffix: true })}</TableCell>
                <TableCell>{exec.depth}</TableCell>
                <TableCell className="text-red-500">{exec.errors?.length || 0}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}