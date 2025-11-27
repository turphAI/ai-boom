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
  Clock,
  Info,
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

interface AIInvestmentData {
  ticker: string
  name: string
  category: string
  rd: number | null
  rd_formatted: string
  capex_abs: number | null
  capex_formatted: string
  capex_multiplier: number
  ai_investment_proxy: number | null
  ai_investment_formatted: string
  calculation: {
    formula: string
    rd_component: number
    capex_component: number
  }
}

interface Methodology {
  description: string
  formula: string
  data_sources: string[]
  multipliers: {
    tech_companies: string
    data_centers: string
    financial: string
  }
  limitations: string[]
}

interface DebtData {
  ticker: string
  name: string
  category: string
  total_debt: number | null
  total_debt_formatted: string
  long_term_debt: number | null
  long_term_debt_formatted: string
  current_debt: number | null
  current_debt_formatted: string
  debt_to_equity: number | null
  period: string | null
}

interface DebtMethodology {
  description: string
  metrics: {
    total_debt: string
    long_term_debt: string
    current_debt: string
  }
  data_sources: string[]
  notes: string[]
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
  const [aiInvestmentData, setAIInvestmentData] = useState<Record<string, AIInvestmentData>>({})
  const [debtData, setDebtData] = useState<Record<string, DebtData>>({})
  const [methodology, setMethodology] = useState<Methodology | null>(null)
  const [debtMethodology, setDebtMethodology] = useState<DebtMethodology | null>(null)
  const [showMethodologyDialog, setShowMethodologyDialog] = useState(false)
  const [showDebtMethodologyDialog, setShowDebtMethodologyDialog] = useState(false)
  const [selectedTickerForMethodology, setSelectedTickerForMethodology] = useState<string | null>(null)
  const [selectedTickerForDebtMethodology, setSelectedTickerForDebtMethodology] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [isLoadingMarketCaps, setIsLoadingMarketCaps] = useState(false)
  const [isLoadingAIInvestment, setIsLoadingAIInvestment] = useState(false)
  const [isLoadingDebt, setIsLoadingDebt] = useState(false)
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

  // Fetch AI investment proxy data
  const fetchAIInvestment = async () => {
    setIsLoadingAIInvestment(true)
    try {
      const response = await fetch('/api/ai-investment')
      const data = await response.json()
      
      if (data.success && data.data?.individual_tickers) {
        setAIInvestmentData(data.data.individual_tickers)
        setMethodology(data.data.methodology)
      }
    } catch (error) {
      console.error('Error fetching AI investment data:', error)
    } finally {
      setIsLoadingAIInvestment(false)
    }
  }

  // Fetch debt data
  const fetchDebt = async () => {
    setIsLoadingDebt(true)
    try {
      const response = await fetch('/api/debt')
      const data = await response.json()
      
      if (data.success && data.data?.individual_tickers) {
        setDebtData(data.data.individual_tickers)
        setDebtMethodology(data.data.methodology)
      }
    } catch (error) {
      console.error('Error fetching debt data:', error)
    } finally {
      setIsLoadingDebt(false)
    }
  }

