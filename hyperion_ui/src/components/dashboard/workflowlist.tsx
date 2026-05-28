import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Play, Pencil } from 'lucide-react'

interface Workflow {
  workflow_id: string
  name: string
  status: string
  updated_at: string
}

interface WorkflowListProps {
  workflows: Workflow[]
}

const statusColors = {
  active: 'bg-green-500',
  draft: 'bg-yellow-500',
  archived: 'bg-gray-500',
}

export function WorkflowList({ workflows }: WorkflowListProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Workflows</CardTitle>
        <Button asChild size="sm">
          <Link to="/workflows/new">New Workflow</Link>
        </Button>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {workflows.map((wf) => (
            <div key={wf.workflow_id} className="flex items-center justify-between border-b pb-3 last:border-0">
              <div>
                <p className="font-medium">{wf.name}</p>
                <p className="text-sm text-muted-foreground">
                  Updated {new Date(wf.updated_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge className={statusColors[wf.status] || 'bg-gray-500'}>{wf.status}</Badge>
                <Button variant="ghost" size="icon" asChild>
                  <Link to={`/workflows/${wf.workflow_id}`}>
                    <Pencil className="h-4 w-4" />
                  </Link>
                </Button>
                <Button variant="ghost" size="icon">
                  <Play className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}