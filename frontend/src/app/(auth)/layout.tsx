import { Metadata } from "next"

export const metadata: Metadata = {
    title: "Authentication - YouTube Automation Platform",
    description: "Sign in or create an account",
}

export default function AuthLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return <>{children}</>
}