  // Fetch all live data
  const fetchAllData = async () => {
    await Promise.all([fetchMarketCaps(), fetchAIInvestment(), fetchDebt()])
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

    // Fetch live market cap and AI investment data on mount
    fetchAllData()
  }, [])

  // Helper to get live market cap for a ticker
  const getLiveMarketCap = (ticker?: string): string | undefined => {
    if (!ticker || ticker === 'Private') return undefined
    const data = marketCapData[ticker]
    return data?.market_cap_formatted
  }

  // Helper to get live AI investment for a ticker
  const getLiveAIInvestment = (ticker?: string): AIInvestmentData | undefined => {
    if (!ticker || ticker === 'Private') return undefined
    return aiInvestmentData[ticker]
  }

  // Open methodology dialog for a specific ticker
  const openMethodologyDialog = (ticker?: string) => {
    setSelectedTickerForMethodology(ticker || null)
    setShowMethodologyDialog(true)
  }

  // Helper to get live debt for a ticker
  const getLiveDebt = (ticker?: string): DebtData | undefined => {
    if (!ticker || ticker === 'Private') return undefined
    return debtData[ticker]
  }

  // Open debt methodology dialog for a specific ticker
  const openDebtMethodologyDialog = (ticker?: string) => {
    setSelectedTickerForDebtMethodology(ticker || null)
    setShowDebtMethodologyDialog(true)
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
      header: (
        <div className="flex items-center">
          <span>Total Debt</span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              openDebtMethodologyDialog()
            }}
            className="ml-1 p-0.5 rounded hover:bg-gray-200 transition-colors"
            title="Learn about this data"
          >
            <Info className="h-3.5 w-3.5 text-blue-500" />
          </button>
        </div>
      ),
      sortable: true,
      width: '160px',
      render: (value, row) => {
        const liveData = getLiveDebt(row.ticker)
        if (liveData && liveData.total_debt_formatted) {
          return (
            <div className="flex items-center">
              <button
                onClick={() => openDebtMethodologyDialog(row.ticker)}
                className="text-left hover:underline"
                title={`LT: ${liveData.long_term_debt_formatted}, Current: ${liveData.current_debt_formatted}`}
              >
                <span className="text-orange-600 font-medium">{liveData.total_debt_formatted}</span>
              </button>
              <span className="ml-1 text-xs text-orange-500" title="Live data from Yahoo Finance">●</span>
            </div>
          )
        }
        return <span className="text-gray-500">{formatCurrency(value)}</span>
      }
    },
    {
      key: 'aiInvestment',
      header: (
        <div className="flex items-center">
          <span>AI Investment</span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              openMethodologyDialog()
            }}
            className="ml-1 p-0.5 rounded hover:bg-gray-200 transition-colors"
            title="Learn about this proxy calculation"
          >
            <Info className="h-3.5 w-3.5 text-blue-500" />
          </button>
        </div>
      ),
      sortable: true,
      width: '160px',
      render: (value, row) => {
        const liveData = getLiveAIInvestment(row.ticker)
        if (liveData && liveData.ai_investment_formatted) {
          return (
            <div className="flex items-center">
              <button
                onClick={() => openMethodologyDialog(row.ticker)}
                className="text-left hover:underline"
                title={`R&D: ${liveData.rd_formatted} + CapEx: ${liveData.capex_formatted} × ${(liveData.capex_multiplier * 100).toFixed(0)}%`}
              >
                <span className="text-purple-600 font-medium">{liveData.ai_investment_formatted}</span>
              </button>
              <span className="ml-1 text-xs text-purple-500" title="Proxy data from Yahoo Finance">●</span>
            </div>
          )
        }
        return <span className="text-gray-500">{value || '-'}</span>
      }
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
              onClick={fetchAllData}
              disabled={isLoadingMarketCaps || isLoadingAIInvestment || isLoadingDebt}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${(isLoadingMarketCaps || isLoadingAIInvestment || isLoadingDebt) ? 'animate-spin' : ''}`} />
              Refresh Data
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

        {/* AI Investment Methodology Dialog */}
        {showMethodologyDialog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-gray-900">
                    AI Investment Proxy Methodology
                  </h2>
                  <button
                    onClick={() => setShowMethodologyDialog(false)}
                    className="p-1 rounded hover:bg-gray-100"
                  >
                    <X className="h-5 w-5 text-gray-500" />
                  </button>
                </div>

                {/* Selected ticker details */}
                {selectedTickerForMethodology && aiInvestmentData[selectedTickerForMethodology] && (
                  <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <h3 className="font-semibold text-purple-800 mb-2">
                      {aiInvestmentData[selectedTickerForMethodology].name} ({selectedTickerForMethodology})
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">R&D Spending:</span>
                        <span className="font-medium">{aiInvestmentData[selectedTickerForMethodology].rd_formatted}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Capital Expenditure:</span>
                        <span className="font-medium">{aiInvestmentData[selectedTickerForMethodology].capex_formatted}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">CapEx Multiplier:</span>
                        <span className="font-medium">{(aiInvestmentData[selectedTickerForMethodology].capex_multiplier * 100).toFixed(0)}%</span>
                      </div>
                      <hr className="my-2 border-purple-200" />
                      <div className="flex justify-between text-purple-700">
                        <span className="font-medium">AI Investment Proxy:</span>
                        <span className="font-bold">{aiInvestmentData[selectedTickerForMethodology].ai_investment_formatted}</span>
                      </div>
                      <div className="mt-2 text-xs text-gray-500 bg-white p-2 rounded font-mono">
                        {aiInvestmentData[selectedTickerForMethodology].calculation?.formula}
                      </div>
                    </div>
                  </div>
                )}

                {/* Methodology explanation */}
                {methodology && (
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Why is this a proxy?</h3>
                      <p className="text-sm text-gray-600">
                        Companies don't separately report "AI investment" in their financial statements. 
                        We use R&D spending and Capital Expenditure as reasonable proxies for technology 
                        infrastructure spending, with category-specific multipliers.
                      </p>
                    </div>

                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Formula</h3>
                      <div className="bg-gray-100 p-3 rounded font-mono text-sm">
                        {methodology.formula}
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Data Sources</h3>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {methodology.data_sources.map((source, idx) => (
                          <li key={idx}>{source}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Category Multipliers</h3>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div className="bg-blue-50 p-2 rounded">
                          <div className="font-medium text-blue-700">Tech Companies</div>
                          <div className="text-blue-600">{methodology.multipliers.tech_companies}</div>
                        </div>
                        <div className="bg-green-50 p-2 rounded">
                          <div className="font-medium text-green-700">Data Centers</div>
                          <div className="text-green-600">{methodology.multipliers.data_centers}</div>
                        </div>
                        <div className="bg-purple-50 p-2 rounded">
                          <div className="font-medium text-purple-700">Financial</div>
                          <div className="text-purple-600">{methodology.multipliers.financial}</div>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Limitations</h3>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {methodology.limitations.map((limitation, idx) => (
                          <li key={idx}>{limitation}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="pt-4 border-t">
                      <p className="text-xs text-gray-500">
                        Data refreshed daily from Yahoo Finance. Last update: {lastUpdated ? new Date(lastUpdated).toLocaleString() : 'N/A'}
                      </p>
                    </div>
                  </div>
                )}

                <div className="mt-6 flex justify-end">
                  <Button onClick={() => setShowMethodologyDialog(false)}>
                    Close
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Debt Methodology Dialog */}
        {showDebtMethodologyDialog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-gray-900">
                    Total Debt Data
                  </h2>
                  <button
                    onClick={() => setShowDebtMethodologyDialog(false)}
                    className="p-1 rounded hover:bg-gray-100"
                  >
                    <X className="h-5 w-5 text-gray-500" />
                  </button>
                </div>

                {/* Selected ticker details */}
                {selectedTickerForDebtMethodology && debtData[selectedTickerForDebtMethodology] && (
                  <div className="mb-6 p-4 bg-orange-50 rounded-lg border border-orange-200">
                    <h3 className="font-semibold text-orange-800 mb-2">
                      {debtData[selectedTickerForDebtMethodology].name} ({selectedTickerForDebtMethodology})
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Debt:</span>
                        <span className="font-bold text-orange-700">{debtData[selectedTickerForDebtMethodology].total_debt_formatted}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Long-term Debt:</span>
                        <span className="font-medium">{debtData[selectedTickerForDebtMethodology].long_term_debt_formatted}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Current Debt:</span>
                        <span className="font-medium">{debtData[selectedTickerForDebtMethodology].current_debt_formatted}</span>
                      </div>
                      {debtData[selectedTickerForDebtMethodology].debt_to_equity && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Debt-to-Equity Ratio:</span>
                          <span className="font-medium">{debtData[selectedTickerForDebtMethodology].debt_to_equity}x</span>
                        </div>
                      )}
                      {debtData[selectedTickerForDebtMethodology].period && (
                        <div className="mt-2 text-xs text-gray-500">
                          As of: {debtData[selectedTickerForDebtMethodology].period}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Methodology explanation */}
                {debtMethodology && (
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">What is this data?</h3>
                      <p className="text-sm text-gray-600">
                        {debtMethodology.description}
                      </p>
                    </div>

                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Debt Components</h3>
                      <div className="space-y-2">
                        <div className="bg-gray-50 p-3 rounded">
                          <div className="font-medium text-gray-700">Total Debt</div>
                          <div className="text-sm text-gray-600">{debtMethodology.metrics.total_debt}</div>
                        </div>
                        <div className="bg-gray-50 p-3 rounded">
                          <div className="font-medium text-gray-700">Long-term Debt</div>
                          <div className="text-sm text-gray-600">{debtMethodology.metrics.long_term_debt}</div>
                        </div>
                        <div className="bg-gray-50 p-3 rounded">
                          <div className="font-medium text-gray-700">Current Debt</div>
                          <div className="text-sm text-gray-600">{debtMethodology.metrics.current_debt}</div>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Data Sources</h3>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {debtMethodology.data_sources.map((source, idx) => (
                          <li key={idx}>{source}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2">Important Notes</h3>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {debtMethodology.notes.map((note, idx) => (
                          <li key={idx}>{note}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="pt-4 border-t">
                      <p className="text-xs text-gray-500">
                        Data refreshed daily from Yahoo Finance. Last update: {lastUpdated ? new Date(lastUpdated).toLocaleString() : 'N/A'}
                      </p>
                    </div>
                  </div>
                )}

                <div className="mt-6 flex justify-end">
                  <Button onClick={() => setShowDebtMethodologyDialog(false)}>
                    Close
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}


