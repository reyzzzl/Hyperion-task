import { useQuery } from '@tanstack/react-query'
import { StatsCards } from '@/components/dashboard/StatsCards'
import { RecentExecutions } from '@/components/dashboard/RecentExecutions'
import { WorkflowList } from '@/components/dashboard/WorkflowList'
import { Skeleton } from '@/components/ui/skeleton'
import api from '@/services/api'

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.get('/stats').then(res => res.data),
  })

  const { data: recentExecutions, isLoading: execLoading } = useQuery({
    queryKey: ['recent-executions'],
    queryFn: () => api.get('/executions?limit=5').then(res => res.data),
  })

  const { data: workflows, isLoading: workflowsLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => api.get('/workflows').then(res => res.data),
  })

  if (statsLoading || execLoading || workflowsLoading) {
    return <DashboardSkeleton />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your automation environment
        </p>
      </div>
      <StatsCards stats={stats} />
      <div className="grid gap-6 md:grid-cols-2">
        <RecentExecutions executions={recentExecutions} />
        <WorkflowList workflows={workflows} />
      </div>
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        <Skeleton className="h-96" />
        <Skeleton className="h-96" />
      </div>
    </div>
  )
}