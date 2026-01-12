"use client"

import { useEffect, useRef, useState } from "react"
import { motion, useScroll, useTransform, useInView } from "framer-motion"
import {
  Zap,
  Shield,
  BarChart3,
  Play,
  ArrowRight,
  Check,
  Monitor,
  Clock,
  Users,
  TrendingUp,
  Sparkles,
  Radio,
  Video,
  Coffee,
  Crown,
  Building2,
  Loader2,
  // eslint-disable-next-line @typescript-eslint/no-deprecated
  Youtube
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { LegalLink } from "@/components/legal-modal"
import { billingApi, PublicPlan } from "@/lib/api/billing"

// ============================================
// ICON MAP FOR DYNAMIC ICONS
// ============================================
const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Sparkles,
  Zap,
  Crown,
  Building2,
}

// ============================================
// ANIMATED COUNTER COMPONENT
// ============================================
function AnimatedCounter({ value, suffix = "", duration = 2 }: { value: number; suffix?: string; duration?: number }) {
  const [count, setCount] = useState(0)
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true })

  useEffect(() => {
    if (isInView) {
      let start = 0
      const end = value
      const incrementTime = (duration * 1000) / end
      const timer = setInterval(() => {
        start += 1
        setCount(start)
        if (start >= end) clearInterval(timer)
      }, incrementTime)
      return () => clearInterval(timer)
    }
  }, [isInView, value, duration])

  return (
    <span ref={ref} className="font-mono">
      {count.toLocaleString()}{suffix}
    </span>
  )
}

// ============================================
// FLOATING CARD COMPONENT (3D EFFECT)
// ============================================
function FloatingCard({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay, ease: "easeOut" }}
      className={className}
    >
      <motion.div
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay }}
        className="h-full"
      >
        {children}
      </motion.div>
    </motion.div>
  )
}

// ============================================
// GRADIENT BLOB COMPONENT
// ============================================
function GradientBlob({ className = "" }: { className?: string }) {
  return (
    <div className={`absolute rounded-full blur-3xl opacity-30 ${className}`} />
  )
}

// ============================================
// FEATURE DATA
// ============================================
const features = [
  {
    icon: Monitor,
    title: "Multi-Channel Dashboard",
    description: "Manage unlimited YouTube channels from one powerful, intuitive dashboard.",
    gradient: "from-blue-500 to-indigo-500",
  },
  {
    icon: Radio,
    title: "24/7 Live Streaming",
    description: "Schedule and run continuous live streams with automatic loop and restart.",
    gradient: "from-red-500 to-orange-500",
  },
  {
    icon: Shield,
    title: "Smart Moderation",
    description: "AI-powered chat moderation keeps your community safe and engaged.",
    gradient: "from-green-500 to-emerald-500",
  },
  {
    icon: BarChart3,
    title: "Real-time Analytics",
    description: "Track views, subscribers, and revenue across all channels instantly.",
    gradient: "from-purple-500 to-pink-500",
  },
  {
    icon: Video,
    title: "Video Library",
    description: "Upload, organize, and manage your video content in the cloud.",
    gradient: "from-cyan-500 to-blue-500",
  },
  {
    icon: Zap,
    title: "Instant Notifications",
    description: "Get alerts for strikes, milestones, and important channel events.",
    gradient: "from-yellow-500 to-orange-500",
  },
]

// ============================================
// HOW IT WORKS STEPS
// ============================================
const steps = [
  {
    number: "01",
    title: "Connect YouTube",
    description: "Link your YouTube channels securely with OAuth 2.0",
    icon: Youtube,
  },
  {
    number: "02",
    title: "Upload Videos",
    description: "Upload your content to our cloud video library",
    icon: Video,
  },
  {
    number: "03",
    title: "Schedule Streams",
    description: "Set up 24/7 live streams with custom schedules",
    icon: Clock,
  },
  {
    number: "04",
    title: "Relax & Monitor",
    description: "Watch your channels grow while we handle the rest",
    icon: Coffee,
  },
]

