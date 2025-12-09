import type { PasswordStrength } from "@/types/auth"

/**
 * Calculate password strength based on various criteria
 * Score: 0-4 (0 = very weak, 4 = very strong)
 */
export function calculatePasswordStrength(password: string): PasswordStrength {
    const feedback: string[] = []
    let score = 0

    if (!password) {
        return { score: 0, feedback: ["Enter a password"], isValid: false }
    }

    // Length checks
    if (password.length >= 8) {
        score += 1
    } else {
        feedback.push("Use at least 8 characters")
    }

    if (password.length >= 12) {
        score += 1
    }

    // Character type checks
    if (/[a-z]/.test(password)) {
        score += 0.5
    } else {
        feedback.push("Add lowercase letters")
    }

    if (/[A-Z]/.test(password)) {
        score += 0.5
    } else {
        feedback.push("Add uppercase letters")
    }

    if (/[0-9]/.test(password)) {
        score += 0.5
    } else {
        feedback.push("Add numbers")
    }

    if (/[^a-zA-Z0-9]/.test(password)) {
        score += 0.5
    } else {
        feedback.push("Add special characters")
    }

    // Common patterns to avoid
    const commonPatterns = [
        /^123/,
        /password/i,
        /qwerty/i,
        /abc123/i,
        /(.)\1{2,}/, // Repeated characters
    ]

    for (const pattern of commonPatterns) {
        if (pattern.test(password)) {
            score = Math.max(0, score - 1)
            feedback.push("Avoid common patterns")
            break
        }
    }

    // Normalize score to 0-4
    score = Math.min(4, Math.max(0, Math.round(score)))

    // Password is valid if score >= 2 and length >= 8
    const isValid = score >= 2 && password.length >= 8 && /[a-z]/.test(password) && /[A-Z]/.test(password) && /[0-9]/.test(password)

    return { score, feedback, isValid }
}

/**
 * Get color class based on password strength score
 */
export function getStrengthColor(score: number): string {
    switch (score) {
        case 0:
            return "bg-destructive"
        case 1:
            return "bg-orange-500"
        case 2:
            return "bg-yellow-500"
        case 3:
            return "bg-lime-500"
        case 4:
            return "bg-green-500"
        default:
            return "bg-muted"
    }
}

/**
 * Get label based on password strength score
 */
export function getStrengthLabel(score: number): string {
    switch (score) {
        case 0:
            return "Very weak"
        case 1:
            return "Weak"
        case 2:
            return "Fair"
        case 3:
            return "Strong"
        case 4:
            return "Very strong"
        default:
            return ""
    }
}
