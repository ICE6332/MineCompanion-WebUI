import { useMemo } from 'react'
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from 'recharts'

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

type TokenTrendPoint = {
  hour: string
  tokens: number
  timestamp?: string
}

type TokenTrendChartProps = {
  data?: TokenTrendPoint[]
  loading?: boolean
  className?: string
}

export function TokenTrendChart({
  data,
  loading = false,
  className,
}: TokenTrendChartProps) {
  const userTimezone = useMemo(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone
    } catch {
      return 'UTC'
    }
  }, [])

  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      return []
    }

    const localHourMap = new Map<string, number>()

    data.forEach(({ timestamp, hour, tokens }) => {
      let date: Date | null = null

      if (timestamp) {
        const parsed = new Date(timestamp)
        if (!Number.isNaN(parsed.getTime())) {
          date = parsed
        }
      }

      // 兼容缺失时区信息的旧数据：视为 UTC 小时再转换成本地
      if (!date && hour) {
        const utcHour = Number(hour.split(':')[0])
        if (!Number.isNaN(utcHour)) {
          const guess = new Date()
          guess.setUTCHours(utcHour, 0, 0, 0)
          date = guess
        }
      }

      if (!date) return

      const localHour = `${date.getHours().toString().padStart(2, '0')}:00`

      localHourMap.set(localHour, (localHourMap.get(localHour) ?? 0) + tokens)
    })

    const now = new Date()
    const hours: string[] = []

    for (let i = 23; i >= 0; i -= 1) {
      const hour = (now.getHours() - i + 24) % 24
      hours.push(`${hour.toString().padStart(2, '0')}:00`)
    }

    return hours.map((hour) => ({
      hour,
      tokens: localHourMap.get(hour) ?? 0,
    }))
  }, [data])

  const isEmpty = chartData.length === 0

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <CardTitle>Token 消耗趋势</CardTitle>
        <CardDescription>
          最近 24 小时 Token 使用情况（本地时间 {userTimezone}）
        </CardDescription>
      </CardHeader>
      <CardContent className='ps-2'>
        <ResponsiveContainer width='100%' height={350}>
          {loading ? (
            <div className='flex h-full items-center justify-center text-sm text-muted-foreground'>
              加载中...
            </div>
          ) : isEmpty ? (
            <div className='flex h-full items-center justify-center text-sm text-muted-foreground'>
              暂无 Token 数据
            </div>
          ) : (
            <BarChart data={chartData}>
              <XAxis
                dataKey='hour'
                stroke='#888888'
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                direction='ltr'
                stroke='#888888'
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `${value} Token`}
              />
              <Bar
                dataKey='tokens'
                fill='currentColor'
                radius={[4, 4, 0, 0]}
                className='fill-primary'
              />
            </BarChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
