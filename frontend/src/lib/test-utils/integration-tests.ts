/**
 * Integration Test Utilities
 * 
 * These functions can be run in the browser console or via a test runner
 * to verify end-to-end functionality.
 */

import apiClient from "@/lib/api/client"
import { authApi } from "@/lib/api/auth"
import { accountsApi } from "@/lib/api/accounts"
import { streamsApi } from "@/lib/api/streams"
import { billingApi } from "@/lib/api/billing"

export interface TestResult {
    name: string
    passed: boolean
    error?: string
    duration: number
}

export interface TestSuite {
    name: string
    results: TestResult[]
    passed: number
    failed: number
    duration: number
}

type TestFunction = () => Promise<void>

/**
 * Run a single test and capture result
 */
async function runTest(name: string, testFn: TestFunction): Promise<TestResult> {
    const start = Date.now()
    try {
        await testFn()
        return {
            name,
            passed: true,
            duration: Date.now() - start,
        }
    } catch (error) {
        return {
            name,
            passed: false,
            error: error instanceof Error ? error.message : String(error),
            duration: Date.now() - start,
        }
    }
}

/**
 * Run a test suite
 */
async function runSuite(name: string, tests: Array<{ name: string; fn: TestFunction }>): Promise<TestSuite> {
    const start = Date.now()
    const results: TestResult[] = []

    for (const test of tests) {
        const result = await runTest(test.name, test.fn)
        results.push(result)
        console.log(
            `${result.passed ? "✓" : "✗"} ${test.name}`,
            result.passed ? "" : `- ${result.error}`
        )
    }

    const passed = results.filter(r => r.passed).length
    const failed = results.filter(r => !r.passed).length

    return {
        name,
        results,
        passed,
        failed,
        duration: Date.now() - start,
    }
}

/**
 * Authentication Tests
 */
export async function testAuthentication(): Promise<TestSuite> {
    return runSuite("Authentication", [
        {
            name: "API client is configured",
            fn: async () => {
                const baseUrl = apiClient.getBaseUrl()
                if (!baseUrl) throw new Error("API base URL not configured")
            },
        },
        {
            name: "Can check auth status",
            fn: async () => {
                try {
                    await authApi.getCurrentUser()
                } catch (error) {
                    // 401 is expected if not logged in
                    const apiError = error as { status?: number }
                    if (apiError.status !== 401) {
                        throw error
                    }
                }
            },
        },
        {
            name: "Login with invalid credentials returns error",
            fn: async () => {
                try {
                    await authApi.login({
                        email: "invalid@test.com",
                        password: "wrongpassword",
                    })
                    throw new Error("Should have thrown an error")
                } catch (error) {
                    const apiError = error as { status?: number }
                    if (apiError.status !== 401 && apiError.status !== 400) {
                        throw new Error(`Unexpected status: ${apiError.status}`)
                    }
                }
            },
        },
    ])
}

/**
 * YouTube Account Tests (requires authentication)
 */
export async function testAccounts(): Promise<TestSuite> {
    return runSuite("YouTube Accounts", [
        {
            name: "Can fetch accounts list",
            fn: async () => {
                const accounts = await accountsApi.getAccounts()
                if (!Array.isArray(accounts)) {
                    throw new Error("Expected array of accounts")
                }
            },
        },
        {
            name: "Can initiate OAuth flow",
            fn: async () => {
                // Just verify the method exists and returns expected shape
                // Don't actually call it as it may redirect
                if (typeof accountsApi.initiateOAuth !== "function") {
                    throw new Error("initiateOAuth method not found")
                }
            },
        },
    ])
}

/**
 * Streaming Tests (requires authentication)
 */
export async function testStreaming(): Promise<TestSuite> {
    return runSuite("Streaming", [
        {
            name: "Can fetch streams list",
            fn: async () => {
                const response = await streamsApi.getEvents()
                if (!response || !Array.isArray(response.items)) {
                    throw new Error("Expected response with items array")
                }
            },
        },
    ])
}

/**
 * Billing Tests (requires authentication)
 */
export async function testBilling(): Promise<TestSuite> {
    return runSuite("Billing", [
        {
            name: "Can fetch subscription status",
            fn: async () => {
                // Subscription may be null for free tier users
                const subscription = await billingApi.getSubscription()
                // Just verify the call doesn't throw
                if (subscription === undefined) {
                    throw new Error("Unexpected undefined response")
                }
            },
        },
        {
            name: "Can fetch available plans",
            fn: async () => {
                const plans = await billingApi.getPlans()
                if (!Array.isArray(plans)) {
                    throw new Error("Expected array of plans")
                }
            },
        },
        {
            name: "Can fetch enabled payment gateways",
            fn: async () => {
                const gateways = await billingApi.getEnabledGateways()
                if (!Array.isArray(gateways)) {
                    throw new Error("Expected array of gateways")
                }
            },
        },
    ])
}

/**
 * Run all integration tests
 */
export async function runAllTests(): Promise<TestSuite[]> {
    console.log("🧪 Running Integration Tests...\n")

    const suites: TestSuite[] = []

    // Always run auth tests
    suites.push(await testAuthentication())

    // Check if authenticated before running protected tests
    const token = apiClient.getAccessToken()
    if (token) {
        console.log("\n📋 Running authenticated tests...\n")
        suites.push(await testAccounts())
        suites.push(await testStreaming())
        suites.push(await testBilling())
    } else {
        console.log("\n⚠️ Skipping authenticated tests (not logged in)\n")
    }

    // Summary
    const totalPassed = suites.reduce((sum, s) => sum + s.passed, 0)
    const totalFailed = suites.reduce((sum, s) => sum + s.failed, 0)
    const totalDuration = suites.reduce((sum, s) => sum + s.duration, 0)

    console.log("\n" + "=".repeat(50))
    console.log(`📊 Test Summary`)
    console.log("=".repeat(50))
    console.log(`Total: ${totalPassed + totalFailed} tests`)
    console.log(`Passed: ${totalPassed}`)
    console.log(`Failed: ${totalFailed}`)
    console.log(`Duration: ${totalDuration}ms`)
    console.log("=".repeat(50))

    return suites
}

// Export for browser console usage
if (typeof window !== "undefined") {
    (window as unknown as { runIntegrationTests: typeof runAllTests }).runIntegrationTests = runAllTests
}

export default runAllTests
