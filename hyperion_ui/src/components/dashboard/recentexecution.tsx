import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatDistanceToNow } from 'date-fns'

interface Execution {
  execution_id: string
  workflow_id: string
  status: 'running' | 'completed' | 'failed' | 'cancelled'
  started_at: string
}

interface RecentExecutionsProps {
  executions: Execution[]
}

const statusColors = {
  running: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  cancelled: 'bg-gray-500',
}

export function RecentExecutions({ executions }: RecentExecutionsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Executions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {executions.map((exec) => (
            <div key={exec.execution_id} className="flex items-center justify-between border-b pb-3 last:border-0">
              <div>
                <p className="font-medium">Workflow: {exec.workflow_id.slice(0, 8)}</p>
                <p className="text-sm text-muted-foreground">
                  {formatDistanceToNow(new Date(exec.started_at), { addSuffix: true })}
                </p>
              </div>
              <Badge className={statusColors[exec.status]}>{exec.status}</Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}