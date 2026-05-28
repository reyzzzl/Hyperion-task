import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'

const nodeTypes = [
  { type: 'http_request', label: 'HTTP Request', icon: '🌐', color: 'bg-blue-500' },
  { type: 'database_query', label: 'Database Query', icon: '🗄️', color: 'bg-green-500' },
  { type: 'send_email', label: 'Send Email', icon: '📧', color: 'bg-red-500' },
  { type: 'condition', label: 'Condition', icon: '🔀', color: 'bg-yellow-500' },
  { type: 'delay', label: 'Delay', icon: '⏱️', color: 'bg-purple-500' },
  { type: 'llm_text_generate', label: 'LLM Generate', icon: '🤖', color: 'bg-indigo-500' },
  { type: 'slack_send_message', label: 'Slack Message', icon: '💬', color: 'bg-pink-500' },
  { type: 'webhook_send', label: 'Webhook', icon: '🔗', color: 'bg-teal-500' },
  { type: 'transform_data', label: 'Transform Data', icon: '🔄', color: 'bg-orange-500' },
  { type: 'local_file_read', label: 'Read File', icon: '📁', color: 'bg-gray-500' },
]

export default function NodePalette() {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <Card className="w-64 rounded-none border-l-0 border-y-0 p-4 overflow-y-auto">
      <h3 className="font-semibold mb-4">Nodes</h3>
      <ScrollArea className="h-full">
        <div className="space-y-2">
          {nodeTypes.map((node) => (
            <div
              key={node.type}
              className="flex items-center gap-3 p-2 rounded-lg border cursor-move hover:bg-muted transition-colors"
              draggable
              onDragStart={(e) => onDragStart(e, node.type)}
            >
              <div className={`w-8 h-8 rounded-md ${node.color} flex items-center justify-center text-white`}>
                {node.icon}
              </div>
              <span className="text-sm">{node.label}</span>
            </div>
          ))}
        </div>
      </ScrollArea>
    </Card>
  )
}