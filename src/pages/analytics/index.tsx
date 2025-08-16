import React from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowRight, TrendingUp, BarChart3, Activity, Database } from 'lucide-react'
import Link from 'next/link'

const analyticsPages = [
  {
    key: 'bond_issuance',
    name: 'Bond Issuance',
    description: 'Analyze debt financing patterns and trends',
    icon: TrendingUp,
    color: 'blue',
    href: '/analytics/bond-issuance'
  },
  {
    key: 'bdc_discount',
    name: 'BDC Discount',
    description: 'Monitor BDC market stress and performance',
    icon: BarChart3,
    color: 'green',
    href: '/analytics/bdc-discount'
  },
  {
    key: 'credit_fund',
    name: 'Credit Funds',
    description: 'Track private capital flows and fund activity',
    icon: Activity,
    color: 'purple',
    href: '/analytics/credit-funds'
  },
  {
    key: 'bank_provision',
    name: 'Bank Provisions',
    description: 'Analyze banking sector risk assessment',
    icon: Database,
    color: 'red',
    href: '/analytics/bank-provisions'
  },
  {
    key: 'correlations',
    name: 'Cross-Metric Correlations',
    description: 'Comprehensive analysis of boom-bust cycle indicators',
    icon: BarChart3,
    color: 'yellow',
    href: '/analytics/correlations'
  }
]

export default function AnalyticsIndex() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Deep dive analysis of AI datacenter investment cycle indicators</p>
        </div>

        {/* Analytics Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Analytics Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-semibold mb-2">What You'll Find:</h4>
                <ul className="text-gray-600 space-y-1">
                  <li>• Category breakdowns by player type</li>
                  <li>• Cross-metric correlation analysis</li>
                  <li>• Red flag detection and insights</li>
                  <li>• Leading indicator identification</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Key Insights:</h4>
                <ul className="text-gray-600 space-y-1">
                  <li>• Debt issuance patterns and risks</li>
                  <li>• Market stress indicators</li>
                  <li>• Capital flow trends</li>
                  <li>• Banking sector risk assessment</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Analytics Pages Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {analyticsPages.map((page) => {
            const IconComponent = page.icon
            const colorClasses = {
              blue: 'bg-blue-100 text-blue-600',
              green: 'bg-green-100 text-green-600',
              purple: 'bg-purple-100 text-purple-600',
              red: 'bg-red-100 text-red-600',
              yellow: 'bg-yellow-100 text-yellow-600'
            }
            return (
              <Card key={page.key} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${colorClasses[page.color as keyof typeof colorClasses]}`}>
                      <IconComponent className="h-6 w-6" />
                    </div>
                    <div>
                      <CardTitle className="text-xl">{page.name}</CardTitle>
                      <p className="text-sm text-gray-600">{page.description}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Link href={page.href}>
                    <Button className="w-full">
                      View Analytics
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            )
          })}
        </div>


      </div>
    </DashboardLayout>
  )
}
