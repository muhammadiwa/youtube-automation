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
        const imgRef = React.useRef<HTMLImageElement>(null)

        React.useEffect(() => {
            setHasError(false)
        }, [src])

        const handleError = (e: React.SyntheticEvent<HTMLImageElement>) => {
            setHasError(true)
            onLoadingStatusChange?.("error")
            onError?.(e)
        }

        const handleLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
            onLoadingStatusChange?.("loaded")
            onLoad?.(e)
        }

        // Don't render if no src or has error
        if (!src || hasError) {
            return null
        }

        return (
            // eslint-disable-next-line @next/next/no-img-element
            <img
                ref={ref || imgRef}
                alt={alt}
                src={src}
                className={cn(
                    "aspect-square h-full w-full object-cover",
                    className
                )}
                onLoad={handleLoad}
                onError={handleError}
                referrerPolicy="no-referrer"
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
