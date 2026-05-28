import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Workflow, CheckCircle, XCircle, Activity } from 'lucide-react'

interface StatsCardsProps {
  stats: {
    totalWorkflows: number
    activeWorkflows: number
    totalExecutions: number
    successRate: number
  }
}

export function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: 'Total Workflows',
      value: stats.totalWorkflows,
      icon: Workflow,
      color: 'text-blue-500',
    },
    {
      title: 'Active Workflows',
      value: stats.activeWorkflows,
      icon: Activity,
      color: 'text-green-500',
    },
    {
      title: 'Total Executions',
      value: stats.totalExecutions,
      icon: CheckCircle,
      color: 'text-purple-500',
    },
    {
      title: 'Success Rate',
      value: `${stats.successRate}%`,
      icon: XCircle,
      color: 'text-orange-500',
    },
  ]

  return (
    <>
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {card.title}
            </CardTitle>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
          </CardContent>
        </Card>
      ))}
    </>
  )
}