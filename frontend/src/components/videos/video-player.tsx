/**
 * Video Player Component
 * 
 * HTML5 video player with custom controls, keyboard shortcuts, and fullscreen support.
 * Requirements: 1.3 (Video Preview & Details)
 * Design: VideoPlayer component
 */

"use client"

import { useState, useRef, useEffect } from "react"
import {
    Play,
    Pause,
    Volume2,
    VolumeX,
    Maximize,
    Minimize,
    Loader2,
    AlertCircle,
    SkipBack,
    SkipForward,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

interface VideoPlayerProps {
    videoUrl: string
    poster?: string
    className?: string
    onError?: (error: Error) => void
}

export function VideoPlayer({
    videoUrl,
    poster,
    className = "",
    onError,
}: VideoPlayerProps) {
    const videoRef = useRef<HTMLVideoElement>(null)
    const containerRef = useRef<HTMLDivElement>(null)
    const [isPlaying, setIsPlaying] = useState(false)
    const [currentTime, setCurrentTime] = useState(0)
    const [duration, setDuration] = useState(0)
    const [volume, setVolume] = useState(1)
    const [isMuted, setIsMuted] = useState(false)
    const [isFullscreen, setIsFullscreen] = useState(false)
    const [playbackRate, setPlaybackRate] = useState(1)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [showControls, setShowControls] = useState(true)
    const [buffered, setBuffered] = useState(0)

    // Hide controls after 3 seconds of inactivity
    useEffect(() => {
        let timeout: NodeJS.Timeout
        if (isPlaying && showControls) {
            timeout = setTimeout(() => setShowControls(false), 3000)
        }
        return () => clearTimeout(timeout)
    }, [isPlaying, showControls])

    // Update current time
    useEffect(() => {
        const video = videoRef.current
        if (!video) return

        const updateTime = () => setCurrentTime(video.currentTime)
        const updateDuration = () => setDuration(video.duration)
        const updateBuffered = () => {
            if (video.buffered.length > 0) {
                setBuffered(video.buffered.end(video.buffered.length - 1))
            }
        }

        video.addEventListener("timeupdate", updateTime)
        video.addEventListener("durationchange", updateDuration)
        video.addEventListener("loadedmetadata", updateDuration)
        video.addEventListener("progress", updateBuffered)
        video.addEventListener("canplay", () => setLoading(false))
        video.addEventListener("waiting", () => setLoading(true))
        video.addEventListener("error", handleVideoError)

        return () => {
            video.removeEventListener("timeupdate", updateTime)
            video.removeEventListener("durationchange", updateDuration)
            video.removeEventListener("loadedmetadata", updateDuration)
            video.removeEventListener("progress", updateBuffered)
            video.removeEventListener("canplay", () => setLoading(false))
            video.removeEventListener("waiting", () => setLoading(true))
            video.removeEventListener("error", handleVideoError)
        }
    }, [])

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (!videoRef.current) return

            switch (e.key.toLowerCase()) {
                case " ":
                case "k":
                    e.preventDefault()
                    togglePlay()
                    break
                case "arrowleft":
                    e.preventDefault()
                    seek(currentTime - 5)
                    break
                case "arrowright":
                    e.preventDefault()
                    seek(currentTime + 5)
                    break
                case "arrowup":
                    e.preventDefault()
                    setVolume(Math.min(1, volume + 0.1))
                    break
                case "arrowdown":
                    e.preventDefault()
                    setVolume(Math.max(0, volume - 0.1))
                    break
                case "f":
                    e.preventDefault()
                    toggleFullscreen()
                    break
                case "m":
                    e.preventDefault()
                    toggleMute()
                    break
                case "+":
                case "=":
                    e.preventDefault()
                    changePlaybackRate(Math.min(2, playbackRate + 0.25))
                    break
                case "-":
                case "_":
                    e.preventDefault()
                    changePlaybackRate(Math.max(0.5, playbackRate - 0.25))
                    break
            }
        }

        window.addEventListener("keydown", handleKeyDown)
        return () => window.removeEventListener("keydown", handleKeyDown)
    }, [currentTime, volume, playbackRate])

    // Fullscreen change listener
    useEffect(() => {
        const handleFullscreenChange = () => {
            setIsFullscreen(!!document.fullscreenElement)
        }

        document.addEventListener("fullscreenchange", handleFullscreenChange)
        return () => document.removeEventListener("fullscreenchange", handleFullscreenChange)
    }, [])

    const handleVideoError = () => {
        const video = videoRef.current
        if (!video) return

        let errorMessage = "Failed to load video"
        if (video.error) {
            switch (video.error.code) {
                case MediaError.MEDIA_ERR_ABORTED:
                    errorMessage = "Video loading was aborted"
                    break
                case MediaError.MEDIA_ERR_NETWORK:
                    errorMessage = "Network error while loading video"
                    break
                case MediaError.MEDIA_ERR_DECODE:
                    errorMessage = "Video decoding failed"
                    break
                case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
                    errorMessage = "Video format not supported"
                    break
            }
        }

        setError(errorMessage)
        setLoading(false)
        onError?.(new Error(errorMessage))
    }

    const togglePlay = () => {
        const video = videoRef.current
        if (!video) return

        if (isPlaying) {
            video.pause()
        } else {
            video.play()
        }
        setIsPlaying(!isPlaying)
    }

    const seek = (time: number) => {
        const video = videoRef.current
        if (!video) return

        video.currentTime = Math.max(0, Math.min(duration, time))
    }

    const handleSeek = (value: number[]) => {
        seek(value[0])
    }

    const handleVolumeChange = (value: number[]) => {
        const newVolume = value[0]
        setVolume(newVolume)
        if (videoRef.current) {
            videoRef.current.volume = newVolume
        }
        if (newVolume > 0 && isMuted) {
            setIsMuted(false)
        }
    }

    const toggleMute = () => {
        const video = videoRef.current
        if (!video) return

        video.muted = !isMuted
        setIsMuted(!isMuted)
    }

    const toggleFullscreen = async () => {
        const container = containerRef.current
        if (!container) return

        try {
            if (!isFullscreen) {
                await container.requestFullscreen()
            } else {
                await document.exitFullscreen()
            }
        } catch (error) {
            console.error("Fullscreen error:", error)
        }
    }

    const changePlaybackRate = (rate: number) => {
        const video = videoRef.current
        if (!video) return

        video.playbackRate = rate
        setPlaybackRate(rate)
    }

    const formatTime = (seconds: number) => {
        if (isNaN(seconds)) return "0:00"

        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        const secs = Math.floor(seconds % 60)

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
        }
        return `${minutes}:${secs.toString().padStart(2, "0")}`
    }

    const handleRetry = () => {
        setError(null)
        setLoading(true)
        videoRef.current?.load()
    }

    if (error) {
        return (
            <div className={`relative bg-black rounded-lg overflow-hidden ${className}`}>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-white p-8">
                    <AlertCircle className="h-16 w-16 mb-4 text-destructive" />
                    <h3 className="text-lg font-semibold mb-2">Error Loading Video</h3>
                    <p className="text-sm text-muted-foreground mb-4 text-center">{error}</p>
                    <Button onClick={handleRetry} variant="secondary">
                        Retry
                    </Button>
                </div>
            </div>
        )
    }

    return (
        <div
            ref={containerRef}
            className={`relative bg-black rounded-lg overflow-hidden group ${className}`}
            onMouseMove={() => setShowControls(true)}
            onMouseLeave={() => isPlaying && setShowControls(false)}
        >
            {/* Video Element */}
            <video
                ref={videoRef}
                src={videoUrl}
                poster={poster}
                className="w-full h-full"
                onClick={togglePlay}
            />

            {/* Loading Spinner */}
            {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                    <Loader2 className="h-12 w-12 animate-spin text-white" />
                </div>
            )}

            {/* Controls Overlay */}
            <div
                className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 transition-opacity duration-300 ${showControls || !isPlaying ? "opacity-100" : "opacity-0"
                    }`}
            >
                {/* Progress Bar */}
                <div className="mb-4">
                    <Slider
                        value={[currentTime]}
                        max={duration || 100}
                        step={0.1}
                        onValueChange={handleSeek}
                        className="cursor-pointer"
                    />
                    {/* Buffered indicator */}
                    <div
                        className="absolute h-1 bg-white/30 rounded-full"
                        style={{
                            width: `${(buffered / duration) * 100}%`,
                            bottom: "2.5rem",
                            left: "1rem",
                            right: "1rem",
                        }}
                    />
                </div>

                {/* Controls */}
                <div className="flex items-center gap-2 text-white">
                    {/* Play/Pause */}
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={togglePlay}
                        className="text-white hover:bg-white/20"
                    >
                        {isPlaying ? (
                            <Pause className="h-5 w-5" />
                        ) : (
                            <Play className="h-5 w-5" />
                        )}
                    </Button>

                    {/* Skip Back */}
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => seek(currentTime - 5)}
                        className="text-white hover:bg-white/20"
                    >
                        <SkipBack className="h-4 w-4" />
                    </Button>

                    {/* Skip Forward */}
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => seek(currentTime + 5)}
                        className="text-white hover:bg-white/20"
                    >
                        <SkipForward className="h-4 w-4" />
                    </Button>

                    {/* Volume */}
                    <div className="flex items-center gap-2">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={toggleMute}
                            className="text-white hover:bg-white/20"
                        >
                            {isMuted || volume === 0 ? (
                                <VolumeX className="h-5 w-5" />
                            ) : (
                                <Volume2 className="h-5 w-5" />
                            )}
                        </Button>
                        <Slider
                            value={[isMuted ? 0 : volume]}
                            max={1}
                            step={0.01}
                            onValueChange={handleVolumeChange}
                            className="w-20"
                        />
                    </div>

                    {/* Time */}
                    <span className="text-sm">
                        {formatTime(currentTime)} / {formatTime(duration)}
                    </span>

                    <div className="flex-1" />

                    {/* Playback Speed */}
                    <Select
                        value={playbackRate.toString()}
                        onValueChange={(value) => changePlaybackRate(parseFloat(value))}
                    >
                        <SelectTrigger className="w-20 bg-transparent border-white/20 text-white">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="0.5">0.5x</SelectItem>
                            <SelectItem value="0.75">0.75x</SelectItem>
                            <SelectItem value="1">1x</SelectItem>
                            <SelectItem value="1.25">1.25x</SelectItem>
                            <SelectItem value="1.5">1.5x</SelectItem>
                            <SelectItem value="2">2x</SelectItem>
                        </SelectContent>
                    </Select>

                    {/* Fullscreen */}
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={toggleFullscreen}
                        className="text-white hover:bg-white/20"
                    >
                        {isFullscreen ? (
                            <Minimize className="h-5 w-5" />
                        ) : (
                            <Maximize className="h-5 w-5" />
                        )}
                    </Button>
                </div>
            </div>

            {/* Keyboard Shortcuts Help (Optional) */}
            {showControls && !isPlaying && (
                <div className="absolute top-4 right-4 bg-black/80 text-white text-xs p-3 rounded-lg">
                    <div className="font-semibold mb-2">Keyboard Shortcuts</div>
                    <div className="space-y-1">
                        <div>Space/K: Play/Pause</div>
                        <div>←/→: Seek -5s/+5s</div>
                        <div>↑/↓: Volume</div>
                        <div>F: Fullscreen</div>
                        <div>M: Mute</div>
                        <div>+/-: Speed</div>
                    </div>
                </div>
            )}
        </div>
    )
}
