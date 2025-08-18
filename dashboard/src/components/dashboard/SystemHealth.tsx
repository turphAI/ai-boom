import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { SystemHealth as SystemHealthType } from '@/types/dashboard'
import { CheckCircle, AlertCircle, XCircle, Clock } from 'lucide-react'

interface SystemHealthProps {
	healthData: SystemHealthType[]
}

export function SystemHealth({ healthData }: SystemHealthProps) {
	const getStatusIcon = (status: string) => {
		switch (status) {
			case 'healthy':
				return <CheckCircle className="h-4 w-4 text-green-500" />
			case 'degraded':
				return <AlertCircle className="h-4 w-4 text-yellow-500" />
			case 'failed':
				return <XCircle className="h-4 w-4 text-red-500" />
			default:
				return <Clock className="h-4 w-4 text-gray-500" />
		}
	}

	const getStatusVariant = (status: string) => {
		switch (status) {
			case 'healthy': return 'success'
			case 'degraded': return 'warning'
			case 'failed': return 'destructive'
			default: return 'secondary'
		}
	}

	const formatUptime = (uptime: number) => {
		const days = Math.floor(uptime / (24 * 60 * 60))
		const hours = Math.floor((uptime % (24 * 60 * 60)) / (60 * 60))
		const minutes = Math.floor((uptime % (60 * 60)) / 60)
		
		if (days > 0) {
			return `${days}d ${hours}h`
		} else if (hours > 0) {
			return `${hours}h ${minutes}m`
		} else {
			return `${minutes}m`
		}
	}

	const overallStatus = healthData.every(item => item.status === 'healthy') 
		? 'healthy' 
		: healthData.some(item => item.status === 'failed')
		? 'failed'
		: 'degraded'

	return (
		<Card>
			<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
				<CardTitle className="text-lg">System Health</CardTitle>
				<Badge variant={getStatusVariant(overallStatus)}>
					{overallStatus}
				</Badge>
			</CardHeader>
			<CardContent>
				<div className="space-y-4">
					{healthData.map((item, idx) => {
						const key = `${item.dataSource || 'unknown'}-${item.lastUpdate || idx}`
						return (
							<div key={key} className="flex items-center justify-between p-3 rounded-lg border">
								<div className="flex items-center space-x-3">
									{getStatusIcon(item.status)}
									<div>
										<div className="font-medium">{item.dataSource || 'Unknown source'}</div>
										<div className="text-sm text-muted-foreground">
											Last update: {item.lastUpdate ? new Date(item.lastUpdate).toLocaleString() : '—'}
										</div>
										{item.errorMessage && (
											<div className="text-sm text-red-500 mt-1">
												{item.errorMessage}
											</div>
										)}
									</div>
								</div>
								<div className="text-right">
									<Badge variant={getStatusVariant(item.status)} className="mb-1">
										{item.status}
									</Badge>
									<div className="text-xs text-muted-foreground">
										Uptime: {formatUptime(item.uptime)}
									</div>
								</div>
							</div>
						)
					})}
				</div>
			</CardContent>
		</Card>
	)
}