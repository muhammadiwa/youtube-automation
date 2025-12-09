"use client"

import { useState } from "react"
import { Sparkles, Download, Check, Sliders } from "lucide-react"
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

interface AIThumbnailGeneratorProps {
    videoId: string
    onApply: (thumbnailUrl: string) => void
}

export function AIThumbnailGenerator({ videoId, onApply }: AIThumbnailGeneratorProps) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [thumbnails, setThumbnails] = useState<ThumbnailResult[]>([])
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
    const [showEditor, setShowEditor] = useState(false)

    // Generation options
    const [style, setStyle] = useState<"modern" | "classic" | "bold" | "minimal">("modern")
    const [includeText, setIncludeText] = useState(true)
    const [text, setText] = useState("")

    // Editor options
    const [brightness, setBrightness] = useState(100)
    const [contrast, setContrast] = useState(100)
    const [saturation, setSaturation] = useState(100)

    const generateThumbnails = async () => {
        try {
            setLoading(true)
            const results = await aiApi.generateThumbnails({
                videoId,
                style,
                includeText,
                text: includeText ? text : undefined,
            })
            setThumbnails(results)
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
            onApply(thumbnails[selectedIndex].imageUrl)
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
                <Button variant="outline" size="sm">
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Thumbnails
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>AI Thumbnail Generator</DialogTitle>
                    <DialogDescription>
                        Generate 3 professional thumbnail variations for your video
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-6 mt-4">
                    {/* Generation Options */}
                    <div className="border rounded-lg p-4 space-y-4">
                        <h3 className="font-semibold">Generation Options</h3>

                        <div>
                            <Label>Style</Label>
                            <RadioGroup value={style} onValueChange={(v: any) => setStyle(v)}>
                                <div className="grid grid-cols-4 gap-2 mt-2">
                                    <div className="flex items-center space-x-2 border rounded p-2">
                                        <RadioGroupItem value="modern" id="modern" />
                                        <Label htmlFor="modern" className="font-normal cursor-pointer">
                                            Modern
                                        </Label>
                                    </div>
                                    <div className="flex items-center space-x-2 border rounded p-2">
                                        <RadioGroupItem value="classic" id="classic" />
                                        <Label htmlFor="classic" className="font-normal cursor-pointer">
                                            Classic
                                        </Label>
                                    </div>
                                    <div className="flex items-center space-x-2 border rounded p-2">
                                        <RadioGroupItem value="bold" id="bold" />
                                        <Label htmlFor="bold" className="font-normal cursor-pointer">
                                            Bold
                                        </Label>
                                    </div>
                                    <div className="flex items-center space-x-2 border rounded p-2">
                                        <RadioGroupItem value="minimal" id="minimal" />
                                        <Label htmlFor="minimal" className="font-normal cursor-pointer">
                                            Minimal
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
                                                src={thumbnail.imageUrl}
                                                alt={`Thumbnail ${index + 1}`}
                                                className="w-full aspect-video object-cover"
                                                style={selectedIndex === index && showEditor ? getFilterStyle() : {}}
                                            />
                                            {selectedIndex === index && (
                                                <div className="absolute top-2 right-2">
                                                    <Check className="h-6 w-6 text-primary bg-white rounded-full p-1" />
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
                                                    thumbnails[selectedIndex].imageUrl,
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
