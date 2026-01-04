import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { AuthProvider } from "@/components/providers/auth-provider";
import { ApiErrorProvider } from "@/components/providers/api-error-provider";
import { ToastProvider } from "@/components/ui/toast";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" },
  ],
};

export const metadata: Metadata = {
  title: {
    default: "YT Automation - YouTube Channel Management Platform",
    template: "%s | YT Automation",
  },
  description: "Manage multiple YouTube channels effortlessly. Automate 24/7 live streaming, moderate comments with AI, track analytics, and grow your audience with YT Automation.",
  keywords: [
    "YouTube automation",
    "YouTube management",
    "multi-channel management",
    "live streaming automation",
    "24/7 live stream",
    "YouTube analytics",
    "comment moderation",
    "AI moderation",
    "YouTube growth",
    "content creator tools",
    "video to live stream",
    "YouTube scheduler",
  ],
  authors: [{ name: "YT Automation" }],
  creator: "YT Automation",
  publisher: "YT Automation",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
  manifest: "/manifest.json",
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "YT Automation",
    title: "YT Automation - YouTube Channel Management Platform",
    description: "Manage multiple YouTube channels effortlessly. Automate 24/7 live streaming, moderate comments with AI, and track analytics.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "YT Automation - YouTube Channel Management Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "YT Automation - YouTube Channel Management Platform",
    description: "Manage multiple YouTube channels effortlessly. Automate 24/7 live streaming, moderate comments with AI, and track analytics.",
    images: ["/og-image.png"],
    creator: "@ytautomation",
  },
  applicationName: "YT Automation",
  category: "Technology",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <ToastProvider>
              <ApiErrorProvider>
                {children}
              </ApiErrorProvider>
            </ToastProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
