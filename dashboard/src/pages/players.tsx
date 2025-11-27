import { useState, useEffect } from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable, Column } from '@/components/ui/data-table'
import { AddCompanyForm } from '@/components/ui/add-company-form'
import { 
  Building2, 
  Database, 
  DollarSign, 
  ExternalLink,
  Plus,
  RefreshCw,
  Clock
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
  lastUpdate?: string
  debtIssuance?: number
  datacenterCapacity?: string
  aiInvestment?: string
}

interface MarketCapData {
  ticker: string
  name: string
  category: string
  market_cap: number
  market_cap_formatted: string
  price?: number
  currency: string
  timestamp: string
}

const initialCompanies: Company[] = [
  // Demand Side - Tech Giants
  {
    id: 'amazon',
    name: 'Amazon',
    ticker: 'AMZN',
    category: 'demand',
    subcategory: 'Cloud & AI Services',
    description: 'AWS cloud infrastructure and AI services demand',
    marketCap: '$1.8T',
    status: 'active',
    aiInvestment: '$10B+',
    datacenterCapacity: 'Global network'
  },
  {
    id: 'google',
    name: 'Alphabet (Google)',
    ticker: 'GOOGL',
    category: 'demand',
    subcategory: 'Cloud & AI Services',
    description: 'Google Cloud and AI research infrastructure',
    marketCap: '$1.7T',
    status: 'active',
    aiInvestment: '$8B+',
    datacenterCapacity: 'Global network'
  },
  {
    id: 'meta',
    name: 'Meta Platforms',
    ticker: 'META',
    category: 'demand',
    subcategory: 'Social Media & AI',
    description: 'AI research and social media infrastructure',
    marketCap: '$1.2T',
    status: 'active',
    aiInvestment: '$15B+',
    datacenterCapacity: 'Global network'
  },
  {
    id: 'microsoft',
    name: 'Microsoft',
    ticker: 'MSFT',
    category: 'demand',
    subcategory: 'Cloud & AI Services',
    description: 'Azure cloud and OpenAI partnership infrastructure',
    marketCap: '$2.8T',
    status: 'active',
    aiInvestment: '$13B+',
    datacenterCapacity: 'Global network'
  },
  {
    id: 'nvidia',
    name: 'NVIDIA',
    ticker: 'NVDA',
    category: 'demand',
    subcategory: 'AI Hardware',
    description: 'AI chip demand and own datacenter needs',
    marketCap: '$1.1T',
    status: 'active',
    aiInvestment: '$5B+',
    datacenterCapacity: 'Internal + cloud'
  },
  {
    id: 'tesla',
    name: 'Tesla',
    ticker: 'TSLA',
    category: 'demand',
    subcategory: 'Automotive & AI',
    description: 'Autonomous driving AI and robotics infrastructure',
    marketCap: '$800B',
    status: 'active',
    aiInvestment: '$3B+',
    datacenterCapacity: 'Internal + cloud'
  },
  {
    id: 'x-corp',
    name: 'X Corp (Twitter)',
    ticker: 'X',
    category: 'demand',
    subcategory: 'Social Media & AI',
    description: 'Social media platform with AI content moderation and recommendation systems',
    marketCap: 'Private',
    status: 'active',
    aiInvestment: '$1B+',
    datacenterCapacity: 'Global network'
  },
  {
    id: 'amd',
    name: 'Advanced Micro Devices',
    ticker: 'AMD',
    category: 'demand',
    subcategory: 'AI Hardware',
    description: 'AI chip manufacturer competing with NVIDIA, supplying datacenter GPUs and CPUs for AI workloads',
    marketCap: '$250B',
    status: 'active',
    aiInvestment: '$2B+',
    datacenterCapacity: 'Internal + cloud'
  },
  {
    id: 'broadcom',
    name: 'Broadcom',
    ticker: 'AVGO',
    category: 'demand',
    subcategory: 'AI Hardware',
    description: 'Semiconductor company providing networking chips and infrastructure for AI datacenters',
    marketCap: '$600B',
    status: 'active',
    aiInvestment: '$3B+',
    datacenterCapacity: 'Internal + cloud'
  },
  {
    id: 'tsmc',
    name: 'Taiwan Semiconductor',
    ticker: 'TSM',
    category: 'demand',
    subcategory: 'AI Hardware',
    description: 'World\'s largest semiconductor foundry, manufacturing AI chips for NVIDIA, AMD, and other tech giants',
    marketCap: '$700B',
    status: 'active',
    aiInvestment: '$4B+',
    datacenterCapacity: 'Internal + cloud'
  },
  {
    id: 'openai',
    name: 'OpenAI',
    ticker: 'Private',
    category: 'demand',
    subcategory: 'AI Research',
    description: 'Leading AI research company behind ChatGPT, requiring massive compute infrastructure for training and inference',
    marketCap: 'Private ($80B+ valuation)',
    status: 'active',
    aiInvestment: '$10B+',
    datacenterCapacity: 'Global network'
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    ticker: 'Private',
    category: 'demand',
    subcategory: 'AI Research',
    description: 'AI safety company behind Claude, requiring significant compute resources for large language model training',
    marketCap: 'Private ($30B+ valuation)',
    status: 'active',
    aiInvestment: '$5B+',
    datacenterCapacity: 'Global network'
  },
  {
    id: 'palantir',
    name: 'Palantir',
    ticker: 'PLTR',
    category: 'demand',
    subcategory: 'Enterprise Software',
    description: 'Data analytics and AI platform company, building infrastructure for enterprise AI applications',
    marketCap: '$50B',
    status: 'active',
    aiInvestment: '$2B+',
    datacenterCapacity: 'Internal + cloud'
  },
  {
    id: 'cisco',
    name: 'Cisco Systems',
    ticker: 'CSCO',
    category: 'demand',
    subcategory: 'Enterprise Software',
    description: 'Networking equipment provider for datacenters, supporting AI infrastructure with high-speed networking',
    marketCap: '$200B',
    status: 'active',
    aiInvestment: '$1B+',
    datacenterCapacity: 'Internal + cloud'
  },
  {
    id: 'intel',
    name: 'Intel',
    ticker: 'INTC',
    category: 'demand',
    subcategory: 'AI Hardware',
    description: 'CPU manufacturer expanding into AI chips and datacenter infrastructure for AI workloads',
    marketCap: '$180B',
    status: 'active',
    aiInvestment: '$3B+',
    datacenterCapacity: 'Internal + cloud'
  },

  // Supply Side - Data Center Builders
  {
    id: 'coreweave',
    name: 'CoreWeave',
    category: 'supply',
    subcategory: 'GPU Cloud Infrastructure',
    description: 'Specialized GPU cloud infrastructure for AI workloads',
    status: 'active',
    datacenterCapacity: 'Expanding rapidly',
    debtIssuance: 2300000000 // $2.3B
  },
  {
    id: 'equinix',
    name: 'Equinix',
    ticker: 'EQIX',
    category: 'supply',
    subcategory: 'Data Center REIT',
    description: 'Global data center colocation services',
    marketCap: '$75B',
    status: 'active',
    datacenterCapacity: '250+ data centers',
    debtIssuance: 15000000000 // $15B
  },
  {
    id: 'digital-realty',
    name: 'Digital Realty',
    ticker: 'DLR',
    category: 'supply',
    subcategory: 'Data Center REIT',
    description: 'Data center real estate investment trust',
    marketCap: '$45B',
    status: 'active',
    datacenterCapacity: '300+ facilities',
    debtIssuance: 18000000000 // $18B
  },
  {
    id: 'cyrusone',
    name: 'CyrusOne',
    ticker: 'CONE',
    category: 'supply',
    subcategory: 'Data Center REIT',
    description: 'Data center REIT focused on hyperscale and enterprise customers, providing colocation and interconnection services',
    marketCap: '$12B',
    status: 'active',
    datacenterCapacity: '50+ data centers',
    debtIssuance: 4000000000 // $4B
  },
  {
    id: 'iron-mountain-data',
    name: 'Iron Mountain Data Centers',
    ticker: 'IRM',
    category: 'supply',
    subcategory: 'Data Center REIT',
    description: 'Data center division of Iron Mountain, providing colocation and interconnection services for enterprise customers',
    marketCap: '$25B',
    status: 'active',
    datacenterCapacity: '15+ data centers',
    debtIssuance: 8000000000 // $8B
  },
  {
    id: 'qts-realty',
    name: 'QTS Realty Trust',
    ticker: 'QTS',
    category: 'supply',
    subcategory: 'Data Center REIT',
    description: 'Data center REIT providing colocation, cloud, and managed services with focus on hyperscale customers',
    marketCap: '$8B',
    status: 'active',
    datacenterCapacity: '30+ data centers',
    debtIssuance: 3000000000 // $3B
  },
  {
    id: 'coresite',
    name: 'Coresite Realty Corporation',
    ticker: 'COR',
    category: 'supply',
    subcategory: 'Data Center REIT',
    description: 'Data center REIT specializing in interconnection and colocation services, particularly strong in carrier-neutral facilities',
    marketCap: '$6B',
    status: 'active',
    datacenterCapacity: '25+ data centers',
    debtIssuance: 2500000000 // $2.5B
  },
  {
    id: 'switch',
    name: 'Switch',
    ticker: 'SWCH',
    category: 'supply',
    subcategory: 'Data Center Infrastructure',
    description: 'Technology infrastructure company operating data centers with focus on sustainability and high-density computing',
    marketCap: '$4B',
    status: 'active',
    datacenterCapacity: '4 major campuses',
    debtIssuance: 1500000000 // $1.5B
  },
  {
    id: 'vantage-data',
    name: 'Vantage Data Centers',
    category: 'supply',
    subcategory: 'Data Center Infrastructure',
    description: 'Private data center company focused on hyperscale cloud and AI workloads, rapidly expanding global footprint',
    marketCap: 'Private',
    status: 'active',
    datacenterCapacity: '25+ data centers',
    debtIssuance: 5000000000 // $5B
  },

  // Financing Side - Institutional Banks
  {
    id: 'jpmorgan-chase',
    name: 'JPMorgan Chase',
    ticker: 'JPM',
    category: 'financing',
    subcategory: 'Institutional Banks',
    description: 'Largest US bank by market cap, major lender to technology and infrastructure companies, including AI datacenter financing',
    marketCap: '$500B',
    status: 'active',
    debtIssuance: 50000000000 // $50B
  },
  {
    id: 'goldman-sachs',
    name: 'Goldman Sachs',
    ticker: 'GS',
    category: 'financing',
    subcategory: 'Institutional Banks',
    description: 'Leading investment bank with significant technology and infrastructure lending, including AI datacenter financing',
    marketCap: '$120B',
    status: 'active',
    debtIssuance: 30000000000 // $30B
  },
  {
    id: 'bank-of-america',
    name: 'Bank of America',
    ticker: 'BAC',
    category: 'financing',
    subcategory: 'Institutional Banks',
    description: 'Major US bank with extensive commercial lending to technology and infrastructure sectors',
    marketCap: '$250B',
    status: 'active',
    debtIssuance: 40000000000 // $40B
  },
  {
    id: 'wells-fargo',
    name: 'Wells Fargo',
    ticker: 'WFC',
    category: 'financing',
    subcategory: 'Institutional Banks',
    description: 'Large US bank with commercial lending to technology and infrastructure companies',
    marketCap: '$180B',
    status: 'active',
    debtIssuance: 25000000000 // $25B
  },
  {
    id: 'citigroup',
    name: 'Citigroup',
    ticker: 'C',
    category: 'financing',
    subcategory: 'Institutional Banks',
    description: 'Global bank with significant technology and infrastructure lending operations',
    marketCap: '$100B',
    status: 'active',
    debtIssuance: 20000000000 // $20B
  },
  {
    id: 'barclays',
    name: 'Barclays',
    ticker: 'BCS',
    category: 'financing',
    subcategory: 'Institutional Banks',
    description: 'UK-based global bank with technology and infrastructure lending, including AI datacenter financing',
    marketCap: '$35B',
    status: 'active',
    debtIssuance: 15000000000 // $15B
  },
  {
    id: 'deutsche-bank',
    name: 'Deutsche Bank',
    ticker: 'DB',
    category: 'financing',
    subcategory: 'Institutional Banks',
    description: 'German global bank with technology and infrastructure lending operations',
    marketCap: '$25B',
    status: 'active',
    debtIssuance: 12000000000 // $12B
  },
  {
    id: 'hsbc',
    name: 'HSBC',
    ticker: 'HSBC',
    category: 'financing',
    subcategory: 'Institutional Banks',
    description: 'UK-based global bank with extensive technology and infrastructure lending operations',
    marketCap: '$150B',
    status: 'active',
    debtIssuance: 35000000000 // $35B
  },

  // Financing Side - Major BDCs
  {
    id: 'ares-capital',
    name: 'Ares Capital',
    ticker: 'ARCC',
    category: 'financing',
    subcategory: 'Technology BDC',
    description: 'Business development company focused on technology lending',
    marketCap: '$12B',
    status: 'active',
    debtIssuance: 5000000000 // $5B
  },
  {
    id: 'blackstone-credit',
    name: 'Blackstone Private Credit',
    category: 'financing',
    subcategory: 'Private Credit',
    description: 'Private credit arm of Blackstone Group',
    status: 'active',
    debtIssuance: 8000000000 // $8B
  },
  {
    id: 'kkr-credit',
    name: 'KKR Credit',
    category: 'financing',
    subcategory: 'Private Credit',
    description: 'Credit and lending division of KKR',
    status: 'active',
    debtIssuance: 6000000000 // $6B
  },
  {
    id: 'main-street-capital',
    name: 'Main Street Capital',
    ticker: 'MAIN',
    category: 'financing',
    subcategory: 'Technology BDC',
    description: 'Diversified portfolio with strategic investments in technology and infrastructure, including data center operations and cloud services',
    marketCap: '$3.5B',
    status: 'active',
    debtIssuance: 2500000000 // $2.5B
  },
  {
    id: 'hercules-capital',
    name: 'Hercules Capital',
    ticker: 'HTGC',
    category: 'financing',
    subcategory: 'Venture Lending BDC',
    description: 'Specializes in venture lending to high-growth tech and life sciences companies, including machine learning, data analytics, and infrastructure software for AI applications',
    marketCap: '$2.8B',
    status: 'active',
    debtIssuance: 1800000000 // $1.8B
  },
  {
    id: 'blue-owl-capital',
    name: 'Blue Owl Capital Corp',
    ticker: 'OBDC',
    category: 'financing',
    subcategory: 'Enterprise Technology BDC',
    description: 'Finances large enterprise technology and infrastructure deals, including cloud and data storage companies required for large AI workloads',
    marketCap: '$5.2B',
    status: 'active',
    debtIssuance: 3500000000 // $3.5B
  },
  {
    id: 'trinity-capital',
    name: 'Trinity Capital',
    ticker: 'TRIN',
    category: 'financing',
    subcategory: 'Venture Lending BDC',
    description: 'Lends to venture-backed tech companies developing scalable data solutions, automation, and supporting tools for AI deployment',
    marketCap: '$1.2B',
    status: 'active',
    debtIssuance: 800000000 // $800M
  },

  // Financing Side - Major Private Equity
  {
    id: 'blackstone-group',
    name: 'Blackstone Group',
    ticker: 'BX',
    category: 'financing',
    subcategory: 'Private Equity',
    description: 'Global private equity firm with significant investments in data centers and technology infrastructure',
    marketCap: '$150B',
    status: 'active',
    debtIssuance: 25000000000 // $25B
  },
  {
    id: 'kkr-co',
    name: 'KKR & Co',
    ticker: 'KKR',
    category: 'financing',
    subcategory: 'Private Equity',
    description: 'Global investment firm with technology and infrastructure investment focus',
    marketCap: '$80B',
    status: 'active',
    debtIssuance: 20000000000 // $20B
  },
  {
    id: 'apollo-global',
    name: 'Apollo Global Management',
    ticker: 'APO',
    category: 'financing',
    subcategory: 'Private Equity',
    description: 'Alternative asset manager with significant credit and infrastructure investments',
    marketCap: '$60B',
    status: 'active',
    debtIssuance: 15000000000 // $15B
  },
  {
    id: 'carlyle-group',
    name: 'Carlyle Group',
    ticker: 'CG',
    category: 'financing',
    subcategory: 'Private Equity',
    description: 'Global investment firm with technology and infrastructure investment capabilities',
    marketCap: '$40B',
    status: 'active',
    debtIssuance: 12000000000 // $12B
  },
  {
    id: 'brookfield-asset',
    name: 'Brookfield Asset Management',
    ticker: 'BAM',
    category: 'financing',
    subcategory: 'Infrastructure Investment',
    description: 'Global alternative asset manager with significant infrastructure and renewable energy investments',
    marketCap: '$70B',
    status: 'active',
    debtIssuance: 18000000000 // $18B
  },

  // Financing Side - Venture Capital
  {
    id: 'andreessen-horowitz',
    name: 'Andreessen Horowitz',
    category: 'financing',
    subcategory: 'Venture Capital',
    description: 'Leading venture capital firm with significant investments in AI and infrastructure companies',
    status: 'active',
    debtIssuance: 5000000000 // $5B
  },
  {
    id: 'sequoia-capital',
    name: 'Sequoia Capital',
    category: 'financing',
    subcategory: 'Venture Capital',
    description: 'Venture capital firm with investments in AI, cloud infrastructure, and data center companies',
    status: 'active',
    debtIssuance: 4000000000 // $4B
  },
  {
    id: 'kleiner-perkins',
    name: 'Kleiner Perkins',
    category: 'financing',
    subcategory: 'Venture Capital',
    description: 'Venture capital firm focused on technology investments including AI and infrastructure',
    status: 'active',
    debtIssuance: 3000000000 // $3B
  },
  {
    id: 'accel',
    name: 'Accel',
    category: 'financing',
    subcategory: 'Venture Capital',
    description: 'Venture capital firm with investments in AI, cloud computing, and data infrastructure',
    status: 'active',
    debtIssuance: 2500000000 // $2.5B
  },

  // Financing Side - Infrastructure Funds
  {
    id: 'digital-bridge',
    name: 'DigitalBridge Group',
    ticker: 'DBRG',
    category: 'financing',
    subcategory: 'Infrastructure Investment',
    description: 'Digital infrastructure investment firm specializing in data centers, towers, and fiber',
    marketCap: '$3B',
    status: 'active',
    debtIssuance: 8000000000 // $8B
  },
  {
    id: 'american-tower',
    name: 'American Tower',
    ticker: 'AMT',
    category: 'financing',
    subcategory: 'Infrastructure Investment',
    description: 'Global communications infrastructure company with data center investments',
    marketCap: '$100B',
    status: 'active',
    debtIssuance: 30000000000 // $30B
  },
  {
    id: 'crown-castle',
    name: 'Crown Castle',
    ticker: 'CCI',
    category: 'financing',
    subcategory: 'Infrastructure Investment',
    description: 'Communications infrastructure company with data center and fiber investments',
    marketCap: '$60B',
    status: 'active',
    debtIssuance: 20000000000 // $20B
  },

  // Financing Side - Minor BDCs
  {
    id: 'horizon-technology',
    name: 'Horizon Technology Finance',
    ticker: 'HRZN',
    category: 'financing',
    subcategory: 'Innovation Finance BDC',
    description: 'Focuses on innovative technologies and funds startups involved in digital infrastructure, including AI-adjacent software and hardware',
    marketCap: '$450M',
    status: 'monitoring',
    debtIssuance: 300000000 // $300M
  },
  {
    id: 'ofs-capital',
    name: 'OFS Capital Corp',
    ticker: 'OFS',
    category: 'financing',
    subcategory: 'Diversified BDC',
    description: 'Occasionally invests in infrastructure and cloud technology companies but generally plays a minor role in AI, with more focus on diversified lending',
    marketCap: '$180M',
    status: 'monitoring',
    debtIssuance: 150000000 // $150M
  },
  {
    id: 'tp-venture-growth',
    name: 'TP Venture Growth BDC',
    ticker: 'TPVG',
    category: 'financing',
    subcategory: 'Venture Growth BDC',
    description: 'Backed several tech firms with potential AI infrastructure or software components, but is not primarily an AI infrastructure investor',
    marketCap: '$320M',
    status: 'monitoring',
    debtIssuance: 200000000 // $200M
  }
]

