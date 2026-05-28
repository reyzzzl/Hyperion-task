export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'editor' | 'viewer'
}

export interface WorkflowNode {
  node_id: string
  action_type: string
  config: Record<string, any>
  next_node: string | null
  on_error: string | null
  retry_count: number
  timeout_seconds: number
  temp_id: string | null
  position_x: number
  position_y: number
}

export interface Workflow {
  workflow_id: string
  name: string
  description: string
  trigger: string
  trigger_config: Record<string, any>
  nodes: WorkflowNode[]
  start_node: string | null
  status: string
  created_at?: string
  updated_at?: string
}

export interface Execution {
  execution_id: string
  workflow_id: string
  status: 'running' | 'completed' | 'failed' | 'cancelled'
  started_at: string
  completed_at: string | null
  depth: number
  input_data?: any
  output_data?: any
  node_outputs?: any
  errors?: any[]
}

export interface DashboardStats {
  totalWorkflows: number
  activeWorkflows: number
  totalExecutions: number
  successRate: number
}