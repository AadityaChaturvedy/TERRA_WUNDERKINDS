"use client"

import { useEffect, useState, useRef } from "react"
import { createClient } from "@supabase/supabase-js"
import {
  MapPin,
  TrendingUp,
  AlertTriangle,
  FileText,
  Leaf,
  Droplets,
  Sun,
  CloudRain,
  Thermometer,
  Activity,
  BarChart3,
  Download,
  Eye,
  HelpCircle,
  ArrowLeft,
  Bug,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Legend } from "recharts"
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarInset,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import InteractiveMap from "@/components/InteractiveMap"

const SUPABASE_URL = "https://lmmnqygkgacfhnirbwas.supabase.co"
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxtbW5xeWdrZ2FjZmhuaXJid2FzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcxNDAzMzAsImV4cCI6MjA3MjcxNjMzMH0.4q_3cv8kitBnHqEkHHtniNeE64eoC2X0rEJVQ0utxlE"
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

const chartConfig = {
  greenness: {
    label: "Greenness",
    color: "hsl(var(--chart-2))",
  },
  growth: {
    label: "Growth",
    color: "hsl(var(--chart-1))",
  },
}

const tooltipExplanations = {
  greenness: "Indicates how green and healthy crops are.",
  growth: "Represents crop growth and canopy structure.",
  coverage: "Shows how much of the ground is covered by plants.",
  moisture: "Measures crop water content and stress.",
}

// Weather API config (OpenWeatherMap example)
const WEATHER_API_KEY = "76ab130292a14db0162e5f4f12fcbeb0"
const DEFAULT_LOCATION = { lat: 28.6139, lon: 77.2090 } // Delhi, India

// Bounding box for your region
const bounds = [
  [10.57, 79],      // Southwest corner [lat, lon]
  [10.617, 79.047], // Northeast corner [lat, lon]
]

// Map image sources (should be in /public)
const mapImages = {
  Greenness: "/tanjavur_2023-01-05_NDVI.png",
  Coverage: "/tanjavur_2023-01-05_EnhancedTrueColor.png",
  Moisture: "/tanjavur_2023-01-05_NDWI.png",
}

