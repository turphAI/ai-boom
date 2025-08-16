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
import { Switch } from '@/components/ui/switch'
import { Settings, MessageSquare, Mail, Bell, TestTube } from 'lucide-react'

const notificationSettingsSchema = z.object({
  emailEnabled: z.boolean(),
  emailAddress: z.string().email().optional(),
  slackEnabled: z.boolean(),
  slackWebhookUrl: z.string().url().optional(),
  telegramEnabled: z.boolean(),
  telegramBotToken: z.string().optional(),
  telegramChatId: z.string().optional(),
})

type NotificationSettingsFormData = z.infer<typeof notificationSettingsSchema>

interface NotificationSettingsProps {
  settings: NotificationSettingsFormData
  onSave: (settings: NotificationSettingsFormData) => void
  onTest: (channel: string) => void
}

export function NotificationSettings({ settings, onSave, onTest }: NotificationSettingsProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isTesting, setIsTesting] = useState<string | null>(null)

  const form = useForm<NotificationSettingsFormData>({
    resolver: zodResolver(notificationSettingsSchema),
    defaultValues: settings,
  })

  const handleSubmit = (data: NotificationSettingsFormData) => {
    onSave(data)
    setIsOpen(false)
  }

  const handleTest = async (channel: string) => {
    setIsTesting(channel)
    try {
      await onTest(channel)
    } finally {
      setIsTesting(null)
    }
  }

  const getChannelStatus = (enabled: boolean, configured: boolean) => {
    if (!enabled) return { status: 'disabled', label: 'Disabled', variant: 'secondary' as const }
    if (!configured) return { status: 'incomplete', label: 'Incomplete', variant: 'destructive' as const }
    return { status: 'active', label: 'Active', variant: 'success' as const }
  }

  const emailStatus = getChannelStatus(
    form.watch('emailEnabled'),
    !!form.watch('emailAddress')
  )
  const slackStatus = getChannelStatus(
    form.watch('slackEnabled'),
    !!form.watch('slackWebhookUrl')
  )
  const telegramStatus = getChannelStatus(
    form.watch('telegramEnabled'),
    !!(form.watch('telegramBotToken') && form.watch('telegramChatId'))
  )

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-lg">Notification Settings</CardTitle>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Configure
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Notification Channels</DialogTitle>
              <DialogDescription>
                Configure how you want to receive alerts when thresholds are breached.
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
                {/* Email Settings */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Mail className="h-4 w-4" />
                      <FormLabel className="text-base">Email Notifications</FormLabel>
                    </div>
                    <FormField
                      control={form.control}
                      name="emailEnabled"
                      render={({ field }) => (
                        <FormItem>
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                  </div>
                  {form.watch('emailEnabled') && (
                    <FormField
                      control={form.control}
                      name="emailAddress"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email Address</FormLabel>
                          <FormControl>
                            <Input
                              placeholder="your-email@example.com"
                              {...field}
                            />
                          </FormControl>
                          <FormDescription>
                            Alerts will be sent to this email address
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  )}
                </div>

                {/* Slack Settings */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <MessageSquare className="h-4 w-4" />
                      <FormLabel className="text-base">Slack Notifications</FormLabel>
                    </div>
                    <FormField
                      control={form.control}
                      name="slackEnabled"
                      render={({ field }) => (
                        <FormItem>
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                  </div>
                  {form.watch('slackEnabled') && (
                    <FormField
                      control={form.control}
                      name="slackWebhookUrl"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Slack Webhook URL</FormLabel>
                          <FormControl>
                            <Input
                              placeholder="https://hooks.slack.com/services/..."
                              {...field}
                            />
                          </FormControl>
                          <FormDescription>
                            Incoming webhook URL from your Slack workspace
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  )}
                </div>

                {/* Telegram Settings */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Bell className="h-4 w-4" />
                      <FormLabel className="text-base">Telegram Notifications</FormLabel>
                    </div>
                    <FormField
                      control={form.control}
                      name="telegramEnabled"
                      render={({ field }) => (
                        <FormItem>
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                  </div>
                  {form.watch('telegramEnabled') && (
                    <div className="space-y-4">
                      <FormField
                        control={form.control}
                        name="telegramBotToken"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Bot Token</FormLabel>
                            <FormControl>
                              <Input
                                placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                                {...field}
                              />
                            </FormControl>
                            <FormDescription>
                              Bot token from @BotFather
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="telegramChatId"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Chat ID</FormLabel>
                            <FormControl>
                              <Input
                                placeholder="123456789"
                                {...field}
                              />
                            </FormControl>
                            <FormDescription>
                              Your Telegram chat ID
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  )}
                </div>

                <DialogFooter>
                  <Button type="submit">Save Settings</Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Email Status */}
          <div className="flex items-center justify-between p-3 rounded-lg border">
            <div className="flex items-center space-x-3">
              <Mail className="h-4 w-4" />
              <div>
                <div className="font-medium">Email</div>
                <div className="text-sm text-muted-foreground">
                  {form.watch('emailAddress') || 'No email configured'}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={emailStatus.variant}>
                {emailStatus.label}
              </Badge>
              {emailStatus.status === 'active' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleTest('email')}
                  disabled={isTesting === 'email'}
                >
                  <TestTube className="h-3 w-3 mr-1" />
                  {isTesting === 'email' ? 'Testing...' : 'Test'}
                </Button>
              )}
            </div>
          </div>

          {/* Slack Status */}
          <div className="flex items-center justify-between p-3 rounded-lg border">
            <div className="flex items-center space-x-3">
              <MessageSquare className="h-4 w-4" />
              <div>
                <div className="font-medium">Slack</div>
                <div className="text-sm text-muted-foreground">
                  {form.watch('slackWebhookUrl') ? 'Webhook configured' : 'No webhook configured'}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={slackStatus.variant}>
                {slackStatus.label}
              </Badge>
              {slackStatus.status === 'active' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleTest('slack')}
                  disabled={isTesting === 'slack'}
                >
                  <TestTube className="h-3 w-3 mr-1" />
                  {isTesting === 'slack' ? 'Testing...' : 'Test'}
                </Button>
              )}
            </div>
          </div>

          {/* Telegram Status */}
          <div className="flex items-center justify-between p-3 rounded-lg border">
            <div className="flex items-center space-x-3">
              <Bell className="h-4 w-4" />
              <div>
                <div className="font-medium">Telegram</div>
                <div className="text-sm text-muted-foreground">
                  {form.watch('telegramBotToken') && form.watch('telegramChatId') 
                    ? 'Bot configured' 
                    : 'No bot configured'}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={telegramStatus.variant}>
                {telegramStatus.label}
              </Badge>
              {telegramStatus.status === 'active' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleTest('telegram')}
                  disabled={isTesting === 'telegram'}
                >
                  <TestTube className="h-3 w-3 mr-1" />
                  {isTesting === 'telegram' ? 'Testing...' : 'Test'}
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