// ============================================
// PRICING PLANS - Fallback data (prices in dollars for display)
// ============================================
const fallbackPlans = [
  {
    name: "Free",
    slug: "free",
    description: "Get started with basic features",
    price_monthly: 0,
    price_yearly: 0,
    currency: "USD",
    display_features: [
      { name: "1 YouTube Account", included: true },
      { name: "1 GB Storage", included: true },
      { name: "5 Uploads/month", included: true },
      { name: "15 GB Bandwidth/month", included: true },
      { name: "1 Concurrent Stream", included: true },
      { name: "Basic Analytics", included: true },
    ],
    is_popular: false,
    icon: "Sparkles",
    color: "slate",
  },
  {
    name: "Basic",
    slug: "basic",
    description: "Perfect for growing creators",
    price_monthly: 9.99,
    price_yearly: 99.99,
    currency: "USD",
    display_features: [
      { name: "3 YouTube Accounts", included: true },
      { name: "10 GB Storage", included: true },
      { name: "20 Uploads/month", included: true },
      { name: "100 GB Bandwidth/month", included: true },
      { name: "2 Concurrent Streams", included: true },
      { name: "Advanced Analytics", included: true },
    ],
    is_popular: false,
    icon: "Zap",
    color: "blue",
  },
  {
    name: "Pro",
    slug: "pro",
    description: "For professional creators & agencies",
    price_monthly: 29.99,
    price_yearly: 299.99,
    currency: "USD",
    display_features: [
      { name: "10 YouTube Accounts", included: true },
      { name: "50 GB Storage", included: true },
      { name: "100 Uploads/month", included: true },
      { name: "500 GB Bandwidth/month", included: true },
      { name: "5 Concurrent Streams", included: true },
      { name: "Full Analytics Suite", included: true },
    ],
    is_popular: true,
    icon: "Crown",
    color: "violet",
  },
  {
    name: "Enterprise",
    slug: "enterprise",
    description: "For agencies & MCN with custom needs",
    price_monthly: 99.99,
    price_yearly: 999.99,
    currency: "USD",
    display_features: [
      { name: "Unlimited Accounts", included: true },
      { name: "500 GB Storage", included: true },
      { name: "Unlimited Uploads", included: true },
      { name: "5 TB Bandwidth/month", included: true },
      { name: "Unlimited Concurrent Streams", included: true },
      { name: "Priority Support 24/7", included: true },
    ],
    is_popular: false,
    icon: "Building2",
    color: "amber",
  },
]

// ============================================
// STATS DATA
// ============================================
const stats = [
  { value: 10000, suffix: "+", label: "Active Creators" },
  { value: 50, suffix: "M+", label: "Hours Streamed" },
  { value: 99.9, suffix: "%", label: "Uptime" },
  { value: 24, suffix: "/7", label: "Support" },
]