export default function PlayersPage() {
  const [companies, setCompanies] = useState<Company[]>(initialCompanies)
  const [showAddForm, setShowAddForm] = useState(false)
  const [marketCapData, setMarketCapData] = useState<Record<string, MarketCapData>>({})
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [isLoadingMarketCaps, setIsLoadingMarketCaps] = useState(false)
  const [totalMarketCap, setTotalMarketCap] = useState<string>('$8.5T+')

  // Fetch live market cap data
  const fetchMarketCaps = async () => {
    setIsLoadingMarketCaps(true)
    try {
      const response = await fetch('/api/market-caps')
      const data = await response.json()
      
      if (data.success && data.data?.individual_tickers) {
        setMarketCapData(data.data.individual_tickers)
        setLastUpdated(data.data.timestamp)
        
        // Calculate total market cap from live data
        if (data.data.total_market_cap_formatted && data.data.total_market_cap_formatted !== '-') {
          setTotalMarketCap(data.data.total_market_cap_formatted)
        }
      }
    } catch (error) {
      console.error('Error fetching market cap data:', error)
    } finally {
      setIsLoadingMarketCaps(false)
    }
  }

  // Load companies from localStorage on component mount
  useEffect(() => {
    const savedCompanies = localStorage.getItem('ai-datacenter-companies')
    
    if (savedCompanies && savedCompanies !== 'null' && savedCompanies !== 'undefined') {
      try {
        const parsedCompanies = JSON.parse(savedCompanies)
        if (Array.isArray(parsedCompanies) && parsedCompanies.length > 0) {
          setCompanies(parsedCompanies)
        } else {
          setCompanies(initialCompanies)
          localStorage.setItem('ai-datacenter-companies', JSON.stringify(initialCompanies))
        }
      } catch (error) {
        console.error('Error parsing saved companies:', error)
        setCompanies(initialCompanies)
        localStorage.setItem('ai-datacenter-companies', JSON.stringify(initialCompanies))
      }
    } else {
      setCompanies(initialCompanies)
      localStorage.setItem('ai-datacenter-companies', JSON.stringify(initialCompanies))
    }

    // Fetch live market cap data on mount
    fetchMarketCaps()
  }, [])

  // Helper to get live market cap for a ticker
  const getLiveMarketCap = (ticker?: string): string | undefined => {
    if (!ticker || ticker === 'Private') return undefined
    const data = marketCapData[ticker]
    return data?.market_cap_formatted
  }

  const handleAddCompany = (newCompany: Company) => {
    const updatedCompanies = [...companies, newCompany]
    setCompanies(updatedCompanies)
    localStorage.setItem('ai-datacenter-companies', JSON.stringify(updatedCompanies))
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'demand': return <Database className="h-4 w-4 text-blue-600" />
      case 'supply': return <Building2 className="h-4 w-4 text-green-600" />
      case 'financing': return <DollarSign className="h-4 w-4 text-purple-600" />
      default: return <Database className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'monitoring': return 'bg-yellow-100 text-yellow-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatCurrency = (value: number | undefined) => {
    if (!value) return '-'
    if (value >= 1000000000) {
      return `$${(value / 1000000000).toFixed(1)}B`
    }
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`
    }
    return `$${value.toLocaleString()}`
  }

  const columns: Column<Company>[] = [
    {
      key: 'name',
      header: 'Company',
      sortable: true,
      filterable: true,
      width: '200px',
      render: (value, row) => (
        <div className="flex items-center space-x-3">
          {getCategoryIcon(row.category)}
          <div>
            <div className="font-medium">{value}</div>
            {row.ticker && (
              <div className="text-sm text-gray-500 font-mono">{row.ticker}</div>
            )}
          </div>
        </div>
      )
    },
    {
      key: 'category',
      header: 'Category',
      sortable: true,
      filterable: true,
      width: '120px',
      render: (value) => (
        <Badge variant="outline" className="capitalize">
          {value}
        </Badge>
      )
    },
    {
      key: 'subcategory',
      header: 'Subcategory',
      sortable: true,
      filterable: true,
      width: '180px'
    },
    {
      key: 'marketCap',
      header: 'Market Cap',
      sortable: true,
      width: '140px',
      render: (value, row) => {
        const liveValue = getLiveMarketCap(row.ticker)
        if (liveValue) {
          return (
            <div className="flex items-center">
              <span className="text-green-600 font-medium">{liveValue}</span>
              <span className="ml-1 text-xs text-green-500" title="Live data">●</span>
            </div>
          )
        }
        return <span className="text-gray-500">{value || '-'}</span>
      }
    },
    {
      key: 'debtIssuance',
      header: 'Debt Issuance',
      sortable: true,
      width: '140px',
      render: (value) => formatCurrency(value)
    },
    {
      key: 'aiInvestment',
      header: 'AI Investment',
      sortable: true,
      width: '140px',
      render: (value) => value || '-'
    },
    {
      key: 'datacenterCapacity',
      header: 'Capacity',
      sortable: true,
      width: '150px',
      render: (value) => value || '-'
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      filterable: true,
      width: '100px',
      render: (value) => (
        <Badge className={getStatusColor(value)}>
          {value}
        </Badge>
      )
    },
    {
      key: 'description',
      header: 'Description',
      sortable: false,
      width: '300px',
      render: (value) => (
        <div className="max-w-xs truncate" title={value}>
          {value}
        </div>
      )
    }
  ]

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">AI Datacenter Market Players</h1>
            <p className="text-gray-600 mt-1">Track key companies driving the AI infrastructure investment cycle</p>
            {lastUpdated && (
              <div className="flex items-center mt-2 text-xs text-gray-500">
                <Clock className="h-3 w-3 mr-1" />
                Market caps updated: {new Date(lastUpdated).toLocaleString()}
              </div>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              onClick={fetchMarketCaps}
              disabled={isLoadingMarketCaps}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoadingMarketCaps ? 'animate-spin' : ''}`} />
              Refresh Market Caps
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                localStorage.removeItem('ai-datacenter-companies')
                setCompanies(initialCompanies)
                localStorage.setItem('ai-datacenter-companies', JSON.stringify(initialCompanies))
              }}
            >
              Reset Data
            </Button>
            <Button onClick={() => setShowAddForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Company
            </Button>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{companies.filter(c => c.category === 'demand').length}</div>
                <div className="text-sm text-gray-600">Demand Players</div>
                <div className="text-xs text-gray-500">Tech giants driving AI infrastructure needs</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{companies.filter(c => c.category === 'supply').length}</div>
                <div className="text-sm text-gray-600">Supply Players</div>
                <div className="text-xs text-gray-500">Data center builders and operators</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{companies.filter(c => c.category === 'financing').length}</div>
                <div className="text-sm text-gray-600">Financing Players</div>
                <div className="text-xs text-gray-500">BDCs and PE firms providing capital</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Interactive Data Table */}
        <Card>
          <CardHeader>
            <CardTitle>Market Players Database ({companies.length} companies)</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              data={companies}
              columns={columns}
              searchKey="name"
            />
          </CardContent>
        </Card>

        {/* Market Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Market Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Total Debt Issuance</h3>
                <div className="text-3xl font-bold text-blue-600">
                  ${(companies.reduce((sum, c) => sum + (c.debtIssuance || 0), 0) / 1000000000).toFixed(1)}B
                </div>
                <p className="text-sm text-gray-600 mt-1">Combined debt from all tracked companies</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Total Market Cap</h3>
                <div className="text-3xl font-bold text-green-600">
                  {totalMarketCap}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Combined market cap of public companies
                  {Object.keys(marketCapData).length > 0 && (
                    <span className="text-green-500 ml-1">(Live)</span>
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Add Company Form Modal */}
        {showAddForm && (
          <AddCompanyForm
            onAddCompany={handleAddCompany}
            onClose={() => setShowAddForm(false)}
          />
        )}
      </div>
    </DashboardLayout>
  )
}


