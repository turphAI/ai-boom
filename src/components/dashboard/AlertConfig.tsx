import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertConfig as AlertConfigType } from '@/types/dashboard'
import { Settings, Plus, Edit, Trash2 } from 'lucide-react'

const alertConfigSchema = z.object({
  metricName: z.string().min(1, 'Metric name is required'),
  dataSource: z.string().min(1, 'Data source is required'),
  thresholdType: z.enum(['absolute', 'percentage', 'standard_deviation']),
  thresholdValue: z.number().min(0, 'Threshold must be positive'),
  comparisonPeriod: z.number().min(1, 'Comparison period must be at least 1 day'),
  enabled: z.boolean(),
  channels: z.array(z.string()).min(1, 'At least one notification channel is required'),
})

type AlertConfigFormData = z.infer<typeof alertConfigSchema>

interface AlertConfigProps {
  configs: AlertConfigType[]
  onSave: (config: AlertConfigFormData) => void
  onDelete: (id: string) => void
  onUpdate: (id: string, config: AlertConfigFormData) => void
}

export function AlertConfig({ configs, onSave, onDelete, onUpdate }: AlertConfigProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<AlertConfigType | null>(null)

  const form = useForm<AlertConfigFormData>({
    resolver: zodResolver(alertConfigSchema),
    defaultValues: {
      metricName: '',
      dataSource: '',
      thresholdType: 'percentage',
      thresholdValue: 0,
      comparisonPeriod: 7,
      enabled: true,
      channels: ['email'],
    },
  })

  const handleSubmit = (data: AlertConfigFormData) => {
    if (editingConfig) {
      onUpdate(editingConfig.id, data)
    } else {
      onSave(data)
    }
    setIsOpen(false)
    setEditingConfig(null)
    form.reset()
  }

  const handleEdit = (config: AlertConfigType) => {
    setEditingConfig(config)
    form.reset({
      metricName: config.metricName,
      dataSource: config.dataSource,
      thresholdType: config.thresholdType,
      thresholdValue: config.thresholdValue,
      comparisonPeriod: config.comparisonPeriod,
      enabled: config.enabled,
      channels: config.channels,
    })
    setIsOpen(true)
  }

  const handleClose = () => {
    setIsOpen(false)
    setEditingConfig(null)
    form.reset()
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-lg">Alert Configuration</CardTitle>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Alert
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>
                {editingConfig ? 'Edit Alert Configuration' : 'Create Alert Configuration'}
              </DialogTitle>
              <DialogDescription>
                Configure thresholds and notification settings for market metrics.
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="metricName"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Metric Name</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g., weekly_bond_issuance" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="dataSource"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Data Source</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g., bond_issuance" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="thresholdValue"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Threshold Value</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          step="0.01"
                          {...field} 
                          onChange={(e) => field.onChange(parseFloat(e.target.value))}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="comparisonPeriod"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Comparison Period (days)</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          {...field} 
                          onChange={(e) => field.onChange(parseInt(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription>
                        Number of days to compare against for threshold calculation
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={handleClose}>
                    Cancel
                  </Button>
                  <Button type="submit">
                    {editingConfig ? 'Update' : 'Create'} Alert
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {configs.map((config) => (
            <div key={config.id} className="flex items-center justify-between p-4 rounded-lg border">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h4 className="font-medium">{config.metricName}</h4>
                  <Badge variant={config.enabled ? 'success' : 'secondary'}>
                    {config.enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground">
                  <div>Source: {config.dataSource}</div>
                  <div>Threshold: {config.thresholdValue} ({config.thresholdType})</div>
                  <div>Period: {config.comparisonPeriod} days</div>
                  <div>Channels: {config.channels.join(', ')}</div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEdit(config)}
                >
                  <Edit className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onDelete(config.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
          {configs.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No alert configurations found. Create your first alert to get started.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}