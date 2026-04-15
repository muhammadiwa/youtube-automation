"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FileText, Shield, X, Calendar, Clock, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { RichTextViewer } from "@/components/ui/rich-text-editor"
import apiClient from "@/lib/api/client"

interface TermsOfService {
    id: string
    version: string
    title: string
    content: string
    content_html: string | null
    summary: string | null
    effective_date: string | null
    activated_at: string | null
}

type LegalModalType = "terms" | "privacy" | null

interface LegalModalProps {
    type: LegalModalType
    onClose: () => void
}

// Privacy Policy content (static)
const privacyContent = {
    title: "Privacy Policy",
    lastUpdated: "December 15, 2024",
    sections: [
        {
            title: "1. Introduction",
            content: `Welcome to YouTube Auto ("we," "our," or "us"). We are committed to protecting your personal information and your right to privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our platform.`
        },
        {
            title: "2. Information We Collect",
            content: `We collect personal information that you voluntarily provide when you register, connect your YouTube channel, subscribe to our services, or contact support. We also automatically collect device information, IP address, usage patterns, and cookies.`
        },
        {
            title: "3. How We Use Your Information",
            content: `We use your information to provide and maintain our services, process transactions, send updates and marketing communications, improve our platform, and comply with legal obligations.`
        },
        {
            title: "4. Data Sharing",
            content: `We may share your information with service providers, YouTube/Google for channel integration, payment processors, and law enforcement when required by law.`
        },
        {
            title: "5. Data Security",
            content: `We implement appropriate technical and organizational security measures to protect your personal information. However, no method of transmission over the Internet is 100% secure.`
        },
        {
            title: "6. Your Rights (GDPR)",
            content: `If you are in the EEA, you have the right to access, rectify, delete, object to processing, data portability, and withdraw consent at any time.`
        },
        {
            title: "7. Contact Us",
            content: `For questions about this Privacy Policy, contact us at privacy@youtubeauto.com`
        }
    ]
}

export function LegalModal({ type, onClose }: LegalModalProps) {
    const [terms, setTerms] = useState<TermsOfService | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (type === "terms") {
            setIsLoading(true)
            setError(null)
            apiClient.get<TermsOfService>("/terms-of-service")
                .then(setTerms)
                .catch(() => setError("Terms of Service not available"))
                .finally(() => setIsLoading(false))
        }
    }, [type])

    if (!type) return null

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center">
                {/* Backdrop */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                    className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                />

                {/* Modal */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    transition={{ type: "spring", duration: 0.5 }}
                    className="relative w-full max-w-2xl max-h-[85vh] mx-4 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden"
                >
                    {/* Header */}
                    <div className="sticky top-0 z-10 bg-gradient-to-r from-red-500 to-red-600 px-6 py-5">
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-white/20 rounded-xl">
                                    {type === "terms" ? (
                                        <FileText className="h-6 w-6 text-white" />
                                    ) : (
                                        <Shield className="h-6 w-6 text-white" />
                                    )}
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">
                                        {type === "terms" ? (terms?.title || "Terms of Service") : privacyContent.title}
                                    </h2>
                                    <div className="flex items-center gap-3 mt-1">
                                        {type === "terms" && terms && (
                                            <>
                                                <Badge variant="secondary" className="bg-white/20 text-white border-0 text-xs">
                                                    v{terms.version}
                                                </Badge>
                                                {terms.effective_date && (
                                                    <span className="flex items-center gap-1 text-white/80 text-xs">
                                                        <Calendar className="h-3 w-3" />
                                                        {new Date(terms.effective_date).toLocaleDateString()}
                                                    </span>
                                                )}
                                            </>
                                        )}
                                        {type === "privacy" && (
                                            <span className="flex items-center gap-1 text-white/80 text-xs">
                                                <Clock className="h-3 w-3" />
                                                Updated: {privacyContent.lastUpdated}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                            >
                                <X className="h-5 w-5 text-white" />
                            </button>
                        </div>
                    </div>

                    {/* Content */}
                    <ScrollArea className="h-[calc(85vh-140px)]">
                        <div className="p-6">
                            {type === "terms" ? (
                                isLoading ? (
                                    <div className="flex flex-col items-center justify-center py-12">
                                        <Loader2 className="h-8 w-8 animate-spin text-red-500 mb-3" />
                                        <p className="text-gray-500">Loading Terms of Service...</p>
                                    </div>
                                ) : error ? (
                                    <div className="text-center py-12">
                                        <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                                        <p className="text-gray-500">{error}</p>
                                    </div>
                                ) : terms ? (
                                    <div className="space-y-4">
                                        {terms.summary && (
                                            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800">
                                                <p className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-1">Summary</p>
                                                <p className="text-sm text-blue-600 dark:text-blue-400">{terms.summary}</p>
                                            </div>
                                        )}
                                        <RichTextViewer content={terms.content_html || terms.content} />
                                    </div>
                                ) : null
                            ) : (
                                <div className="space-y-6">
                                    {privacyContent.sections.map((section, index) => (
                                        <div key={index}>
                                            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                                                {section.title}
                                            </h3>
                                            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                                                {section.content}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </ScrollArea>

                    {/* Footer */}
                    <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
                        <div className="flex items-center justify-between">
                            <p className="text-xs text-gray-500">
                                By using our service, you agree to these terms.
                            </p>
                            <Button onClick={onClose} className="bg-red-500 hover:bg-red-600">
                                I Understand
                            </Button>
                        </div>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}

// Hook for easy usage
export function useLegalModal() {
    const [modalType, setModalType] = useState<LegalModalType>(null)

    const openTerms = () => setModalType("terms")
    const openPrivacy = () => setModalType("privacy")
    const close = () => setModalType(null)

    return {
        modalType,
        openTerms,
        openPrivacy,
        close,
        LegalModalComponent: () => <LegalModal type={modalType} onClose={close} />
    }
}

// Standalone link components for easy integration
interface LegalLinkProps {
    type: "terms" | "privacy"
    className?: string
    children?: React.ReactNode
    asPage?: boolean // If true, link to separate page instead of modal
}

export function LegalLink({ type, className, children, asPage = false }: LegalLinkProps) {
    const [isOpen, setIsOpen] = useState(false)

    // If asPage is true, render as a regular link to the page
    if (asPage) {
        const href = type === "terms" ? "/terms" : "/privacy"
        return (
            <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className={className || "text-red-600 dark:text-red-400 hover:underline"}
            >
                {children || (type === "terms" ? "Terms of Service" : "Privacy Policy")}
            </a>
        )
    }

    return (
        <>
            <button
                onClick={() => setIsOpen(true)}
                className={className || "text-red-600 dark:text-red-400 hover:underline"}
            >
                {children || (type === "terms" ? "Terms of Service" : "Privacy Policy")}
            </button>
            {isOpen && <LegalModal type={type} onClose={() => setIsOpen(false)} />}
        </>
    )
}
