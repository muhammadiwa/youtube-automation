"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import { Crop, RotateCw, ZoomIn, ZoomOut, Check, X, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"

interface ThumbnailEditorProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    imageUrl: string
    onSave: (croppedImage: Blob) => void
    aspectRatio?: number // Default 16:9
}

interface CropArea {
    x: number
    y: number
    width: number
    height: number
}

export function ThumbnailEditor({
    open,
    onOpenChange,
    imageUrl,
    onSave,
    aspectRatio = 16 / 9,
}: ThumbnailEditorProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const imageRef = useRef<HTMLImageElement | null>(null)
    const containerRef = useRef<HTMLDivElement>(null)

    const [isLoading, setIsLoading] = useState(true)
    const [isSaving, setIsSaving] = useState(false)
    const [zoom, setZoom] = useState(1)
    const [rotation, setRotation] = useState(0)
    const [position, setPosition] = useState({ x: 0, y: 0 })
    const [isDragging, setIsDragging] = useState(false)
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

    // Load image
    useEffect(() => {
        if (!open || !imageUrl) return

        setIsLoading(true)
        const img = new Image()
        img.crossOrigin = "anonymous"
        img.onload = () => {
            imageRef.current = img
            setIsLoading(false)
            // Reset state
            setZoom(1)
            setRotation(0)
            setPosition({ x: 0, y: 0 })
            drawCanvas()
        }
        img.onerror = () => {
            setIsLoading(false)
        }
        img.src = imageUrl
    }, [open, imageUrl])

    // Redraw canvas when state changes
    useEffect(() => {
        if (!isLoading) {
            drawCanvas()
        }
    }, [zoom, rotation, position, isLoading])

    const drawCanvas = useCallback(() => {
        const canvas = canvasRef.current
        const img = imageRef.current
        if (!canvas || !img) return

        const ctx = canvas.getContext("2d")
        if (!ctx) return

        // Set canvas size (16:9 aspect ratio)
        const canvasWidth = 640
        const canvasHeight = canvasWidth / aspectRatio
        canvas.width = canvasWidth
        canvas.height = canvasHeight

        // Clear canvas
        ctx.fillStyle = "#000"
        ctx.fillRect(0, 0, canvasWidth, canvasHeight)

        // Save context state
        ctx.save()

        // Move to center
        ctx.translate(canvasWidth / 2, canvasHeight / 2)

        // Apply rotation
        ctx.rotate((rotation * Math.PI) / 180)

        // Apply zoom
        ctx.scale(zoom, zoom)

        // Calculate image dimensions to cover canvas
        const imgAspect = img.width / img.height
        const canvasAspect = canvasWidth / canvasHeight

        let drawWidth, drawHeight
        if (imgAspect > canvasAspect) {
            drawHeight = canvasHeight / zoom
            drawWidth = drawHeight * imgAspect
        } else {
            drawWidth = canvasWidth / zoom
            drawHeight = drawWidth / imgAspect
        }

        // Draw image centered with position offset
        ctx.drawImage(
            img,
            -drawWidth / 2 + position.x,
            -drawHeight / 2 + position.y,
            drawWidth,
            drawHeight
        )

        // Restore context state
        ctx.restore()
    }, [zoom, rotation, position, aspectRatio])

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true)
        setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
    }

    const handleMouseMove = (e: React.MouseEvent) => {
        if (!isDragging) return
        setPosition({
            x: e.clientX - dragStart.x,
            y: e.clientY - dragStart.y,
        })
    }

    const handleMouseUp = () => {
        setIsDragging(false)
    }

    const handleZoomChange = (value: number[]) => {
        setZoom(value[0])
    }

    const handleRotate = () => {
        setRotation((prev) => (prev + 90) % 360)
    }

    const handleSave = async () => {
        const canvas = canvasRef.current
        if (!canvas) return

        setIsSaving(true)
        try {
            canvas.toBlob(
                (blob) => {
                    if (blob) {
                        onSave(blob)
                        onOpenChange(false)
                    }
                    setIsSaving(false)
                },
                "image/jpeg",
                0.9
            )
        } catch (error) {
            setIsSaving(false)
        }
    }

    const handleReset = () => {
        setZoom(1)
        setRotation(0)
        setPosition({ x: 0, y: 0 })
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Crop className="h-5 w-5" />
                        Edit Thumbnail
                    </DialogTitle>
                    <DialogDescription>
                        Adjust your thumbnail. Drag to reposition, use controls to zoom and rotate.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                    {/* Canvas Preview */}
                    <div
                        ref={containerRef}
                        className="relative bg-black rounded-lg overflow-hidden cursor-move"
                        onMouseDown={handleMouseDown}
                        onMouseMove={handleMouseMove}
                        onMouseUp={handleMouseUp}
                        onMouseLeave={handleMouseUp}
                    >
                        {isLoading ? (
                            <div className="aspect-video flex items-center justify-center">
                                <Loader2 className="h-8 w-8 animate-spin text-white" />
                            </div>
                        ) : (
                            <canvas
                                ref={canvasRef}
                                className="w-full aspect-video"
                                style={{ display: "block" }}
                            />
                        )}

                        {/* Crop overlay guide */}
                        <div className="absolute inset-0 pointer-events-none">
                            <div className="absolute inset-4 border-2 border-white/30 rounded" />
                            {/* Rule of thirds grid */}
                            <div className="absolute inset-4 grid grid-cols-3 grid-rows-3">
                                {[...Array(9)].map((_, i) => (
                                    <div key={i} className="border border-white/10" />
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Controls */}
                    <div className="grid gap-4 sm:grid-cols-2">
                        {/* Zoom Control */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label className="flex items-center gap-2">
                                    <ZoomIn className="h-4 w-4" />
                                    Zoom
                                </Label>
                                <span className="text-sm text-muted-foreground">
                                    {Math.round(zoom * 100)}%
                                </span>
                            </div>
                            <div className="flex items-center gap-2">
                                <ZoomOut className="h-4 w-4 text-muted-foreground" />
                                <Slider
                                    value={[zoom]}
                                    onValueChange={handleZoomChange}
                                    min={0.5}
                                    max={3}
                                    step={0.1}
                                    className="flex-1"
                                />
                                <ZoomIn className="h-4 w-4 text-muted-foreground" />
                            </div>
                        </div>

                        {/* Rotation Control */}
                        <div className="space-y-2">
                            <Label className="flex items-center gap-2">
                                <RotateCw className="h-4 w-4" />
                                Rotation
                            </Label>
                            <div className="flex items-center gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleRotate}
                                    className="flex-1"
                                >
                                    <RotateCw className="h-4 w-4 mr-2" />
                                    Rotate 90°
                                </Button>
                                <span className="text-sm text-muted-foreground w-16 text-center">
                                    {rotation}°
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <DialogFooter className="flex-col sm:flex-row gap-2">
                    <Button variant="outline" onClick={handleReset}>
                        Reset
                    </Button>
                    <div className="flex gap-2 ml-auto">
                        <Button variant="outline" onClick={() => onOpenChange(false)}>
                            <X className="h-4 w-4 mr-2" />
                            Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={isSaving || isLoading}>
                            {isSaving ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                                <Check className="h-4 w-4 mr-2" />
                            )}
                            Save Thumbnail
                        </Button>
                    </div>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default ThumbnailEditor
