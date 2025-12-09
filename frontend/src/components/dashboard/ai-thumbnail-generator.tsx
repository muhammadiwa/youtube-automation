"use client"

import { useState } from "react"
import { Sparkles, Download, Check, Sliders, Image as ImageIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { aiApi, type ThumbnailResult } from "@/lib/api/ai"
import { cn } from "@/lib/utils"

interface AIThumbnailGeneratorProps {
    videoTitle: string
    videoContent?: string
    onApply: (thumbnailUrl: string) => void
}

export function AIThumbnailGenerator({ videoTitle, videoContent, onApply }: AIThumbnailGeneratorProps) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [thumbnails, setThumbnails] = useState<ThumbnailResult[]>([])
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
    const [showEditor, setShowEditor] = useState(false)

    // Generation options
    const [style, setStyle] = useState<"modern" | "minimalist" | "bold" | "professional" | "gaming">("modern")
    const [includeText, setIncludeText] = useState(true)
    const [text, setText] = useState("")

    // Editor options
    const [brightness, setBrightness] = useState(100)
    const [contrast, setContrast] = useState(100)
    const [saturation, setSaturation] = useState(100)

    const generateThumbnails = async () => {
        if (!videoTitle.trim()) {
            alert("Please enter a video title first")
            return
        }

        try {
            setLoading(true)
            const response = await aiApi.generateThumbnails({
                video_title: videoTitle,
                video_content: videoContent,
                style,
                include_text: includeText,
                text_content: includeText ? text : undefined,
            })
            setThumbnails(response.thumbnails)
            setSelectedIndex(null)
        } catch (error) {
            console.error("Failed to generate thumbnails:", error)
            alert("Failed to generate thumbnails")
        } finally {
            setLoading(false)
        }
    }

    const handleOpen = (isOpen: boolean) => {
        setOpen(isOpen)
        if (isOpen && thumbnails.length === 0) {
            generateThumbnails()
        }
    }

    const downloadThumbnail = (url: string, index: number) => {
        const a = document.createElement("a")
        a.href = url
        a.download = `thumbnail-${index + 1}.jpg`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
    }

    const applyThumbnail = () => {
        if (selectedIndex !== null && thumbnails[selectedIndex]) {
            onApply(thumbnails[selectedIndex].image_url)
            setOpen(false)
        }
    }

    const getFilterStyle = () => {
        return {
            filter: `brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%)`,
        }
    }

    return (
        <Dialog open={open} onOpenChange={handleOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="group hover:border-primary/50 transition-all duration-300">
                    <Sparkles className="mr-2 h-4 w-4 group-hover:text-primary transition-colors" />
                    Generate Thumbnails
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5">
                            <ImageIcon className="h-5 w-5 text-primary" />
                        </div>
                        AI Thumbnail Generator
                    </DialogTitle>
                    <DialogDescription>
                        Generate 3 professional thumbnail variations for your video
                    </DialogDescription>
                </DialogHeader>

                <div className="flex-1 overflow-y-auto space-y-6 mt-4 pr-2">
                    {/* Generation Options */}
                    <div className="border rounded-xl p-4 space-y-4 bg-card shadow-sm">
                        <h3 className="font-semibold flex items-center gap-2">
                            <Sliders className="h-4 w-4 text-primary" />
                            Generation Options
                        </h3>

                        <div>
                            <Label>Style</Label>
                            <RadioGroup value={style} onValueChange={(v: any) => setStyle(v)}>
                                <div className="grid grid-cols-5 gap-2 mt-2">
                                    <div className={cn(
                                        "flex items-center space-x-2 border rounded-lg p-2 cursor-pointer transition-all",
                                        style === "modern" && "border-primary bg-primary/5"
                                    )}>
                                        <RadioGroupItem value="modern" id="modern" />
                                        <Label htmlFor="modern" className="font-normal cursor-pointer text-sm">
                                            Modern
                                        </Label>
                                    </div>
                                    <div className={cn(
                                        "flex items-center space-x-2 border rounded-lg p-2 cursor-pointer transition-all",
                                        style === "minimalist" && "border-primary bg-primary/5"
                                    )}>
                                        <RadioGroupItem value="minimalist" id="minimalist" />
                                        <Label htmlFor="minimalist" className="font-normal cursor-pointer text-sm">
                                            Minimal
                                        </Label>
                                    </div>
                                    <div className={cn(
                                        "flex items-center space-x-2 border rounded-lg p-2 cursor-pointer transition-all",
                                        style === "bold" && "border-primary bg-primary/5"
                                    )}>
                                        <RadioGroupItem value="bold" id="bold" />
                                        <Label htmlFor="bold" className="font-normal cursor-pointer text-sm">
                                            Bold
                                        </Label>
                                    </div>
                                    <div className={cn(
                                        "flex items-center space-x-2 border rounded-lg p-2 cursor-pointer transition-all",
                                        style === "professional" && "border-primary bg-primary/5"
                                    )}>
                                        <RadioGroupItem value="professional" id="professional" />
                                        <Label htmlFor="professional" className="font-normal cursor-pointer text-sm">
                                            Pro
                                        </Label>
                                    </div>
                                    <div className={cn(
                                        "flex items-center space-x-2 border rounded-lg p-2 cursor-pointer transition-all",
                                        style === "gaming" && "border-primary bg-primary/5"
                                    )}>
                                        <RadioGroupItem value="gaming" id="gaming" />
                                        <Label htmlFor="gaming" className="font-normal cursor-pointer text-sm">
                                            Gaming
                                        </Label>
                                    </div>
                                </div>
                            </RadioGroup>
                        </div>

                        <div className="flex items-center justify-between">
                            <Label htmlFor="include-text">Include Text Overlay</Label>
                            <Switch
                                id="include-text"
                                checked={includeText}
                                onCheckedChange={setIncludeText}
                            />
                        </div>

                        {includeText && (
                            <div>
                                <Label htmlFor="text">Text to Display</Label>
                                <Input
                                    id="text"
                                    value={text}
                                    onChange={(e) => setText(e.target.value)}
                                    placeholder="Enter text for thumbnail"
                                    maxLength={50}
                                />
                            </div>
                        )}

                        <Button onClick={generateThumbnails} disabled={loading} className="w-full">
                            {loading ? "Generating..." : "Generate Thumbnails"}
                        </Button>
                    </div>

                    {/* Thumbnail Gallery */}
                    {loading ? (
                        <div className="grid grid-cols-3 gap-4">
                            {[...Array(3)].map((_, i) => (
                                <Skeleton key={i} className="aspect-video w-full" />
                            ))}
                        </div>
                    ) : thumbnails.length > 0 ? (
                        <>
                            <div className="grid grid-cols-3 gap-4">
                                {thumbnails.map((thumbnail, index) => (
                                    <div
                                        key={thumbnail.id}
                                        className={`border-2 rounded-lg overflow-hidden cursor-pointer transition-all ${selectedIndex === index
                                            ? "border-primary ring-2 ring-primary"
                                            : "border-transparent hover:border-primary/50"
                                            }`}
                                        onClick={() => setSelectedIndex(index)}
                                    >
                                        <div className="relative">
                                            <img
                                                src={thumbnail.image_url}
                                                alt={`Thumbnail ${index + 1}`}
                                                className="w-full aspect-video object-cover"
                                                style={selectedIndex === index && showEditor ? getFilterStyle() : {}}
                                            />
                                            {selectedIndex === index && (
                                                <div className="absolute top-2 right-2">
                                                    <Check className="h-6 w-6 text-primary bg-white rounded-full p-1 shadow-lg" />
                                                </div>
                                            )}
                                        </div>
                                        <div className="p-2 text-center">
                                            <p className="text-xs text-muted-foreground capitalize">
                                                {thumbnail.style} Style
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Editor */}
                            {selectedIndex !== null && (
                                <div className="border rounded-lg p-4 space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h3 className="font-semibold flex items-center gap-2">
                                            <Sliders className="h-4 w-4" />
                                            Edit Thumbnail
                                        </h3>
                                        <Switch
                                            checked={showEditor}
                                            onCheckedChange={setShowEditor}
                                        />
                                    </div>

                                    {showEditor && (
                                        <div className="space-y-4">
                                            <div>
                                                <div className="flex items-center justify-between mb-2">
                                                    <Label>Brightness</Label>
                                                    <span className="text-sm text-muted-foreground">
                                                        {brightness}%
                                                    </span>
                                                </div>
                                                <Slider
                                                    value={[brightness]}
                                                    onValueChange={(v: number[]) => setBrightness(v[0])}
                                                    min={50}
                                                    max={150}
                                                    step={1}
                                                />
                                            </div>

                                            <div>
                                                <div className="flex items-center justify-between mb-2">
                                                    <Label>Contrast</Label>
                                                    <span className="text-sm text-muted-foreground">
                                                        {contrast}%
                                                    </span>
                                                </div>
                                                <Slider
                                                    value={[contrast]}
                                                    onValueChange={(v: number[]) => setContrast(v[0])}
                                                    min={50}
                                                    max={150}
                                                    step={1}
                                                />
                                            </div>

                                            <div>
                                                <div className="flex items-center justify-between mb-2">
                                                    <Label>Saturation</Label>
                                                    <span className="text-sm text-muted-foreground">
                                                        {saturation}%
                                                    </span>
                                                </div>
                                                <Slider
                                                    value={[saturation]}
                                                    onValueChange={(v: number[]) => setSaturation(v[0])}
                                                    min={0}
                                                    max={200}
                                                    step={1}
                                                />
                                            </div>

                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => {
                                                    setBrightness(100)
                                                    setContrast(100)
                                                    setSaturation(100)
                                                }}
                                            >
                                                Reset Filters
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex justify-between gap-2">
                                <div className="flex gap-2">
                                    {selectedIndex !== null && (
                                        <Button
                                            variant="outline"
                                            onClick={() =>
                                                downloadThumbnail(
                                                    thumbnails[selectedIndex].image_url,
                                                    selectedIndex
                                                )
                                            }
                                        >
                                            <Download className="mr-2 h-4 w-4" />
                                            Download
                                        </Button>
                                    )}
                                </div>
                                <div className="flex gap-2">
                                    <Button variant="outline" onClick={generateThumbnails}>
                                        Regenerate
                                    </Button>
                                    <Button
                                        onClick={applyThumbnail}
                                        disabled={selectedIndex === null}
                                    >
                                        Set as Thumbnail
                                    </Button>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="text-center py-8 text-muted-foreground">
                            <p>No thumbnails generated yet</p>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}
