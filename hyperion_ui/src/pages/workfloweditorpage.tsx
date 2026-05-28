import { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Connection,
  Node,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Save, Play, ArrowLeft, Loader2 } from 'lucide-react'
import { useWorkflow, useCreateWorkflow, useUpdateWorkflow, useExecuteWorkflow } from '@/hooks/useWorkflows'
import NodePalette from '@/components/workflow-editor/NodePalette'
import NodeConfigPanel from '@/components/workflow-editor/NodeConfigPanel'
import CustomNodes from '@/components/workflow-editor/CustomNodes'
import { toast } from '@/components/ui/use-toast'
import { v4 as uuidv4 } from 'uuid'

const nodeTypes = CustomNodes

export default function WorkflowEditorPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: existingWorkflow, isLoading: isLoadingWorkflow } = useWorkflow(id || '')
  const createWorkflow = useCreateWorkflow()
  const updateWorkflow = useUpdateWorkflow(id || '')
  const executeWorkflow = useExecuteWorkflow()

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [workflowName, setWorkflowName] = useState('Untitled Workflow')
  const [description, setDescription] = useState('')
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)

  useEffect(() => {
    if (existingWorkflow) {
      setWorkflowName(existingWorkflow.name)
      setDescription(existingWorkflow.description || '')
      const flowNodes = existingWorkflow.nodes.map((node: any) => ({
        id: node.node_id,
        type: node.action_type,
        position: { x: node.position_x || 0, y: node.position_y || 0 },
        data: {
          label: node.action_type.replace(/_/g, ' '),
          config: node.config,
        },
      }))
      const flowEdges = existingWorkflow.nodes
        .filter((node: any) => node.next_node)
        .map((node: any) => ({
          id: `${node.node_id}-${node.next_node}`,
          source: node.node_id,
          target: node.next_node,
        }))
      setNodes(flowNodes)
      setEdges(flowEdges)
    }
  }, [existingWorkflow, setNodes, setEdges])

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const updateNodeConfig = useCallback((nodeId: string, config: any) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, config } }
          : node
      )
    )
  }, [setNodes])

  const updateNodeLabel = useCallback((nodeId: string, label: string) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, label } }
          : node
      )
    )
  }, [setNodes])

  const handleSave = async () => {
    const backendNodes = nodes.map((node) => {
      const outgoingEdge = edges.find(e => e.source === node.id)
      return {
        node_id: node.id,
        action_type: node.type || '',
        config: node.data.config || {},
        next_node: outgoingEdge?.target || null,
        on_error: null,
        retry_count: node.data.config?.retry_count || 3,
        timeout_seconds: 30,
        temp_id: null,
        position_x: Math.round(node.position.x),
        position_y: Math.round(node.position.y),
      }
    })

    const payload = {
      workflow_id: id || uuidv4(),
      name: workflowName,
      description,
      trigger: 'manual',
      trigger_config: {},
      nodes: backendNodes,
      start_node: backendNodes[0]?.node_id || null,
      status: 'active',
    }

    try {
      if (id) {
        await updateWorkflow.mutateAsync(payload)
        toast({ title: 'Workflow updated', description: 'Changes saved successfully' })
      } else {
        const newWorkflow = await createWorkflow.mutateAsync(payload)
        navigate(`/workflows/${newWorkflow.workflow_id}`)
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to save workflow', variant: 'destructive' })
    }
  }

  const handleExecute = async () => {
    if (!id) {
      toast({ title: 'Error', description: 'Please save the workflow first', variant: 'destructive' })
      return
    }
    setIsExecuting(true)
    try {
      await executeWorkflow.mutateAsync({ id, input: {} })
      toast({ title: 'Execution started', description: 'Workflow execution has been triggered' })
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to execute workflow', variant: 'destructive' })
    } finally {
      setIsExecuting(false)
    }
  }

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      const type = event.dataTransfer.getData('application/reactflow')
      if (!type) return

      const position = {
        x: event.clientX - 200,
        y: event.clientY - 100,
      }

      const newNode: Node = {
        id: uuidv4(),
        type,
        position,
        data: { label: type.replace(/_/g, ' '), config: {} },
      }
      setNodes((nds) => nds.concat(newNode))
    },
    [setNodes]
  )

  if (isLoadingWorkflow) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="border-b p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/workflows')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <Input
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="w-64 font-semibold"
            placeholder="Workflow name"
          />
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description"
            className="w-80 h-9 resize-none py-2"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={handleSave} disabled={createWorkflow.isPending || updateWorkflow.isPending}>
            <Save className="mr-2 h-4 w-4" />
            Save
          </Button>
          <Button variant="outline" onClick={handleExecute} disabled={isExecuting || !id}>
            {isExecuting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
            Execute
          </Button>
        </div>
      </div>
      <div className="flex-1 flex overflow-hidden">
        <NodePalette />
        <div className="flex-1 relative" onDragOver={onDragOver} onDrop={onDrop}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
        <NodeConfigPanel
          node={selectedNode}
          onUpdateConfig={updateNodeConfig}
          onUpdateLabel={updateNodeLabel}
          onClose={() => setSelectedNode(null)}
        />
      </div>
    </div>
  )
}