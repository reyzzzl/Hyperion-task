import { Handle, Position } from 'reactflow'

interface CustomNodeProps {
  data: {
    label: string
    config: Record<string, any>
  }
}

function HttpRequestNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white dark:bg-gray-800 border-2 border-blue-500 min-w-[150px]">
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      <div className="flex items-center gap-2">
        <span className="text-lg">🌐</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>
      <div className="text-xs text-gray-500 mt-1">
        {data.config.method || 'GET'} {data.config.url ? data.config.url.substring(0, 30) : ''}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  )
}

function DatabaseQueryNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white dark:bg-gray-800 border-2 border-green-500 min-w-[150px]">
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      <div className="flex items-center gap-2">
        <span className="text-lg">🗄️</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>
      <div className="text-xs text-gray-500 mt-1 truncate max-w-[200px]">
        {data.config.query ? data.config.query.substring(0, 40) : ''}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  )
}

function ConditionNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white dark:bg-gray-800 border-2 border-yellow-500 min-w-[150px] relative">
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      <div className="flex items-center gap-2">
        <span className="text-lg">🔀</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>
      <div className="text-xs text-gray-500 mt-1">
        {data.config.field} {data.config.operator} {data.config.value}
      </div>
      <div className="absolute -left-12 top-[60%] text-xs text-green-600 font-bold">TRUE</div>
      <div className="absolute -right-14 top-[60%] text-xs text-red-600 font-bold">FALSE</div>
      <Handle type="source" position={Position.Left} id="true" style={{ top: '60%', left: -8 }} />
      <Handle type="source" position={Position.Right} id="false" style={{ top: '60%', right: -8 }} />
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  )
}

function SendEmailNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white dark:bg-gray-800 border-2 border-red-500 min-w-[150px]">
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      <div className="flex items-center gap-2">
        <span className="text-lg">📧</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>
      <div className="text-xs text-gray-500 mt-1 truncate max-w-[200px]">
        To: {data.config.to || ''}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  )
}

function DelayNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white dark:bg-gray-800 border-2 border-purple-500 min-w-[150px]">
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      <div className="flex items-center gap-2">
        <span className="text-lg">⏱️</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>
      <div className="text-xs text-gray-500 mt-1">
        {data.config.seconds || 1} seconds
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  )
}

function LLMNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white dark:bg-gray-800 border-2 border-indigo-500 min-w-[150px]">
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      <div className="flex items-center gap-2">
        <span className="text-lg">🤖</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>
      <div className="text-xs text-gray-500 mt-1 truncate max-w-[200px]">
        Model: {data.config.model || 'mistral'}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  )
}

function SlackNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white dark:bg-gray-800 border-2 border-pink-500 min-w-[150px]">
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      <div className="flex items-center gap-2">
        <span className="text-lg">💬</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>
      <div className="text-xs text-gray-500 mt-1 truncate max-w-[200px]">
        {data.config.webhook_url ? 'Webhook configured' : 'No webhook'}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  )
}

function WebhookNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white dark:bg-gray-800 border-2 border-teal-500 min-w-[150px]">
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      <div className="flex items-center gap-2">
        <span className="text-lg">🔗</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>
      <div className="text-xs text-gray-500 mt-1 truncate max-w-[200px]">
        {data.config.url}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  )
}

function TransformDataNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white dark:bg-gray-800 border-2 border-orange-500 min-w-[150px]">
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      <div className="flex items-center gap-2">
        <span className="text-lg">🔄</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>
      <div className="text-xs text-gray-500 mt-1 truncate max-w-[200px]">
        {data.config.template ? 'Template configured' : 'No template'}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  )
}

function LocalFileReadNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white dark:bg-gray-800 border-2 border-gray-500 min-w-[150px]">
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      <div className="flex items-center gap-2">
        <span className="text-lg">📁</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>
      <div className="text-xs text-gray-500 mt-1 truncate max-w-[200px]">
        {data.config.file_path || 'No file path'}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  )
}

const CustomNodes = {
  http_request: HttpRequestNode,
  database_query: DatabaseQueryNode,
  condition: ConditionNode,
  send_email: SendEmailNode,
  delay: DelayNode,
  llm_text_generate: LLMNode,
  slack_send_message: SlackNode,
  webhook_send: WebhookNode,
  transform_data: TransformDataNode,
  local_file_read: LocalFileReadNode,
}

export default CustomNodes