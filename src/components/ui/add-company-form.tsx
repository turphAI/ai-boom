import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  Plus, 
  Database, 
  Building2, 
  DollarSign,
  X
} from 'lucide-react'

interface Company {
  id: string
  name: string
  ticker?: string
  category: 'demand' | 'supply' | 'financing'
  subcategory: string
  description: string
  marketCap?: string
  status: 'active' | 'monitoring' | 'inactive'
  debtIssuance?: number
  datacenterCapacity?: string
  aiInvestment?: string
}

interface AddCompanyFormProps {
  onAddCompany: (company: Company) => void
  onClose: () => void
}

export function AddCompanyForm({ onAddCompany, onClose }: AddCompanyFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    ticker: '',
    category: 'demand' as 'demand' | 'supply' | 'financing',
    subcategory: '',
    description: '',
    marketCap: '',
    status: 'active' as 'active' | 'monitoring' | 'inactive',
    debtIssuance: '',
    datacenterCapacity: '',
    aiInvestment: ''
  })

  // Predefined subcategories for each category
  const getSubcategoryOptions = (category: string) => {
    switch (category) {
      case 'demand':
        return [
          'Cloud & AI Services',
          'Social Media & AI',
          'AI Hardware',
          'Automotive & AI',
          'Enterprise Software',
          'AI Research'
        ]
      case 'supply':
        return [
          'GPU Cloud Infrastructure',
          'Data Center REIT',
          'Data Center Operator',
          'Infrastructure Provider',
          'Equipment Supplier',
          'Network Services'
        ]
      case 'financing':
        return [
          'Technology BDC',
          'Venture Lending BDC',
          'Enterprise Technology BDC',
          'Innovation Finance BDC',
          'Diversified BDC',
          'Venture Growth BDC',
          'Private Credit',
          'Private Equity'
        ]
      default:
        return []
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const company: Company = {
      id: formData.name.toLowerCase().replace(/\s+/g, '-'),
      name: formData.name,
      ticker: formData.ticker || undefined,
      category: formData.category,
      subcategory: formData.subcategory,
      description: formData.description,
      marketCap: formData.marketCap || undefined,
      status: formData.status,
      debtIssuance: formData.debtIssuance ? parseFloat(formData.debtIssuance) * 1000000000 : undefined,
      datacenterCapacity: formData.datacenterCapacity || undefined,
      aiInvestment: formData.aiInvestment || undefined
    }

    onAddCompany(company)
    onClose()
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'demand': return <Database className="h-4 w-4 text-blue-600" />
      case 'supply': return <Building2 className="h-4 w-4 text-green-600" />
      case 'financing': return <DollarSign className="h-4 w-4 text-purple-600" />
      default: return <Database className="h-4 w-4" />
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Plus className="h-5 w-5" />
              <span>Add New Company</span>
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Name *
                </label>
                <Input
                  required
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Apple Inc."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ticker Symbol
                </label>
                <Input
                  value={formData.ticker}
                  onChange={(e) => setFormData(prev => ({ ...prev, ticker: e.target.value }))}
                  placeholder="e.g., AAPL"
                />
              </div>
            </div>

            {/* Category and Subcategory */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category *
                </label>
                <div className="flex space-x-2">
                  {(['demand', 'supply', 'financing'] as const).map((category) => (
                    <button
                      key={category}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, category }))}
                      className={`flex items-center space-x-1 px-3 py-2 rounded-lg border text-sm font-medium transition-colors ${
                        formData.category === category
                          ? 'bg-blue-100 border-blue-300 text-blue-700'
                          : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      {getCategoryIcon(category)}
                      <span className="capitalize">{category}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Subcategory *
                </label>
                <select
                  required
                  value={formData.subcategory}
                  onChange={(e) => setFormData(prev => ({ ...prev, subcategory: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select subcategory...</option>
                  {getSubcategoryOptions(formData.category).map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description *
              </label>
              <textarea
                required
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Brief description of the company's role in AI datacenter space..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={3}
              />
            </div>

            {/* Financial Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Market Cap
                </label>
                <Input
                  value={formData.marketCap}
                  onChange={(e) => setFormData(prev => ({ ...prev, marketCap: e.target.value }))}
                  placeholder="e.g., $2.5T"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status *
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="active">Active</option>
                  <option value="monitoring">Monitoring</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>

            {/* AI and Infrastructure Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Debt Issuance (Billions)
                </label>
                <Input
                  type="number"
                  step="0.1"
                  value={formData.debtIssuance}
                  onChange={(e) => setFormData(prev => ({ ...prev, debtIssuance: e.target.value }))}
                  placeholder="e.g., 5.2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AI Investment
                </label>
                <Input
                  value={formData.aiInvestment}
                  onChange={(e) => setFormData(prev => ({ ...prev, aiInvestment: e.target.value }))}
                  placeholder="e.g., $2B+"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Datacenter Capacity
                </label>
                <Input
                  value={formData.datacenterCapacity}
                  onChange={(e) => setFormData(prev => ({ ...prev, datacenterCapacity: e.target.value }))}
                  placeholder="e.g., 100+ facilities"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit">
                <Plus className="h-4 w-4 mr-2" />
                Add Company
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