// ============================================
// MAIN LANDING PAGE COMPONENT
// ============================================
export default function Home() {
  const [isYearly, setIsYearly] = useState(false)
  const [plans, setPlans] = useState(fallbackPlans)
  const [plansLoading, setPlansLoading] = useState(true)
  const heroRef = useRef(null)
  const { scrollYProgress } = useScroll()
  const y = useTransform(scrollYProgress, [0, 1], [0, -50])

  // Fetch plans from API
  useEffect(() => {
    async function fetchPlans() {
      try {
        const apiPlans = await billingApi.getPublicPlans()
        if (apiPlans.length > 0) {
          setPlans(apiPlans)
        }
      } catch (error) {
        console.error("Failed to fetch plans, using fallback:", error)
      } finally {
        setPlansLoading(false)
      }
    }
    fetchPlans()
  }, [])

  return (
    <div className="min-h-screen bg-[#F9FAFB] overflow-hidden">
      {/* ============================================ */}
      {/* HEADER / NAVIGATION */}
      {/* ============================================ */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 group">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg blur opacity-50 group-hover:opacity-75 transition-opacity" />
                <div className="relative bg-gradient-to-r from-red-500 to-orange-500 p-2 rounded-lg">
                  <Youtube className="h-5 w-5 text-white" />
                </div>
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                YT Automation
              </span>
            </Link>

            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                Features
              </a>
              <a href="#how-it-works" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                How it Works
              </a>
              <a href="#pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                Pricing
              </a>
            </nav>

            {/* CTA Buttons */}
            <div className="flex items-center gap-3">
              <Link href="/login">
                <Button variant="ghost" className="text-gray-600 hover:text-gray-900">
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white shadow-lg shadow-red-500/25 hover:shadow-red-500/40 transition-all">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* ============================================ */}
      {/* HERO SECTION */}
      {/* ============================================ */}
      <section ref={heroRef} className="relative pt-32 pb-20 lg:pt-40 lg:pb-32 overflow-hidden">
        {/* Background Gradient Blobs */}
        <GradientBlob className="w-[600px] h-[600px] bg-gradient-to-r from-red-200 to-orange-200 -top-40 -right-40" />
        <GradientBlob className="w-[400px] h-[400px] bg-gradient-to-r from-indigo-200 to-purple-200 top-1/2 -left-20" />
        <GradientBlob className="w-[300px] h-[300px] bg-gradient-to-r from-green-200 to-emerald-200 bottom-0 right-1/4" />

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Hero Text */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="text-center lg:text-left"
            >
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Badge className="mb-6 bg-red-50 text-red-600 border-red-200 hover:bg-red-100">
                  <Sparkles className="w-3 h-3 mr-1" />
                  Now with AI-Powered Features
                </Badge>
              </motion.div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-gray-900 leading-tight">
                Automate Your{" "}
                <span className="bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
                  YouTube Channels
                </span>
              </h1>

              <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-xl mx-auto lg:mx-0">
                Stream smarter. Grow faster. Manage multiple channels, schedule 24/7 live streams,
                and monitor everything from one clean dashboard.
              </p>

              <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link href="/register">
                  <Button size="lg" className="w-full sm:w-auto bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white shadow-xl shadow-red-500/25 hover:shadow-red-500/40 transition-all text-lg px-8 py-6">
                    Get Started Free
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
                <Button size="lg" variant="outline" className="w-full sm:w-auto border-gray-300 hover:bg-gray-50 text-lg px-8 py-6">
                  <Play className="mr-2 h-5 w-5" />
                  Watch Demo
                </Button>
              </div>

              {/* Trust Badges */}
              <div className="mt-12 flex items-center gap-8 justify-center lg:justify-start text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-500" />
                  <span>No credit card required</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-500" />
                  <span>Free plan available</span>
                </div>
              </div>
            </motion.div>

            {/* Hero Visual - Dashboard Mockup */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
              className="relative"
            >
              <motion.div style={{ y }} className="relative">
                {/* Main Dashboard Card */}
                <FloatingCard delay={0} className="relative z-10">
                  <div className="bg-white rounded-2xl shadow-2xl shadow-gray-200/50 border border-gray-100 p-4 sm:p-6">
                    {/* Dashboard Header */}
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-red-400" />
                        <div className="w-3 h-3 rounded-full bg-yellow-400" />
                        <div className="w-3 h-3 rounded-full bg-green-400" />
                      </div>
                      <div className="text-xs text-gray-400 font-mono">dashboard.ytautomation.com</div>
                    </div>

                    {/* Stats Row */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-xl p-4">
                        <div className="text-2xl font-bold text-gray-900">12.5K</div>
                        <div className="text-xs text-gray-500">Live Viewers</div>
                      </div>
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4">
                        <div className="text-2xl font-bold text-gray-900">98.2%</div>
                        <div className="text-xs text-gray-500">Uptime</div>
                      </div>
                      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4">
                        <div className="text-2xl font-bold text-gray-900">$2.4K</div>
                        <div className="text-xs text-gray-500">Revenue</div>
                      </div>
                    </div>

                    {/* Stream Preview */}
                    <div className="bg-gray-900 rounded-xl aspect-video flex items-center justify-center relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-red-500/20 to-orange-500/20" />
                      <div className="relative flex items-center gap-2">
                        <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                        <span className="text-white font-medium">LIVE</span>
                      </div>
                    </div>
                  </div>
                </FloatingCard>

                {/* Floating Metric Cards */}
                <FloatingCard delay={0.5} className="absolute -top-4 -right-4 z-20">
                  <div className="bg-white rounded-xl shadow-xl shadow-gray-200/50 border border-gray-100 p-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                        <TrendingUp className="w-4 h-4 text-green-600" />
                      </div>
                      <div>
                        <div className="text-sm font-bold text-gray-900">+24%</div>
                        <div className="text-xs text-gray-500">Growth</div>
                      </div>
                    </div>
                  </div>
                </FloatingCard>

                <FloatingCard delay={0.7} className="absolute -bottom-4 -left-4 z-20">
                  <div className="bg-white rounded-xl shadow-xl shadow-gray-200/50 border border-gray-100 p-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Users className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <div className="text-sm font-bold text-gray-900">5 Channels</div>
                        <div className="text-xs text-gray-500">Connected</div>
                      </div>
                    </div>
                  </div>
                </FloatingCard>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* STATS SECTION */}
      {/* ============================================ */}
      <section className="py-16 bg-white border-y border-gray-100">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <div className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
                  <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                </div>
                <div className="mt-2 text-sm text-gray-600">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* FEATURES SECTION */}
      {/* ============================================ */}
      <section id="features" className="py-24 relative">
        <GradientBlob className="w-[500px] h-[500px] bg-gradient-to-r from-indigo-100 to-purple-100 top-0 left-1/4" />

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <Badge className="mb-4 bg-indigo-50 text-indigo-600 border-indigo-200">
              Features
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
              Everything You Need to{" "}
              <span className="bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">
                Succeed
              </span>
            </h2>
            <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
              Powerful tools designed for YouTube creators who want to scale their channels efficiently.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="h-full bg-white border-gray-100 hover:border-gray-200 hover:shadow-xl hover:shadow-gray-100/50 transition-all duration-300 group cursor-pointer">
                  <CardContent className="p-6">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${feature.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                      <feature.icon className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 text-sm leading-relaxed">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* DASHBOARD PREVIEW SECTION */}
      {/* ============================================ */}
      <section className="py-24 bg-white relative overflow-hidden">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <Badge className="mb-4 bg-green-50 text-green-600 border-green-200">
              Dashboard Preview
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
              A Dashboard That{" "}
              <span className="bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">
                Works for You
              </span>
            </h2>
            <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
              Clean, intuitive, and packed with insights. See everything at a glance.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="relative"
          >
            {/* Browser Frame */}
            <div className="bg-gray-900 rounded-t-2xl p-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <div className="flex-1 ml-4">
                  <div className="bg-gray-800 rounded-lg px-4 py-1.5 text-sm text-gray-400 font-mono max-w-md">
                    app.ytautomation.com/dashboard
                  </div>
                </div>
              </div>
            </div>

            {/* Dashboard Content */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-b-2xl p-6 sm:p-8 border border-gray-200 border-t-0">
              <div className="grid lg:grid-cols-3 gap-6">
                {/* Sidebar */}
                <div className="lg:col-span-1">
                  <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="w-10 h-10 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg flex items-center justify-center">
                        <Youtube className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">My Channels</div>
                        <div className="text-xs text-gray-500">5 connected</div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      {["Gaming Channel", "Tech Reviews", "Music Streams", "Podcast Live", "Tutorials"].map((channel, i) => (
                        <div key={channel} className={`flex items-center gap-3 p-2 rounded-lg ${i === 0 ? "bg-red-50" : "hover:bg-gray-50"} transition-colors cursor-pointer`}>
                          <div className={`w-8 h-8 rounded-lg ${i === 0 ? "bg-red-500" : "bg-gray-200"} flex items-center justify-center`}>
                            <span className="text-xs font-bold text-white">{channel[0]}</span>
                          </div>
                          <span className={`text-sm ${i === 0 ? "font-medium text-gray-900" : "text-gray-600"}`}>{channel}</span>
                          {i === 0 && <div className="ml-auto w-2 h-2 bg-green-500 rounded-full animate-pulse" />}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                  {/* Stats Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                      { label: "Total Views", value: "2.4M", change: "+12%" },
                      { label: "Subscribers", value: "156K", change: "+8%" },
                      { label: "Watch Time", value: "45K hrs", change: "+15%" },
                      { label: "Revenue", value: "$12.5K", change: "+22%" },
                    ].map((stat) => (
                      <div key={stat.label} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                        <div className="text-xs text-gray-500 mb-1">{stat.label}</div>
                        <div className="text-xl font-bold text-gray-900">{stat.value}</div>
                        <div className="text-xs text-green-600 font-medium">{stat.change}</div>
                      </div>
                    ))}
                  </div>

                  {/* Chart Placeholder */}
                  <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-4">
                      <div className="font-semibold text-gray-900">Performance Overview</div>
                      <div className="text-xs text-gray-500">Last 30 days</div>
                    </div>
                    <div className="h-40 flex items-end gap-2">
                      {[40, 65, 45, 80, 55, 90, 70, 85, 60, 95, 75, 88].map((height, i) => (
                        <motion.div
                          key={i}
                          initial={{ height: 0 }}
                          whileInView={{ height: `${height}%` }}
                          viewport={{ once: true }}
                          transition={{ delay: i * 0.05, duration: 0.5 }}
                          className="flex-1 bg-gradient-to-t from-red-500 to-orange-400 rounded-t-sm"
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ============================================ */}
      {/* HOW IT WORKS SECTION */}
      {/* ============================================ */}
      <section id="how-it-works" className="py-24 relative">
        <GradientBlob className="w-[400px] h-[400px] bg-gradient-to-r from-orange-100 to-red-100 bottom-0 right-0" />

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <Badge className="mb-4 bg-orange-50 text-orange-600 border-orange-200">
              How It Works
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
              Get Started in{" "}
              <span className="bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
                4 Simple Steps
              </span>
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15 }}
                className="relative"
              >
                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-12 left-1/2 w-full h-0.5 bg-gradient-to-r from-gray-200 to-gray-100" />
                )}

                <div className="relative bg-white rounded-2xl p-6 border border-gray-100 hover:border-gray-200 hover:shadow-xl hover:shadow-gray-100/50 transition-all duration-300 text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-r from-red-500 to-orange-500 text-white font-bold text-lg mb-4">
                    {step.number}
                  </div>
                  <div className="w-16 h-16 mx-auto mb-4 bg-gray-50 rounded-2xl flex items-center justify-center">
                    <step.icon className="w-8 h-8 text-gray-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h3>
                  <p className="text-sm text-gray-600">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* PRICING SECTION */}
      {/* ============================================ */}
      <section id="pricing" className="py-24 bg-gradient-to-b from-white to-gray-50 relative">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <Badge className="mb-4 bg-purple-50 text-purple-600 border-purple-200">
              Pricing
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
              Simple,{" "}
              <span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
                Transparent Pricing
              </span>
            </h2>
            <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
              Choose the plan that fits your needs. No hidden fees.
            </p>

            {/* Billing Toggle */}
            <div className="mt-8 flex items-center justify-center gap-4">
              <span className={`text-sm font-medium transition-colors ${!isYearly ? "text-gray-900" : "text-gray-400"}`}>Monthly</span>
              <Switch checked={isYearly} onCheckedChange={setIsYearly} />
              <span className={`text-sm font-medium transition-colors ${isYearly ? "text-gray-900" : "text-gray-400"}`}>
                Yearly <Badge variant="secondary" className="ml-1 bg-green-100 text-green-700 text-xs">Save 20%</Badge>
              </span>
            </div>
          </motion.div>

          {plansLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
              {plans.map((plan, index) => {
                const IconComponent = iconMap[plan.icon] || Sparkles
                const isFree = plan.price_monthly === 0
                const price = isYearly ? plan.price_yearly : plan.price_monthly

                // Color schemes based on plan.color from database
                const colorSchemes: Record<string, {
                  border: string
                  shadow: string
                  badge: string
                  iconBg: string
                  button: string
                  checkBg: string
                  checkIcon: string
                }> = {
                  slate: {
                    border: "border-slate-200 hover:border-slate-300",
                    shadow: "hover:shadow-slate-200/50",
                    badge: "bg-slate-500 text-white",
                    iconBg: "bg-gradient-to-br from-slate-500 to-slate-600",
                    button: "bg-slate-600 hover:bg-slate-700 shadow-slate-500/25",
                    checkBg: "bg-slate-100",
                    checkIcon: "text-slate-600",
                  },
                  blue: {
                    border: "border-blue-200 hover:border-blue-300",
                    shadow: "hover:shadow-blue-200/50",
                    badge: "bg-blue-500 text-white",
                    iconBg: "bg-gradient-to-br from-blue-500 to-blue-600",
                    button: "bg-blue-600 hover:bg-blue-700 shadow-blue-500/25",
                    checkBg: "bg-blue-100",
                    checkIcon: "text-blue-600",
                  },
                  violet: {
                    border: "border-red-200 hover:border-red-300",
                    shadow: "shadow-red-500/10 hover:shadow-red-500/20",
                    badge: "bg-gradient-to-r from-red-500 to-orange-500 text-white",
                    iconBg: "bg-gradient-to-br from-red-500 to-orange-500",
                    button: "bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 shadow-red-500/25",
                    checkBg: "bg-red-100",
                    checkIcon: "text-red-600",
                  },
                  amber: {
                    border: "border-amber-200 hover:border-amber-300",
                    shadow: "hover:shadow-amber-200/50",
                    badge: "bg-gradient-to-r from-amber-500 to-orange-500 text-white",
                    iconBg: "bg-gradient-to-br from-amber-500 to-orange-500",
                    button: "bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 shadow-amber-500/25",
                    checkBg: "bg-amber-100",
                    checkIcon: "text-amber-600",
                  },
                }

                const colors = colorSchemes[plan.color] || colorSchemes.slate

                return (
                  <motion.div
                    key={plan.name}
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.1 }}
                    className={`relative ${plan.is_popular ? "lg:scale-105 z-10" : ""}`}
                  >
                    {plan.is_popular && (
                      <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-20">
                        <Badge className={`${colors.badge} border-0 shadow-lg px-4 py-1`}>
                          Most Popular
                        </Badge>
                      </div>
                    )}

                    <Card className={`h-full transition-all duration-300 hover:shadow-xl border-2 ${colors.border} ${colors.shadow} ${plan.is_popular ? "shadow-xl border-orange-400" : ""
                      }`}>
                      <CardContent className="p-6">
                        <div className="text-center mb-6">
                          <div className={`inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4 ${colors.iconBg} shadow-lg`}>
                            <IconComponent className="w-7 h-7 text-white" />
                          </div>
                          <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                          <p className="text-sm text-gray-500 mt-1 min-h-[40px]">{plan.description}</p>
                          <div className="mt-4">
                            {isFree ? (
                              <span className="text-4xl font-bold text-gray-900">Free</span>
                            ) : (
                              <>
                                <span className="text-4xl font-bold text-gray-900">
                                  ${price.toFixed(2)}
                                </span>
                                <span className="text-gray-500">/{isYearly ? "year" : "month"}</span>
                              </>
                            )}
                          </div>
                        </div>

                        <ul className="space-y-3 mb-6">
                          {plan.display_features.filter(f => f.included).map((feature) => (
                            <li key={feature.name} className="flex items-center gap-2 text-sm text-gray-600">
                              <div className={`w-5 h-5 rounded-full ${colors.checkBg} flex items-center justify-center flex-shrink-0`}>
                                <Check className={`w-3 h-3 ${colors.checkIcon}`} />
                              </div>
                              {feature.name}
                            </li>
                          ))}
                        </ul>

                        <Link href="/register" className="block">
                          <Button className={`w-full h-12 text-base font-medium transition-all text-white shadow-lg ${colors.button}`}>
                            {isFree ? "Get Started" : "Subscribe Now"}
                          </Button>
                        </Link>
                      </CardContent>
                    </Card>
                  </motion.div>
                )
              })}
            </div>
          )}

          {/* Money back guarantee */}
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mt-12 text-sm text-gray-500"
          >
            <Shield className="w-4 h-4 inline-block mr-1 text-green-500" />
            30-day money-back guarantee • Cancel anytime • No hidden fees
          </motion.p>
        </div>
      </section >

      {/* ============================================ */}
      {/* FINAL CTA SECTION */}
      {/* ============================================ */}
      <section className="py-24 relative overflow-hidden">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 via-orange-500/5 to-white" />
        <GradientBlob className="w-[600px] h-[600px] bg-gradient-to-r from-red-200 to-orange-200 -bottom-40 -left-40" />
        <GradientBlob className="w-[400px] h-[400px] bg-gradient-to-r from-indigo-200 to-purple-200 top-0 right-0" />

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center max-w-3xl mx-auto"
          >
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 leading-tight">
              Ready to Automate Your{" "}
              <span className="bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
                YouTube Channels?
              </span>
            </h2>
            <p className="mt-6 text-lg text-gray-600">
              Join thousands of creators who are growing their channels on autopilot.
              Get started for free today.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/register">
                <Button size="lg" className="w-full sm:w-auto bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white shadow-xl shadow-red-500/25 hover:shadow-red-500/40 transition-all text-lg px-10 py-6">
                  Get Started Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="w-full sm:w-auto border-gray-300 hover:bg-gray-50 text-lg px-10 py-6">
                  Sign In
                </Button>
              </Link>
            </div>
            <p className="mt-6 text-sm text-gray-500">
              No credit card required • Free plan forever • Upgrade anytime
            </p>
          </motion.div>
        </div>
      </section>

      {/* ============================================ */}
      {/* FOOTER */}
      {/* ============================================ */}
      <footer className="bg-gray-900 text-white py-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12">
            {/* Brand */}
            <div className="md:col-span-1">
              <Link href="/" className="flex items-center gap-2 mb-4">
                <div className="bg-gradient-to-r from-red-500 to-orange-500 p-2 rounded-lg">
                  <Video className="h-5 w-5 text-white" />
                </div>
                <span className="text-xl font-bold">YT Automation</span>
              </Link>
              <p className="text-gray-400 text-sm">
                The all-in-one platform for YouTube creators who want to scale their channels efficiently.
              </p>
            </div>

            {/* Product Links */}
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a></li>
                <li><Link href="/login" className="hover:text-white transition-colors">Dashboard</Link></li>
              </ul>
            </div>

            {/* Company Links */}
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">About Us</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>

            {/* Legal Links */}
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><LegalLink type="privacy" className="hover:text-white transition-colors">Privacy Policy</LegalLink></li>
                <li><LegalLink type="terms" className="hover:text-white transition-colors">Terms of Service</LegalLink></li>
                <li><a href="#" className="hover:text-white transition-colors">Cookie Policy</a></li>
              </ul>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-gray-400">
              © {new Date().getFullYear()} YT Automation. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z" /></svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" /></svg>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div >
  )
}
