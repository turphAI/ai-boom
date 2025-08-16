import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { cn } from '@/lib/utils'
import { BarChart3, Activity, Users, RefreshCw, LogOut, Home, Database, Building2, TrendingUp } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SidebarProps {
  className?: string
}

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  description: string
}

const navigation: NavItem[] = [
  {
    name: 'Summary',
    href: '/',
    icon: Home,
    description: 'Overview of AI datacenter metrics'
  },
  {
    name: 'System Health',
    href: '/system-health',
    icon: Activity,
    description: 'Monitor system performance and data freshness'
  },
  {
    name: 'Market Players',
    href: '/players',
    icon: Users,
    description: 'Track key companies and their activities'
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: TrendingUp,
    description: 'Deep dive into metric analysis'
  },
  {
    name: 'Advanced Viz',
    href: '/analytics/advanced-visualizations',
    icon: BarChart3,
    description: 'Interactive charts and predictive analytics'
  }
]

export function Sidebar({ className }: SidebarProps) {
  const router = useRouter()
  const currentPath = router.pathname

  const handleRefresh = () => {
    window.location.reload()
  }

  const handleLogout = () => {
    // TODO: Implement logout logic
    console.log('Logout clicked')
  }

  return (
    <div className={cn(
      "flex flex-col h-screen w-64 bg-gray-50 border-r border-gray-200",
      className
    )}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Database className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-lg font-semibold text-gray-900">Boom Bust Sentinel</h1>
            <p className="text-sm text-gray-500">AI Datacenter Monitor</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const isActive = currentPath === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-100 text-blue-700 border border-blue-200"
                  : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              <item.icon className={cn(
                "h-5 w-5",
                isActive ? "text-blue-600" : "text-gray-400"
              )} />
              <div className="flex-1">
                <div className="font-medium">{item.name}</div>
                <div className={cn(
                  "text-xs",
                  isActive ? "text-blue-600" : "text-gray-500"
                )}>
                  {item.description}
                </div>
              </div>
            </Link>
          )
        })}
      </nav>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-200 space-y-2">
        <Button
          onClick={handleRefresh}
          variant="outline"
          size="sm"
          className="w-full justify-start"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Data
        </Button>
        <Button
          onClick={handleLogout}
          variant="ghost"
          size="sm"
          className="w-full justify-start text-gray-600 hover:text-gray-900"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Logout
        </Button>
      </div>
    </div>
  )
}