export default function FarmSenseAIDashboard() {
  const [selectedIndex, setSelectedIndex] = useState("Greenness")
  const [activeSection, setActiveSection] = useState("dashboard")
  const [expandedZone, setExpandedZone] = useState<string | null>(null)
  const [showReportPreview, setShowReportPreview] = useState(false)
  const [footerPage, setFooterPage] = useState<string | null>(null)

  // Supabase state
  const [sensorRows, setSensorRows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  // Weather state
  const [weather, setWeather] = useState<{ temp: number; humidity: number; alert?: string } | null>(null)

  useEffect(() => {
    async function fetchSensorData() {
      setLoading(true)
      const { data, error } = await supabase
        .from("sensor_data")
        .select("*")
        .order("timestamp", { ascending: false })
        .limit(100)
      if (!error && data) setSensorRows(data)
      setLoading(false)
    }
    fetchSensorData()

    // Subscribe to realtime changes
    const channel = supabase
      .channel('sensor_data_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'sensor_data' },
        () => {
          fetchSensorData()
        }
      )
      .subscribe()

    // Fallback polling every 10 seconds
    const interval = setInterval(fetchSensorData, 10000)

    return () => {
      supabase.removeChannel(channel)
      clearInterval(interval)
    }
  }, [])

  // Fetch weather data
  useEffect(() => {
    async function fetchWeather() {
      try {
        const res = await fetch(
          `https://api.openweathermap.org/data/2.5/weather?lat=${DEFAULT_LOCATION.lat}&lon=${DEFAULT_LOCATION.lon}&appid=${WEATHER_API_KEY}&units=metric`
        )
        const data = await res.json()
        let alert = undefined
        // Example alert logic
        if (data.weather?.[0]?.main === "Rain") {
          alert = "Heavy rain forecast"
        } else if (data.main?.temp > 38) {
          alert = "Heatwave warning"
        }
        setWeather({
          temp: data.main?.temp,
          humidity: data.main?.humidity,
          alert,
        })
      } catch (e) {
        setWeather(null)
      }
    }
    fetchWeather()
    const interval = setInterval(fetchWeather, 60000)
    return () => clearInterval(interval)
  }, [])

  // Zone data from Supabase
  const zoneData = sensorRows.reduce((acc, row) => {
    if (!row.node_name) return acc
    const zoneId = row.node_name.replace("Node", "")
    if (!acc.find((z: any) => z.id === zoneId)) {
      acc.push({
        id: zoneId,
        name: `${row.node_name} Field`,
        status:
          row.greenness >= 0.8
            ? "healthy"
            : row.greenness <= 0.7
            ? "stress"
            : "moderate",
        greenness: row.greenness ?? row.temperature / 100,
        area: "Unknown",
      })
    }
    return acc
  }, [] as any[])

  // Alerts from Supabase and Weather
  const supabaseAlerts =
    sensorRows
      .filter((row) => row.temperature > 35 || row.soil_moisture < 30)
      .map((row, idx) => ({
        id: idx + 1,
        title: row.temperature > 35 ? "High Temperature Alert" : "Low Moisture Alert",
        zone: row.node_name,
        timestamp: row.timestamp,
        severity: row.temperature > 35 ? "high" : "medium",
        cause: row.temperature > 35 ? "Temperature above safe threshold" : "Soil moisture below safe threshold",
        action: row.temperature > 35 ? "Increase shade/irrigation" : "Increase irrigation",
      })) || []

  const alerts = [
    ...(weather?.alert
      ? [
          {
            id: "weather",
            title: "Weather Alert",
            zone: "All Zones",
            timestamp: new Date().toLocaleTimeString(),
            severity: "high",
            cause: weather.alert,
            action: "Check weather forecast and prepare accordingly",
          },
        ]
      : []),
    ...supabaseAlerts,
  ]

  // Trends from Supabase (greenness, humidity, pest risk)
  const trendData = [...sensorRows]
    .slice(0, 10)
    .reverse()
    .map((row) => ({
      date: row.timestamp ? new Date(row.timestamp).toLocaleTimeString() : "",
      greenness: row.greenness ?? row.temperature / 100, // 0-1 scale
      humidity: row.humidity, // % humidity
      pestRisk: row.npk / 100, // 0-1 scale
      predicted: false,
    }))

  // Historical data for zone (greenness, humidity, pest risk)
  const getZoneHistoricalData = (zoneId: string) =>
    [...sensorRows]
      .filter((row) => row.node_name === `Node${zoneId}`)
      .slice(0, 10)
      .reverse()
      .map((row) => ({
        date: row.timestamp ? new Date(row.timestamp).toLocaleTimeString() : "",
        greenness: row.greenness ?? row.temperature / 100,
        humidity: row.humidity,
      }))

  // Use latest sensor row for metrics (no *100)
  const latestRow = sensorRows[0]
  const getZoneMetrics = (zoneId: string) => {
    const zoneRow = sensorRows.find((row) => row.node_name === `Node${zoneId}`)
    return zoneRow
      ? {
          greenness: zoneRow.greenness ?? zoneRow.temperature / 100,
          moisture: zoneRow.soil_moisture / 100,
          pestRisk: zoneRow.npk / 100,
          temperature: zoneRow.temperature,
          humidity: zoneRow.humidity,
        }
      : {
          greenness: 0.7,
          moisture: 0.6,
          pestRisk: 0.3,
          temperature: 25,
          humidity: 60,
        }
  }

  // Sensor readings for zone
  const getSensorReadings = (zoneId: string) => {
    const zoneRow = sensorRows.find((row) => row.node_name === `Node${zoneId}`)
    if (!zoneRow)
      return [
        { sensor: "Soil Moisture Sensor 1", value: "N/A", status: "Unknown", lastUpdate: "N/A" },
        { sensor: "Temperature Probe", value: "N/A", status: "Unknown", lastUpdate: "N/A" },
        { sensor: "Humidity Sensor", value: "N/A", status: "Unknown", lastUpdate: "N/A" },
        { sensor: "Light Sensor", value: "N/A", status: "Unknown", lastUpdate: "N/A" },
        { sensor: "NPK Sensor", value: "N/A", status: "Unknown", lastUpdate: "N/A" },
      ]
    return [
      {
        sensor: "Soil Moisture Sensor 1",
        value: `${zoneRow.soil_moisture}%`,
        status: zoneRow.soil_moisture > 30 ? "Normal" : "Low",
        lastUpdate: zoneRow.timestamp,
      },
      {
        sensor: "Temperature Probe",
        value: `${zoneRow.temperature}°C`,
        status: zoneRow.temperature < 35 ? "Normal" : "High",
        lastUpdate: zoneRow.timestamp,
      },
      {
        sensor: "Humidity Sensor",
        value: `${zoneRow.humidity}%`,
        status: "Normal",
        lastUpdate: zoneRow.timestamp,
      },
      {
        sensor: "Light Sensor",
        value: `${zoneRow.light} lux`,
        status: zoneRow.light > 800 ? "High" : "Normal",
        lastUpdate: zoneRow.timestamp,
      },
      {
        sensor: "NPK Sensor",
        value: `${zoneRow.npk}`,
        status: zoneRow.npk > 20 ? "Optimal" : "Low",
        lastUpdate: zoneRow.timestamp,
      },
    ]
  }

  const handleZoneClick = (zoneId: string) => {
    setExpandedZone(zoneId)
  }

  const handleBackToDashboard = () => {
    setExpandedZone(null)
  }

  const handlePreviewReport = () => {
    setShowReportPreview(true)
  }

  const handleFooterPageClick = (page: string) => {
    setFooterPage(page)
  }

  const renderReportPreview = () => (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Farm Health Report Preview</h2>
            <Button variant="ghost" size="sm" onClick={() => setShowReportPreview(false)}>
              ×
            </Button>
          </div>
          <p className="text-muted-foreground text-sm mt-1">Generated on {new Date().toLocaleDateString()}</p>
        </div>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-600">78%</div>
                <div className="text-sm text-muted-foreground">Overall Health Score</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">46.1 ha</div>
                <div className="text-sm text-muted-foreground">Total Monitored Area</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-yellow-600">5</div>
                <div className="text-sm text-muted-foreground">Action Items</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Zone Performance Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {zoneData.map((zone) => (
                  <div key={zone.id} className="flex items-center justify-between p-3 border border-border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${getStatusColor(zone.status)}`} />
                      <div>
                        <div className="font-medium">
                          Zone {zone.id} - {zone.name}
                        </div>
                        <div className="text-sm text-muted-foreground">{zone.area}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">Greenness: {zone.greenness}</div>
                      <div className="text-sm text-muted-foreground capitalize">{zone.status}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Key Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="font-medium text-green-800">Zone A - Maintain Current Practices</div>
                  <div className="text-sm text-green-700">
                    Excellent health metrics. Continue current irrigation and nutrient schedule.
                  </div>
                </div>
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="font-medium text-red-800">Zone B - Immediate Attention Required</div>
                  <div className="text-sm text-red-700">
                    Greenness drop detected. Increase irrigation by 20% and monitor for pest activity.
                  </div>
                </div>
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="font-medium text-blue-800">Zone C - Optimize Nutrition</div>
                  <div className="text-sm text-blue-700">Consider NPK supplementation to boost growth metrics.</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        <div className="p-6 border-t border-border flex justify-end gap-3">
          <Button variant="outline" onClick={() => setShowReportPreview(false)}>
            Close Preview
          </Button>
          <Button className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Download Full Report
          </Button>
        </div>
      </div>
    </div>
  )

  const renderFooterPage = (page: string) => {
    const content = {
      about: {
        title: "About TERRA",
        content: (
          <div className="space-y-4">
            <p>
              TERRA (Technology for Environmental Resource and Risk Assessment) is an AI-powered agricultural
              intelligence platform that helps farmers make data-driven decisions. By combining satellite imagery,
              low-cost sensor modules, and machine learning algorithms, TERRA provides real-time insights into soil
              health, moisture levels, pest risks, and weather impacts.
            </p>
            <div>
              <h3 className="font-semibold mb-2">Our mission is simple:</h3>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>Make precision farming accessible and affordable for smallholder farmers.</li>
                <li>Bridge the literacy and technology gap through a highly visual, easy-to-use platform.</li>
                <li>Build a resilient agricultural ecosystem in India and beyond.</li>
              </ul>
            </div>
            <p>
              We believe that every farmer deserves actionable insights, not just raw data — and TERRA is here to
              deliver exactly that.
            </p>
          </div>
        ),
      },
      privacy: {
        title: "Privacy Policy",
        content: (
          <div className="space-y-4">
            <p>
              Your trust is important to us. At TERRA, we are committed to protecting your privacy and ensuring that
              your data is used responsibly.
            </p>
            <div>
              <h3 className="font-semibold mb-2">Data We Collect:</h3>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>Farm location (for satellite insights)</li>
                <li>Sensor readings (soil moisture, temperature, humidity, pest conditions)</li>
                <li>Optional photos or manual entries to improve analytics</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-2">How We Use It:</h3>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>To deliver accurate crop health analysis, pest predictions, and actionable alerts</li>
                <li>To improve our machine learning models for better recommendations</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Your Control:</h3>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>You own your farm data. You can request deletion or download of your data anytime.</li>
                <li>We never share data with third parties without your consent.</li>
              </ul>
            </div>
            <p>We follow strict data encryption standards and comply with relevant data privacy regulations.</p>
          </div>
        ),
      },
      contact: {
        title: "Contact Us",
        content: (
          <div className="space-y-4">
            <p>
              We'd love to hear from you! Whether you're a farmer, agricultural officer, or tech enthusiast, your
              feedback is key to improving TERRA.
            </p>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="font-medium">Email:</span>
                <span className="text-muted-foreground">support@terra-agri.in</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">Phone:</span>
                <span className="text-muted-foreground">+91-XXXXXXXXXX</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">Socials:</span>
                <span className="text-muted-foreground">[LinkedIn, Twitter, Instagram handles if any]</span>
              </div>
            </div>
            <p>You can also reach us directly through the Help & Support tab on the TERRA dashboard.</p>
          </div>
        ),
      },
      credits: {
        title: "Hackathon Credits",
        content: (
          <div className="space-y-4">
            <p>TERRA was designed and developed by Team Wunderkinds as part of Hack Summit 2025.</p>
            <div>
              <h3 className="font-semibold mb-3">Team Members:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 border border-border rounded-lg">
                  <div className="font-medium">Arnav Bharadwaj</div>
                  <div className="text-sm text-muted-foreground">UI/UX & Product Pitch</div>
                </div>
                <div className="p-3 border border-border rounded-lg">
                  <div className="font-medium">Aaditya Chaturvedy</div>
                  <div className="text-sm text-muted-foreground">Machine Learning & Model Training</div>
                </div>
                <div className="p-3 border border-border rounded-lg">
                  <div className="font-medium">Anusheel Singh</div>
                  <div className="text-sm text-muted-foreground">Embedded Systems & IoT Module Design</div>
                </div>
                <div className="p-3 border border-border rounded-lg">
                  <div className="font-medium">Rishabh Shanghai</div>
                  <div className="text-sm text-muted-foreground">Data Analysis & Visualization</div>
                </div>
              </div>
            </div>
          </div>
        ),
      },
    }

    const pageContent = content[page as keyof typeof content]
    if (!pageContent) return null

    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => setFooterPage(null)} className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{pageContent.title}</h1>
          </div>
        </div>
        <Card>
          <CardContent className="p-6">{pageContent.content}</CardContent>
        </Card>
      </div>
    )
  }

  const renderExpandedZoneView = (zoneId: string) => {
    const zone = zoneData.find((z) => z.id === zoneId)
    const metrics = getZoneMetrics(zoneId)
    const historicalData = getZoneHistoricalData(zoneId)
    const sensorReadings = getSensorReadings(zoneId)

    if (!zone) return null

    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={handleBackToDashboard} className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
          <div>
            <h1 className="text-2xl font-bold">
              Zone {zone.id} - {zone.name}
            </h1>
            <p className="text-muted-foreground">{zone.area} • Detailed Analytics</p>
          </div>
        </div>

        <Tabs defaultValue="glance" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="glance">Glance</TabsTrigger>
            <TabsTrigger value="advanced">Advanced</TabsTrigger>
          </TabsList>

          <TabsContent value="glance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Quick Metrics Overview</CardTitle>
                <CardDescription>Current status at a glance</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                  <div className="text-center space-y-3">
                    <div className="h-32 flex items-end justify-center">
                      <div
                        className="w-8 bg-green-500 rounded-t-sm transition-all duration-300 hover:bg-green-600"
                        style={{ height: `${metrics.greenness * 100}%` }}
                      />
                    </div>
                    <div className="space-y-1">
                      <Leaf className="h-6 w-6 mx-auto text-green-600" />
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <p className="text-sm font-medium cursor-help">Greenness</p>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{tooltipExplanations.greenness}</p>
                        </TooltipContent>
                      </Tooltip>
                      <p className="text-xs text-muted-foreground">{(metrics.greenness * 100).toFixed(0)}%</p>
                    </div>
                  </div>

                  <div className="text-center space-y-3">
                    <div className="h-32 flex items-end justify-center">
                      <div
                        className="w-8 bg-blue-500 rounded-t-sm transition-all duration-300 hover:bg-blue-600"
                        style={{ height: `${metrics.moisture * 100}%` }}
                      />
                    </div>
                    <div className="space-y-1">
                      <Droplets className="h-6 w-6 mx-auto text-blue-600" />
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <p className="text-sm font-medium cursor-help">Moisture</p>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{tooltipExplanations.moisture}</p>
                        </TooltipContent>
                      </Tooltip>
                      <p className="text-xs text-muted-foreground">{(metrics.moisture * 100).toFixed(0)}%</p>
                    </div>
                  </div>

                  <div className="text-center space-y-3">
                    <div className="h-32 flex items-end justify-center">
                      <div
                        className="w-8 bg-red-500 rounded-t-sm transition-all duration-300 hover:bg-red-600"
                        style={{ height: `${metrics.pestRisk * 100}%` }}
                      />
                    </div>
                    <div className="space-y-1">
                      <Bug className="h-6 w-6 mx-auto text-red-600" />
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <p className="text-sm font-medium cursor-help">Pest Risk</p>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Current pest infestation risk level</p>
                        </TooltipContent>
                      </Tooltip>
                      <p className="text-xs text-muted-foreground">{(metrics.pestRisk * 100).toFixed(0)}%</p>
                    </div>
                  </div>

                  <div className="text-center space-y-3">
                    <div className="h-32 flex items-end justify-center">
                      <div
                        className="w-8 bg-orange-500 rounded-t-sm transition-all duration-300 hover:bg-orange-600"
                        style={{ height: `${((metrics.temperature - 15) / 20) * 100}%` }}
                      />
                    </div>
                    <div className="space-y-1">
                      <Thermometer className="h-6 w-6 mx-auto text-orange-600" />
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <p className="text-sm font-medium cursor-help">Temperature</p>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Current soil and air temperature</p>
                        </TooltipContent>
                      </Tooltip>
                      <p className="text-xs text-muted-foreground">{metrics.temperature.toFixed(1)}°C</p>
                    </div>
                  </div>

                  <div className="text-center space-y-3">
                    <div className="h-32 flex items-end justify-center">
                      <div
                        className="w-8 bg-cyan-500 rounded-t-sm transition-all duration-300 hover:bg-cyan-600"
                        style={{ height: `${metrics.humidity}%` }}
                      />
                    </div>
                    <div className="space-y-1">
                      <Droplets className="h-6 w-6 mx-auto text-cyan-600" />
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <p className="text-sm font-medium cursor-help">Humidity</p>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Relative humidity in the air</p>
                        </TooltipContent>
                      </Tooltip>
                      <p className="text-xs text-muted-foreground">{metrics.humidity.toFixed(0)}%</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="advanced" className="space-y-6">
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex-1">
                <Card>
                  <CardHeader>
                    <CardTitle>Greenness Over Time</CardTitle>
                    <CardDescription>Last 10 Data inputs</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ChartContainer config={chartConfig} className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={historicalData}>
                          <XAxis dataKey="date" />
                          <YAxis />
                          <ChartTooltip content={<ChartTooltipContent />} />
                          <Line type="monotone" dataKey="greenness" name="Greenness" stroke="#22c55e" strokeWidth={2} />
                          <Legend verticalAlign="top" align="center" wrapperStyle={{ paddingBottom: 16 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </ChartContainer>
                  </CardContent>
                </Card>
              </div>
              <div className="flex-1">
                <Card>
                  <CardHeader>
                    <CardTitle>Live Sensor Readings</CardTitle>
                    <CardDescription>Real-time data from field sensors</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Sensor</TableHead>
                          <TableHead>Current Value</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Last Update</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {sensorReadings.map((reading, index) => (
                          <TableRow key={index}>
                            <TableCell className="font-medium">{reading.sensor}</TableCell>
                            <TableCell>{reading.value}</TableCell>
                            <TableCell>
                              <Badge
                                variant={
                                  reading.status === "Normal" || reading.status === "Optimal" ? "default" : "secondary"
                                }
                              >
                                {reading.status}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-muted-foreground">{reading.lastUpdate}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>AI Predictions</CardTitle>
                  <CardDescription>Next 7 days forecast</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Greenness Trend:</span>
                      <span className="text-green-600 font-medium">↗ Improving</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Pest Risk:</span>
                      <span className="text-yellow-600 font-medium">→ Stable</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Water Needs:</span>
                      <span className="text-blue-600 font-medium">↗ Increasing</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recommendations</CardTitle>
                  <CardDescription>Suggested actions</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-green-800">Increase irrigation by 15% this week</p>
                  </div>
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800">Monitor for aphid activity in morning hours</p>
                  </div>
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">Consider nutrient supplementation next month</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "bg-green-500"
      case "stress":
        return "bg-red-500"
      case "moderate":
        return "bg-yellow-500"
      default:
        return "bg-gray-500"
    }
  }

  // Add this before getPestRiskColor to fix ReferenceError
  const pestRiskLevel = "medium"; // You can set this dynamically if needed

  const getPestRiskColor = () => {
    switch (pestRiskLevel) {
      case "low":
        return "text-green-600 bg-green-50";
      case "medium":
        return "text-yellow-600 bg-yellow-50";
      case "high":
        return "text-red-600 bg-red-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  }

  return (
    <TooltipProvider>
      <SidebarProvider>
        <div className="flex min-h-screen w-full bg-background">
          {!expandedZone && (
            <Sidebar>
              <SidebarHeader className="border-b border-sidebar-border">
                <div className="flex items-center gap-2 px-2 py-2">
                  <Leaf className="h-8 w-8 text-primary" />
                  <div>
                    <h1 className="font-bold text-lg text-sidebar-foreground">TERRA</h1>
                    <p className="text-xs text-sidebar-foreground/70">AI Farm Monitoring</p>
                  </div>
                </div>
              </SidebarHeader>
              <SidebarContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      isActive={activeSection === "dashboard"}
                      onClick={() => setActiveSection("dashboard")}
                    >
                      <BarChart3 className="h-4 w-4" />
                      Dashboard
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton isActive={activeSection === "trends"} onClick={() => setActiveSection("trends")}>
                      <TrendingUp className="h-4 w-4" />
                      Trends
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      isActive={activeSection === "pest-risk"}
                      onClick={() => setActiveSection("pest-risk")}
                    >
                      <AlertTriangle className="h-4 w-4" />
                      Pest Risk
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      isActive={activeSection === "alerts"}
                      onClick={() => setActiveSection("alerts")}
                    >
                      <Activity className="h-4 w-4" />
                      Alerts
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      isActive={activeSection === "reports"}
                      onClick={() => setActiveSection("reports")}
                    >
                      <FileText className="h-4 w-4" />
                      Reports
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarContent>
            </Sidebar>
          )}

          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center gap-2 border-b border-border px-4">
              {!expandedZone && <SidebarTrigger className="-ml-1" />}
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>TERRA</span>
                <span>/</span>
                <span className="text-foreground capitalize">{activeSection.replace("-", " ")}</span>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <div className="flex items-center gap-2 text-sm">
                  <Sun className="h-4 w-4 text-yellow-500" />
                  <span>{weather?.temp ? `${weather.temp}°C` : "24°C"}</span>
                  <Droplets className="h-4 w-4 text-blue-500" />
                  <span>{weather?.humidity ? `${weather.humidity}%` : "65%"}</span>
                </div>
                <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                  <span className="text-sm font-medium text-primary-foreground">JD</span>
                </div>
              </div>
            </header>

            <main className="flex-1 p-6 space-y-6">
              {expandedZone ? (
                renderExpandedZoneView(expandedZone)
              ) : footerPage ? (
                renderFooterPage(footerPage)
              ) : (
                <>
                  {activeSection === "dashboard" && (
                    <>
                      <Card>
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <div>
                              <CardTitle className="flex items-center gap-2">
                                <MapPin className="h-5 w-5" />
                                Farm Overview Map
                              </CardTitle>
                              <CardDescription>Interactive vegetation index visualization</CardDescription>
                            </div>
                            {/* Dropdown menu removed */}
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="h-64 rounded-lg overflow-hidden border">
                            <InteractiveMap
                              imageUrl="/tanjavur_2023-01-05_EnhancedTrueColor.png"
                              bounds={bounds}
                              center={[10.5935, 79.0235]}
                              zoom={15}
                            />
                          </div>
                        </CardContent>
                      </Card>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {zoneData.map((zone) => (
                          <Card
                            key={zone.id}
                            className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-105"
                            onClick={() => handleZoneClick(zone.id)}
                          >
                            <CardHeader className="pb-3">
                              <div className="flex items-center justify-between">
                                <CardTitle className="text-sm font-medium">Zone {zone.id}</CardTitle>
                                <div className={`w-3 h-3 rounded-full ${getStatusColor(zone.status)}`} />
                              </div>
                              <CardDescription className="text-xs">{zone.name}</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <div className="flex items-center gap-1">
                                  <span>Greenness:</span>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <HelpCircle className="h-3 w-3 text-muted-foreground" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      <p>{tooltipExplanations.greenness}</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </div>
                                <span className="font-medium">{zone.greenness}</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span>Area:</span>
                                <span className="font-medium">{zone.area}</span>
                              </div>
                              <Badge
                                variant={
                                  zone.status === "healthy"
                                    ? "default"
                                    : zone.status === "stress"
                                      ? "destructive"
                                      : "secondary"
                                }
                                className="text-xs"
                              >
                                {zone.status}
                              </Badge>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </>
                  )}

                  {activeSection === "trends" && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <TrendingUp className="h-5 w-5" />
                          Vegetation Index Trends
                        </CardTitle>
                        <CardDescription>Last 10 Data inputs</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ChartContainer config={chartConfig} className="h-80">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={trendData}>
                              <XAxis dataKey="date" />
                              <YAxis />
                              <ChartTooltip content={<ChartTooltipContent />} />
                              <Line
                                type="monotone"
                                dataKey="greenness"
                                name="Greenness"
                                stroke="#22c55e"
                                strokeWidth={2}
                                dot={{ fill: "#22c55e", strokeWidth: 2, r: 4 }}
                              />
                              <Line
                                type="monotone"
                                dataKey="humidity"
                                name="Humidity"
                                stroke="#06b6d4"
                                strokeWidth={2}
                                dot={{ fill: "#06b6d4", strokeWidth: 2, r: 4 }}
                              />
                              <Line
                                type="monotone"
                                dataKey="pestRisk"
                                name="Pest Risk"
                                stroke="#ef4444"
                                strokeWidth={2}
                                dot={{ fill: "#ef4444", strokeWidth: 2, r: 4 }}
                              />
                              <Legend verticalAlign="top" align="center" wrapperStyle={{ paddingBottom: 16 }} />
                            </LineChart>
                          </ResponsiveContainer>
                        </ChartContainer>
                      </CardContent>
                    </Card>
                  )}

                  {activeSection === "pest-risk" && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <AlertTriangle className="h-5 w-5" />
                          Pest Risk Assessment
                        </CardTitle>
                        <CardDescription>AI-powered risk analysis based on environmental conditions</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex flex-col items-center justify-center py-12">
                          <img
                            src="/pest_img.png"
                            alt="Pest Risk Map"
                            className="max-w-full h-auto rounded-lg border mb-6"
                            style={{ maxHeight: 400 }}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {activeSection === "alerts" && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Activity className="h-5 w-5" />
                          Recent Alerts
                        </CardTitle>
                        <CardDescription>Anomaly detection and system notifications</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {alerts.map((alert) => (
                            <div key={alert.id} className="flex items-start gap-3 p-4 border border-border rounded-lg">
                              <div className="relative">
                                <AlertTriangle
                                  className={`h-5 w-5 ${alert.severity === "high" ? "text-red-500" : alert.severity === "medium" ? "text-yellow-500" : "text-blue-500"}`}
                                />
                                {alert.severity === "high" && (
                                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                                )}
                              </div>
                              <div className="flex-1 space-y-2">
                                <div className="flex items-center justify-between">
                                  <h4 className="font-medium">{alert.title}</h4>
                                  <Badge variant={getSeverityVariant(alert.severity)} className="text-xs">
                                    {alert.severity}
                                  </Badge>
                                </div>
                                <div className="text-sm text-muted-foreground">
                                  <p>
                                    <strong>{alert.zone}</strong> • {alert.timestamp}
                                  </p>
                                  <p>
                                    <strong>Cause:</strong> {alert.cause}
                                  </p>
                                  <p>
                                    <strong>Action:</strong> {alert.action}
                                  </p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {activeSection === "reports" && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <FileText className="h-5 w-5" />
                          Farm Reports
                        </CardTitle>
                        <CardDescription>Generate comprehensive farm health reports</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-6">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <Card>
                              <CardContent className="p-4">
                                <div className="text-center space-y-2">
                                  <div className="text-2xl font-bold text-green-600">78%</div>
                                  <div className="text-sm text-muted-foreground">Overall Health</div>
                                  <Progress value={78} className="h-2" />
                                </div>
                              </CardContent>
                            </Card>
                            <Card>
                              <CardContent className="p-4">
                                <div className="text-center space-y-2">
                                  <div className="text-2xl font-bold text-blue-600">46.1 ha</div>
                                  <div className="text-sm text-muted-foreground">Total Area</div>
                                  <div className="text-xs text-muted-foreground">4 zones monitored</div>
                                </div>
                              </CardContent>
                            </Card>
                            <Card>
                              <CardContent className="p-4">
                                <div className="text-center space-y-2">
                                  <div className="text-2xl font-bold text-yellow-600">3</div>
                                  <div className="text-sm text-muted-foreground">Active Alerts</div>
                                  <div className="text-xs text-muted-foreground">1 high priority</div>
                                </div>
                              </CardContent>
                            </Card>
                          </div>

                          <div className="bg-muted p-6 rounded-lg">
                            <h3 className="font-medium mb-4">Report Preview</h3>
                            <div className="space-y-3 text-sm">
                              <div className="flex justify-between">
                                <span>Report Period:</span>
                                <span className="font-medium">Last 30 days</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Zones Analyzed:</span>
                                <span className="font-medium">4 zones</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Data Points:</span>
                                <span className="font-medium">1,247 measurements</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Recommendations:</span>
                                <span className="font-medium">5 actionable insights</span>
                              </div>
                            </div>
                          </div>

                          <div className="flex gap-3">
                            <Button className="flex items-center gap-2">
                              <Download className="h-4 w-4" />
                              Generate PDF Report
                            </Button>
                            <Button
                              variant="outline"
                              className="flex items-center gap-2 bg-transparent"
                              onClick={handlePreviewReport}
                            >
                              <Eye className="h-4 w-4" />
                              Preview Report
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              )}
            </main>

            <footer className="border-t border-border p-4">
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => handleFooterPageClick("about")}
                    className="hover:text-foreground transition-colors"
                  >
                    About
                  </button>
                  <button
                    onClick={() => handleFooterPageClick("contact")}
                    className="hover:text-foreground transition-colors"
                  >
                    Contact
                  </button>
                  <button
                    onClick={() => handleFooterPageClick("privacy")}
                    className="hover:text-foreground transition-colors"
                  >
                    Privacy
                  </button>
                  <button
                    onClick={() => handleFooterPageClick("credits")}
                    className="hover:text-foreground transition-colors"
                  >
                    Hackathon Credits
                  </button>
                </div>
                <div>© 2025 TERRA — AI Farm Monitoring Platform</div>
              </div>
            </footer>
          </SidebarInset>
        </div>
        {showReportPreview && renderReportPreview()}
      </SidebarProvider>
    </TooltipProvider>
  )
}
