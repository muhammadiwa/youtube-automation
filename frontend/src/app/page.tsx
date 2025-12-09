"use client"

import { motion } from "framer-motion"
import { Youtube, Zap, Shield, BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ThemeToggle } from "@/components/theme-toggle"

const features = [
  {
    icon: Youtube,
    title: "Multi-Account Management",
    description: "Manage multiple YouTube accounts from a single dashboard with ease.",
  },
  {
    icon: Zap,
    title: "Live Streaming Automation",
    description: "Schedule and automate your live streams with 24/7 playlist support.",
  },
  {
    icon: Shield,
    title: "AI-Powered Moderation",
    description: "Keep your chat clean with intelligent moderation and chatbot features.",
  },
  {
    icon: BarChart3,
    title: "Advanced Analytics",
    description: "Track performance across all channels with comprehensive analytics.",
  },
]

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Youtube className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">YouTube Automation</span>
          </div>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Button variant="ghost">Sign In</Button>
            <Button>Get Started</Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container py-24 md:py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
            Automate Your{" "}
            <span className="text-primary">YouTube</span>{" "}
            Success
          </h1>
          <p className="mt-6 text-lg text-muted-foreground">
            The all-in-one platform for managing multiple YouTube accounts,
            automating live streams, and leveraging AI for content optimization.
          </p>
          <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Button size="lg">Start Free Trial</Button>
            <Button size="lg" variant="outline">
              Watch Demo
            </Button>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="container py-16">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h2 className="mb-12 text-center text-3xl font-bold">
            Everything You Need
          </h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 * index }}
              >
                <Card className="h-full transition-shadow hover:shadow-lg">
                  <CardHeader>
                    <feature.icon className="h-10 w-10 text-primary" />
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container text-center text-sm text-muted-foreground">
          <p>© 2024 YouTube Automation Platform. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
