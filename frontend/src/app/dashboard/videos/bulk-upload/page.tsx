"use client"

import { useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Download, Upload, FileSpreadsheet, AlertCircle, CheckCircle2, Edit2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

interface CSVRow {
    id: string
    title: string
    description: string
    tags: string
    categoryId: string
    visibility: "public" | "unlisted" | "private"
    scheduledPublishAt?: string
    errors: string[]
    isValid: boolean
}

const CSV_TEMPLATE = `title,description,tags,categoryId,visibility,scheduledPublishAt
"My First Video","This is a great video about...","tutorial,howto,guide","22","public",""
"My Second Video","Another amazing video","vlog,daily","22","unlisted","2024-12-25T10:00:00Z"
"Private Video","This is private","test","22","private",""`

export default function BulkUploadPage() {
    const router = useRouter()
    const [csvFile, setCSVFile] = useState<File | null>(null)
    const [parsedData, setParsedData] = useState<CSVRow[]>([])
    const [isDragging, setIsDragging] = useState(false)
    const [isEditing, setIsEditing] = useState(false)
    const [editingRow, setEditingRow] = useState<string | null>(null)

    const downloadTemplate = () => {
        const blob = new Blob([CSV_TEMPLATE], { type: "text/csv" })
        const url = URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = "video-upload-template.csv"
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    const validateRow = (row: any, index: number): CSVRow => {
        const errors: string[] = []

        if (!row.title || row.title.trim() === "") {
            errors.push("Title is required")
        } else if (row.title.length > 100) {
            errors.push("Title must be 100 characters or less")
        }

        if (row.description && row.description.length > 5000) {
            errors.push("Description must be 5000 characters or less")
        }

        if (!["public", "unlisted", "private"].includes(row.visibility)) {
            errors.push("Visibility must be: public, unlisted, or private")
        }

        if (row.scheduledPublishAt && row.scheduledPublishAt.trim() !== "") {
            const date = new Date(row.scheduledPublishAt)
            if (isNaN(date.getTime())) {
                errors.push("Invalid scheduled publish date format")
            } else if (date < new Date()) {
                errors.push("Scheduled publish date must be in the future")
            }
        }

        return {
            id: `row-${index}`,
            title: row.title || "",
            description: row.description || "",
            tags: row.tags || "",
            categoryId: row.categoryId || "22",
            visibility: row.visibility || "private",
            scheduledPublishAt: row.scheduledPublishAt || undefined,
            errors,
            isValid: errors.length === 0,
        }
    }

    const parseCSV = (text: string): CSVRow[] => {
        const lines = text.split("\n").filter((line) => line.trim() !== "")
        if (lines.length < 2) {
            return []
        }

        // Simple CSV parser (in production, use a library like papaparse)
        const headers = lines[0].split(",").map((h) => h.trim().replace(/"/g, ""))
        const rows: CSVRow[] = []

        for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(",").map((v) => v.trim().replace(/^"|"$/g, ""))
            const row: any = {}
            headers.forEach((header, index) => {
                row[header] = values[index] || ""
            })
            rows.push(validateRow(row, i))
        }

        return rows
    }

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            handleFile(file)
        }
        e.target.value = "" // Reset input
    }

    const handleFile = (file: File) => {
        if (!file.name.endsWith(".csv")) {
            alert("Please upload a CSV file")
            return
        }

        setCSVFile(file)
        const reader = new FileReader()
        reader.onload = (e) => {
            const text = e.target?.result as string
            const parsed = parseCSV(text)
            setParsedData(parsed)
        }
        reader.readAsText(file)
    }

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
        const file = e.dataTransfer.files[0]
        if (file) {
            handleFile(file)
        }
    }, [])

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }, [])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
    }, [])

    const updateRow = (id: string, field: keyof CSVRow, value: any) => {
        setParsedData((prev) =>
            prev.map((row) => {
                if (row.id === id) {
                    const updated = { ...row, [field]: value }
                    return validateRow(updated, parseInt(id.split("-")[1]))
                }
                return row
            })
        )
    }

    const removeRow = (id: string) => {
        setParsedData((prev) => prev.filter((row) => row.id !== id))
    }

    const handleSubmit = async () => {
        const validRows = parsedData.filter((row) => row.isValid)
        if (validRows.length === 0) {
            alert("No valid rows to upload")
            return
        }

        if (!confirm(`Upload ${validRows.length} video(s)?`)) {
            return
        }

        try {
            // In a real implementation, this would call the API
            console.log("Uploading:", validRows)
            alert(`${validRows.length} upload jobs created successfully!`)
            router.push("/dashboard/videos")
        } catch (error) {
            console.error("Failed to create upload jobs:", error)
            alert("Failed to create upload jobs")
        }
    }

    const validCount = parsedData.filter((row) => row.isValid).length
    const invalidCount = parsedData.filter((row) => !row.isValid).length

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Bulk Upload Videos</h1>
                    <p className="text-muted-foreground">Upload multiple videos using a CSV file</p>
                </div>
                <Button variant="outline" onClick={() => router.push("/dashboard/videos")}>
                    Back to Videos
                </Button>
            </div>

            {/* Template Download */}
            <Card>
                <CardHeader>
                    <CardTitle>Step 1: Download Template</CardTitle>
                    <CardDescription>
                        Download the CSV template and fill in your video details
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Button onClick={downloadTemplate} variant="outline">
                        <Download className="mr-2 h-4 w-4" />
                        Download CSV Template
                    </Button>
                    <div className="mt-4 p-4 bg-muted rounded-lg">
                        <h4 className="font-semibold mb-2">Template Fields:</h4>
                        <ul className="text-sm space-y-1 text-muted-foreground">
                            <li>
                                <strong>title</strong> (required): Video title (max 100 characters)
                            </li>
                            <li>
                                <strong>description</strong> (optional): Video description (max 5000 characters)
                            </li>
                            <li>
                                <strong>tags</strong> (optional): Comma-separated tags
                            </li>
                            <li>
                                <strong>categoryId</strong> (optional): YouTube category ID (default: 22)
                            </li>
                            <li>
                                <strong>visibility</strong> (required): public, unlisted, or private
                            </li>
                            <li>
                                <strong>scheduledPublishAt</strong> (optional): ISO 8601 date format
                            </li>
                        </ul>
                    </div>
                </CardContent>
            </Card>

            {/* CSV Upload */}
            <Card>
                <CardHeader>
                    <CardTitle>Step 2: Upload CSV File</CardTitle>
                    <CardDescription>Upload your completed CSV file</CardDescription>
                </CardHeader>
                <CardContent>
                    <div
                        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${isDragging
                                ? "border-primary bg-primary/5"
                                : "border-muted-foreground/25 hover:border-primary/50"
                            }`}
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                    >
                        <FileSpreadsheet className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">Drag and drop CSV file here</h3>
                        <p className="text-sm text-muted-foreground mb-4">or click to browse</p>
                        <input
                            type="file"
                            id="csv-upload"
                            className="hidden"
                            accept=".csv"
                            onChange={handleFileInput}
                        />
                        <Button asChild>
                            <label htmlFor="csv-upload" className="cursor-pointer">
                                Browse Files
                            </label>
                        </Button>
                        {csvFile && (
                            <p className="text-sm text-muted-foreground mt-4">
                                Selected: {csvFile.name}
                            </p>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Preview and Edit */}
            {parsedData.length > 0 && (
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle>Step 3: Review and Edit</CardTitle>
                                <CardDescription>
                                    Review parsed entries and fix any errors before submitting
                                </CardDescription>
                            </div>
                            <div className="flex gap-2">
                                <Badge variant="default">{validCount} valid</Badge>
                                {invalidCount > 0 && (
                                    <Badge variant="destructive">{invalidCount} invalid</Badge>
                                )}
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {parsedData.map((row) => (
                                <div
                                    key={row.id}
                                    className={`border rounded-lg p-4 ${!row.isValid ? "border-destructive bg-destructive/5" : ""
                                        }`}
                                >
                                    <div className="flex items-start gap-3">
                                        {row.isValid ? (
                                            <CheckCircle2 className="h-5 w-5 text-green-500 mt-1" />
                                        ) : (
                                            <AlertCircle className="h-5 w-5 text-destructive mt-1" />
                                        )}
                                        <div className="flex-1 min-w-0">
                                            {editingRow === row.id ? (
                                                <div className="space-y-3">
                                                    <div>
                                                        <Label>Title</Label>
                                                        <Input
                                                            value={row.title}
                                                            onChange={(e) =>
                                                                updateRow(row.id, "title", e.target.value)
                                                            }
                                                        />
                                                    </div>
                                                    <div>
                                                        <Label>Description</Label>
                                                        <Input
                                                            value={row.description}
                                                            onChange={(e) =>
                                                                updateRow(row.id, "description", e.target.value)
                                                            }
                                                        />
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-3">
                                                        <div>
                                                            <Label>Visibility</Label>
                                                            <Select
                                                                value={row.visibility}
                                                                onValueChange={(value) =>
                                                                    updateRow(row.id, "visibility", value)
                                                                }
                                                            >
                                                                <SelectTrigger>
                                                                    <SelectValue />
                                                                </SelectTrigger>
                                                                <SelectContent>
                                                                    <SelectItem value="public">Public</SelectItem>
                                                                    <SelectItem value="unlisted">Unlisted</SelectItem>
                                                                    <SelectItem value="private">Private</SelectItem>
                                                                </SelectContent>
                                                            </Select>
                                                        </div>
                                                        <div>
                                                            <Label>Tags</Label>
                                                            <Input
                                                                value={row.tags}
                                                                onChange={(e) =>
                                                                    updateRow(row.id, "tags", e.target.value)
                                                                }
                                                            />
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <Button
                                                            size="sm"
                                                            onClick={() => setEditingRow(null)}
                                                        >
                                                            Done
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            variant="outline"
                                                            onClick={() => removeRow(row.id)}
                                                        >
                                                            Remove
                                                        </Button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <>
                                                    <div className="flex items-start justify-between gap-2 mb-2">
                                                        <div className="flex-1 min-w-0">
                                                            <p className="font-medium">{row.title}</p>
                                                            {row.description && (
                                                                <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                                                                    {row.description}
                                                                </p>
                                                            )}
                                                            <div className="flex items-center gap-2 mt-2">
                                                                <Badge variant="outline">{row.visibility}</Badge>
                                                                {row.tags && (
                                                                    <span className="text-xs text-muted-foreground">
                                                                        Tags: {row.tags}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={() => setEditingRow(row.id)}
                                                        >
                                                            <Edit2 className="h-4 w-4" />
                                                        </Button>
                                                    </div>
                                                    {row.errors.length > 0 && (
                                                        <div className="space-y-1 mt-2">
                                                            {row.errors.map((error, i) => (
                                                                <div
                                                                    key={i}
                                                                    className="flex items-center gap-2 text-sm text-destructive"
                                                                >
                                                                    <AlertCircle className="h-3 w-3" />
                                                                    {error}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="flex justify-end gap-2 mt-6">
                            <Button
                                variant="outline"
                                onClick={() => {
                                    setParsedData([])
                                    setCSVFile(null)
                                }}
                            >
                                Clear
                            </Button>
                            <Button onClick={handleSubmit} disabled={validCount === 0}>
                                <Upload className="mr-2 h-4 w-4" />
                                Create {validCount} Upload Job{validCount !== 1 ? "s" : ""}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
