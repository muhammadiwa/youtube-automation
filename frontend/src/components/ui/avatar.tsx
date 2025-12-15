"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

const Avatar = React.forwardRef<
    HTMLSpanElement,
    React.HTMLAttributes<HTMLSpanElement>
>(({ className, ...props }, ref) => (
    <span
        ref={ref}
        className={cn(
            "relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full",
            className
        )}
        {...props}
    />
))
Avatar.displayName = "Avatar"

interface AvatarImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
    onLoadingStatusChange?: (status: "loading" | "loaded" | "error") => void
}

const AvatarImage = React.forwardRef<HTMLImageElement, AvatarImageProps>(
    ({ className, alt = "", src, onLoadingStatusChange, onError, onLoad, ...props }, ref) => {
        const [hasError, setHasError] = React.useState(false)
        const [isLoaded, setIsLoaded] = React.useState(false)

        React.useEffect(() => {
            // Reset state when src changes
            setHasError(false)
            setIsLoaded(false)
        }, [src])

        const handleLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
            setIsLoaded(true)
            setHasError(false)
            onLoadingStatusChange?.("loaded")
            onLoad?.(e)
        }

        const handleError = (e: React.SyntheticEvent<HTMLImageElement>) => {
            setHasError(true)
            setIsLoaded(false)
            onLoadingStatusChange?.("error")
            onError?.(e)
        }

        // Don't render if no src or has error
        if (!src || hasError) {
            return null
        }

        return (
            // eslint-disable-next-line @next/next/no-img-element
            <img
                ref={ref}
                alt={alt}
                src={src}
                className={cn(
                    "aspect-square h-full w-full object-cover",
                    !isLoaded && "opacity-0",
                    isLoaded && "opacity-100 transition-opacity duration-200",
                    className
                )}
                onLoad={handleLoad}
                onError={handleError}
                referrerPolicy="no-referrer"
                loading="lazy"
                {...props}
            />
        )
    }
)
AvatarImage.displayName = "AvatarImage"

const AvatarFallback = React.forwardRef<
    HTMLSpanElement,
    React.HTMLAttributes<HTMLSpanElement>
>(({ className, ...props }, ref) => (
    <span
        ref={ref}
        className={cn(
            "absolute inset-0 flex h-full w-full items-center justify-center rounded-full bg-muted",
            className
        )}
        {...props}
    />
))
AvatarFallback.displayName = "AvatarFallback"

export { Avatar, AvatarImage, AvatarFallback }
