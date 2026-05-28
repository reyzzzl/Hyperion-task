import { Node } from 'reactflow'
import { useState } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'

interface NodeConfigPanelProps {
  node: Node | null
  onUpdateConfig: (nodeId: string, config: any) => void
  onUpdateLabel: (nodeId: string, label: string) => void
  onClose: () => void
}

export default function NodeConfigPanel({ node, onUpdateConfig, onUpdateLabel, onClose }: NodeConfigPanelProps) {
  const [jsonError, setJsonError] = useState<string | null>(null)

  if (!node) return null

  const config = node.data.config || {}
  const nodeType = node.type

  const updateField = (field: string, value: any) => {
    onUpdateConfig(node.id, { ...config, [field]: value })
  }

  const handleLabelChange = (label: string) => {
    onUpdateLabel(node.id, label)
    if (config.label !== label) {
      onUpdateConfig(node.id, { ...config, label })
    }
  }

  const renderConfigForm = () => {
    switch (nodeType) {
      case 'http_request':
        return (
          <div className="space-y-4">
            <div>
              <Label>Method</Label>
              <Select value={config.method || 'GET'} onValueChange={(v) => updateField('method', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GET">GET</SelectItem>
                  <SelectItem value="POST">POST</SelectItem>
                  <SelectItem value="PUT">PUT</SelectItem>
                  <SelectItem value="DELETE">DELETE</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>URL</Label>
              <Input
                value={config.url || ''}
                onChange={(e) => updateField('url', e.target.value)}
                placeholder="https://api.example.com/endpoint"
              />
            </div>
            <div>
              <Label>Headers (JSON)</Label>
              <Textarea
                value={JSON.stringify(config.headers || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const headers = JSON.parse(e.target.value)
                    updateField('headers', headers)
                    setJsonError(null)
                  } catch {
                    setJsonError('Invalid JSON format')
                  }
                }}
                placeholder='{"Content-Type": "application/json"}'
                rows={4}
              />
              {jsonError && <p className="text-red-500 text-xs">{jsonError}</p>}
            </div>
            <div>
              <Label>Body (JSON)</Label>
              <Textarea
                value={JSON.stringify(config.body || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const body = JSON.parse(e.target.value)
                    updateField('body', body)
                    setJsonError(null)
                  } catch {
                    setJsonError('Invalid JSON format')
                  }
                }}
                placeholder='{"key": "value"}'
                rows={6}
              />
              {jsonError && <p className="text-red-500 text-xs">{jsonError}</p>}
            </div>
          </div>
        )
      case 'database_query':
        return (
          <div className="space-y-4">
            <div>
              <Label>Query</Label>
              <Textarea
                value={config.query || ''}
                onChange={(e) => updateField('query', e.target.value)}
                placeholder="SELECT * FROM users WHERE id = :user_id"
                rows={6}
              />
            </div>
            <div>
              <Label>Parameters (JSON)</Label>
              <Textarea
                value={JSON.stringify(config.params || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const params = JSON.parse(e.target.value)
                    updateField('params', params)
                    setJsonError(null)
                  } catch {
                    setJsonError('Invalid JSON format')
                  }
                }}
                placeholder='{"user_id": 123}'
                rows={4}
              />
              {jsonError && <p className="text-red-500 text-xs">{jsonError}</p>}
            </div>
          </div>
        )
      case 'condition':
        return (
          <div className="space-y-4">
            <div>
              <Label>Field</Label>
              <Input
                value={config.field || ''}
                onChange={(e) => updateField('field', e.target.value)}
                placeholder="{{node_outputs.some_node.value}}"
              />
            </div>
            <div>
              <Label>Operator</Label>
              <Select value={config.operator || 'equals'} onValueChange={(v) => updateField('operator', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="equals">equals</SelectItem>
                  <SelectItem value="not_equals">not equals</SelectItem>
                  <SelectItem value="greater_than">greater than</SelectItem>
                  <SelectItem value="less_than">less than</SelectItem>
                  <SelectItem value="contains">contains</SelectItem>
                  <SelectItem value="not_empty">not empty</SelectItem>
                  <SelectItem value="empty">empty</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Value</Label>
              <Input
                value={config.value || ''}
                onChange={(e) => updateField('value', e.target.value)}
                placeholder="expected value"
              />
            </div>
            <div>
              <Label>True Node (optional)</Label>
              <Input
                value={config.true_node || ''}
                onChange={(e) => updateField('true_node', e.target.value)}
                placeholder="node_id"
              />
            </div>
            <div>
              <Label>False Node (optional)</Label>
              <Input
                value={config.false_node || ''}
                onChange={(e) => updateField('false_node', e.target.value)}
                placeholder="node_id"
              />
            </div>
          </div>
        )
      case 'send_email':
        return (
          <div className="space-y-4">
            <div>
              <Label>To</Label>
              <Input
                value={config.to || ''}
                onChange={(e) => updateField('to', e.target.value)}
                placeholder="recipient@example.com"
              />
            </div>
            <div>
              <Label>Subject</Label>
              <Input
                value={config.subject || ''}
                onChange={(e) => updateField('subject', e.target.value)}
                placeholder="Email subject"
              />
            </div>
            <div>
              <Label>Body (HTML)</Label>
              <Textarea
                value={config.body || ''}
                onChange={(e) => updateField('body', e.target.value)}
                placeholder="<h1>Hello</h1><p>Your order status is: {{node_outputs.query.status}}</p>"
                rows={6}
              />
            </div>
          </div>
        )
      case 'delay':
        return (
          <div className="space-y-4">
            <div>
              <Label>Seconds</Label>
              <Input
                type="number"
                value={config.seconds || 1}
                onChange={(e) => updateField('seconds', parseInt(e.target.value))}
              />
            </div>
          </div>
        )
      case 'llm_text_generate':
        return (
          <div className="space-y-4">
            <div>
              <Label>Model</Label>
              <Input
                value={config.model || 'mistral'}
                onChange={(e) => updateField('model', e.target.value)}
                placeholder="mistral, llama3.1, phi3, etc."
              />
            </div>
            <div>
              <Label>Prompt</Label>
              <Textarea
                value={config.prompt || ''}
                onChange={(e) => updateField('prompt', e.target.value)}
                placeholder="Generate a summary of: {{node_outputs.scraper.data}}"
                rows={6}
              />
            </div>
          </div>
        )
      default:
        return <p className="text-muted-foreground">No configuration available for this node type.</p>
    }
  }

  return (
    <Sheet open={!!node} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-96 overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Configure Node</SheetTitle>
          <SheetDescription>Edit the settings for this node</SheetDescription>
        </SheetHeader>
        <div className="mt-6">
          <div className="mb-4">
            <Label>Label</Label>
            <Input
              value={node.data.label || ''}
              onChange={(e) => handleLabelChange(e.target.value)}
              placeholder="Node label"
            />
          </div>
          {renderConfigForm()}
          <div className="mt-6 pt-4 border-t">
            <div className="flex items-center justify-between">
              <Label>Retry on failure</Label>
              <Switch
                checked={config.retry_enabled !== false}
                onCheckedChange={(checked) => updateField('retry_enabled', checked)}
              />
            </div>
            {config.retry_enabled !== false && (
              <div className="mt-3">
                <Label>Max retries</Label>
                <Input
                  type="number"
                  value={config.retry_count || 3}
                  onChange={(e) => updateField('retry_count', parseInt(e.target.value))}
                  min={0}
                  max={10}
                />
              </div>
            )}
          </div>
          <Button className="w-full mt-6" onClick={onClose}>
            Close
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}