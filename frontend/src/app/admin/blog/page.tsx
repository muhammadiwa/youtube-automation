"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { motion } from "framer-motion"
import {
    FileText,
    Plus,
    RefreshCcw,
    Search,
    MoreHorizontal,
    Pencil,
    Trash2,
    Eye,
    EyeOff,
    Calendar,
    Clock,
    Tag,
    Star,
    Upload,
    X,
    ImageIcon,
    Sparkles,
    Wand2,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import apiClient from "@/lib/api/client"
import { type Article } from "@/lib/api/admin"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"
// Base URL without /api/v1 for serving images
const BASE_URL = API_URL.replace(/\/api\/v1$/, "")

const statusConfig = {
    draft: { label: "Draft", color: "bg-gray-500/10 text-gray-500 border-gray-500/20" },
    published: { label: "Published", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
    archived: { label: "Archived", color: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
}

const defaultCategories = ["Growth", "Tutorial", "Analytics", "SEO", "Monetization", "Community", "News", "Updates"]

// Helper function to make authenticated requests using apiClient's token
async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = apiClient.getAccessToken()
    if (!token) {
        console.warn("No auth token found in apiClient")
    }
    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
    })
}

export default function BlogAdminPage() {
    const { addToast } = useToast()

    const [articles, setArticles] = useState<Article[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [isLoading, setIsLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [categoryFilter, setCategoryFilter] = useState<string>("all")

    // Form state
    const [isFormOpen, setIsFormOpen] = useState(false)
    const [editingArticle, setEditingArticle] = useState<Article | null>(null)
    const [formTitle, setFormTitle] = useState("")
    const [formSlug, setFormSlug] = useState("")
    const [formExcerpt, setFormExcerpt] = useState("")
    const [formContent, setFormContent] = useState("")
    const [formCategory, setFormCategory] = useState("Tutorial")
    const [formTags, setFormTags] = useState("")
    const [formFeatured, setFormFeatured] = useState(false)
    const [formReadTime, setFormReadTime] = useState(5)
    const [formMetaTitle, setFormMetaTitle] = useState("")
    const [formMetaDescription, setFormMetaDescription] = useState("")
    const [formImage, setFormImage] = useState<File | null>(null)
    const [formImagePreview, setFormImagePreview] = useState<string | null>(null)
    const [formImageStorageKey, setFormImageStorageKey] = useState<string | null>(null)  // For AI-generated images
    const [isSaving, setIsSaving] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Delete state
    const [deleteArticleItem, setDeleteArticleItem] = useState<Article | null>(null)
    const [isDeleting, setIsDeleting] = useState(false)

    // AI Generation state
    const [isAIDialogOpen, setIsAIDialogOpen] = useState(false)
    const [aiTopic, setAiTopic] = useState("")
    const [aiCategory, setAiCategory] = useState("Tutorial")
    const [aiLanguage, setAiLanguage] = useState("id")
    const [aiGenerateThumbnail, setAiGenerateThumbnail] = useState(true)
    const [isGenerating, setIsGenerating] = useState(false)

    const fetchArticles = useCallback(async () => {
        setIsLoading(true)
        try {
            const params = new URLSearchParams({ page: page.toString(), page_size: "20" })
            if (categoryFilter !== "all") params.set("category", categoryFilter)
            if (statusFilter !== "all") params.set("article_status", statusFilter)

            const res = await fetchWithAuth(`${API_URL}/blog/admin/articles?${params}`)
            if (res.status === 401 || res.status === 403) {
                const errorData = await res.json().catch(() => ({}))
                addToast({ type: "error", title: "Authentication Error", description: errorData.detail || "Please login again" })
                setArticles([])
                return
            }
            if (!res.ok) throw new Error("Failed to fetch")
            const data = await res.json()
            setArticles(data.items)
            setTotal(data.total)
            setTotalPages(data.total_pages)
        } catch (err) {
            addToast({ type: "error", title: "Error", description: "Failed to load articles" })
            setArticles([])
        } finally {
            setIsLoading(false)
        }
    }, [page, statusFilter, categoryFilter, addToast])

    useEffect(() => { fetchArticles() }, [fetchArticles])

    const generateSlug = (title: string) => title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "")

    const resetForm = () => {
        setFormTitle(""); setFormSlug(""); setFormExcerpt(""); setFormContent("")
        setFormCategory("Tutorial"); setFormTags(""); setFormFeatured(false)
        setFormReadTime(5); setFormMetaTitle(""); setFormMetaDescription("")
        setFormImage(null); setFormImagePreview(null); setFormImageStorageKey(null); setEditingArticle(null)
    }

    const openCreateForm = () => { resetForm(); setIsFormOpen(true) }

    const openEditForm = (article: Article) => {
        setEditingArticle(article)
        setFormTitle(article.title); setFormSlug(article.slug)
        setFormExcerpt(article.excerpt || ""); setFormContent(article.content)
        setFormCategory(article.category); setFormTags(article.tags?.join(", ") || "")
        setFormFeatured(article.featured); setFormReadTime(article.read_time_minutes)
        setFormMetaTitle(article.meta_title || ""); setFormMetaDescription(article.meta_description || "")
        setFormImage(null)
        // Handle both cloud storage URLs and local storage paths
        if (article.featured_image) {
            const imageUrl = article.featured_image.startsWith("http")
                ? article.featured_image
                : `${BASE_URL}${article.featured_image}`
            setFormImagePreview(imageUrl)
        } else {
            setFormImagePreview(null)
        }
        setIsFormOpen(true)
    }

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            if (file.size > 5 * 1024 * 1024) {
                addToast({ type: "error", title: "Error", description: "Image must be less than 5MB" })
                return
            }
            setFormImage(file)
            setFormImagePreview(URL.createObjectURL(file))
        }
    }

    const removeImage = () => { setFormImage(null); setFormImagePreview(null); setFormImageStorageKey(null) }

    const handleSave = async () => {
        if (!formTitle.trim() || !formContent.trim() || !formSlug.trim()) return
        setIsSaving(true)
        try {
            const formData = new FormData()
            formData.append("title", formTitle)
            formData.append("slug", formSlug)
            formData.append("content", formContent)
            formData.append("category", formCategory)
            if (formExcerpt) formData.append("excerpt", formExcerpt)
            if (formTags) formData.append("tags", formTags)
            if (formMetaTitle) formData.append("meta_title", formMetaTitle)
            if (formMetaDescription) formData.append("meta_description", formMetaDescription)
            formData.append("featured", formFeatured.toString())
            formData.append("read_time_minutes", formReadTime.toString())

            // Handle image: either upload new file or use existing storage key
            if (formImage) {
                formData.append("featured_image", formImage)
            } else if (formImageStorageKey) {
                // Use storage key from AI generation
                formData.append("featured_image_key", formImageStorageKey)
            }

            const url = editingArticle
                ? `${API_URL}/blog/admin/articles/${editingArticle.id}`
                : `${API_URL}/blog/admin/articles`

            const res = await fetchWithAuth(url, {
                method: editingArticle ? "PUT" : "POST",
                body: formData,
            })

            if (!res.ok) throw new Error("Failed to save")
            addToast({ type: "success", title: editingArticle ? "Article updated" : "Article created" })
            setIsFormOpen(false); resetForm(); fetchArticles()
        } catch {
            addToast({ type: "error", title: "Error", description: "Failed to save article" })
        } finally {
            setIsSaving(false)
        }
    }

    const handlePublish = async (article: Article) => {
        try {
            const res = await fetchWithAuth(`${API_URL}/blog/admin/articles/${article.id}/publish`, { method: "POST" })
            if (!res.ok) throw new Error()
            fetchArticles()
            addToast({ type: "success", title: "Article published" })
        } catch {
            addToast({ type: "error", title: "Error", description: "Failed to publish" })
        }
    }

    const handleUnpublish = async (article: Article) => {
        try {
            const res = await fetchWithAuth(`${API_URL}/blog/admin/articles/${article.id}/unpublish`, { method: "POST" })
            if (!res.ok) throw new Error()
            fetchArticles()
            addToast({ type: "success", title: "Article unpublished" })
        } catch {
            addToast({ type: "error", title: "Error", description: "Failed to unpublish" })
        }
    }

    const handleDelete = async () => {
        if (!deleteArticleItem) return
        setIsDeleting(true)
        try {
            const res = await fetchWithAuth(`${API_URL}/blog/admin/articles/${deleteArticleItem.id}`, { method: "DELETE" })
            if (!res.ok) throw new Error()
            addToast({ type: "success", title: "Article deleted" })
            setDeleteArticleItem(null); fetchArticles()
        } catch {
            addToast({ type: "error", title: "Error", description: "Failed to delete" })
        } finally {
            setIsDeleting(false)
        }
    }

    const formatDate = (dateStr: string) => new Date(dateStr).toLocaleDateString()
    const filteredArticles = articles.filter(a => !searchQuery || a.title.toLowerCase().includes(searchQuery.toLowerCase()))

    const getImageUrl = (image: string | null) => {
        if (!image) return null
        if (image.startsWith("http://") || image.startsWith("https://")) return image
        return `${BASE_URL}${image}`
    }

    // AI Generation handler
    const handleAIGenerate = async () => {
        if (!aiTopic.trim()) {
            addToast({ type: "error", title: "Error", description: "Please enter a topic" })
            return
        }
        setIsGenerating(true)
        try {
            const formData = new FormData()
            formData.append("topic", aiTopic)
            formData.append("category", aiCategory)
            formData.append("language", aiLanguage)
            formData.append("generate_thumbnail", aiGenerateThumbnail.toString())

            const res = await fetchWithAuth(`${API_URL}/blog/admin/generate`, {
                method: "POST",
                body: formData,
            })

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}))
                throw new Error(errorData.detail || "Failed to generate")
            }

            const result = await res.json()
            if (result.success && result.data) {
                const data = result.data
                // Fill form with generated content
                setFormTitle(data.title || "")
                setFormSlug(data.slug || generateSlug(data.title || ""))
                setFormExcerpt(data.excerpt || "")
                setFormContent(data.content || "")
                setFormCategory(aiCategory)
                setFormTags(data.tags?.join(", ") || "")
                setFormMetaTitle(data.meta_title || "")
                setFormMetaDescription(data.meta_description || "")
                setFormReadTime(data.read_time_minutes || 5)
                setFormFeatured(false)

                // Handle generated thumbnail - use featured_image_url for preview
                if (data.featured_image_url) {
                    setFormImagePreview(data.featured_image_url)
                    setFormImageStorageKey(data.featured_image || null)  // Save storage key for saving
                } else if (data.featured_image) {
                    // Fallback: try to construct URL
                    const imageUrl = data.featured_image.startsWith("http")
                        ? data.featured_image
                        : getImageUrl(data.featured_image)
                    setFormImagePreview(imageUrl)
                    setFormImageStorageKey(data.featured_image)
                }

                setIsAIDialogOpen(false)
                setIsFormOpen(true)
                addToast({ type: "success", title: "Content Generated", description: "AI has generated your blog content. Review and edit before saving." })
            }
        } catch (err: any) {
            addToast({ type: "error", title: "Generation Failed", description: err.message || "Failed to generate content" })
        } finally {
            setIsGenerating(false)
        }
    }

    const openAIDialog = () => {
        setAiTopic("")
        setAiCategory("Tutorial")
        setAiLanguage("id")
        setAiGenerateThumbnail(true)
        setIsAIDialogOpen(true)
    }

    return (
        <AdminLayout breadcrumbs={[{ label: "Blog" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center gap-3">
                        <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shadow-lg">
                            <FileText className="h-6 w-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">Blog Management</h1>
                            <p className="text-muted-foreground">Create and manage blog articles</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button variant="outline" size="icon" onClick={fetchArticles} disabled={isLoading}><RefreshCcw className={cn("h-4 w-4", isLoading && "animate-spin")} /></Button>
                        <Button variant="outline" onClick={openAIDialog} className="bg-gradient-to-r from-violet-500/10 to-purple-500/10 border-violet-500/20 hover:border-violet-500/40">
                            <Sparkles className="h-4 w-4 mr-2 text-violet-500" />
                            <span className="bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent font-medium">Generate with AI</span>
                        </Button>
                        <Button onClick={openCreateForm}><Plus className="h-4 w-4 mr-2" />New Article</Button>
                    </div>
                </motion.div>

                {/* Filters */}
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex flex-col sm:flex-row gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input placeholder="Search articles..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
                            </div>
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-[150px]"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Status</SelectItem>
                                    <SelectItem value="draft">Draft</SelectItem>
                                    <SelectItem value="published">Published</SelectItem>
                                </SelectContent>
                            </Select>
                            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                                <SelectTrigger className="w-[150px]"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Categories</SelectItem>
                                    {defaultCategories.map(cat => <SelectItem key={cat} value={cat}>{cat}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                {/* Articles List */}
                <Card>
                    <CardHeader>
                        <CardTitle>All Articles</CardTitle>
                        <CardDescription>{total} articles</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <div className="flex flex-col items-center justify-center py-12">
                                <div className="h-12 w-12 rounded-full border-4 border-purple-500/20 border-t-purple-500 animate-spin" />
                            </div>
                        ) : filteredArticles.length === 0 ? (
                            <div className="text-center py-12 text-muted-foreground">
                                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>No articles found</p>
                                <Button onClick={openCreateForm} className="mt-4"><Plus className="h-4 w-4 mr-2" />Create First Article</Button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {filteredArticles.map((article) => (
                                    <div key={article.id} className={cn("p-4 rounded-lg border flex gap-4", article.status === "draft" && "opacity-70")}>
                                        {/* Thumbnail */}
                                        <div className="w-24 h-24 rounded-lg overflow-hidden bg-gradient-to-br from-purple-100 to-pink-100 flex-shrink-0">
                                            {article.featured_image ? (
                                                <img src={getImageUrl(article.featured_image)!} alt={article.title} className="w-full h-full object-cover" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center"><ImageIcon className="h-8 w-8 text-purple-300" /></div>
                                            )}
                                        </div>
                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className="font-medium">{article.title}</span>
                                                {article.featured && <Star className="h-4 w-4 text-amber-500 fill-amber-500" />}
                                                <Badge variant="outline" className={statusConfig[article.status].color}>{statusConfig[article.status].label}</Badge>
                                                <Badge variant="outline"><Tag className="h-3 w-3 mr-1" />{article.category}</Badge>
                                            </div>
                                            {article.excerpt && <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{article.excerpt}</p>}
                                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                                <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(article.created_at)}</span>
                                                <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{article.read_time_minutes} min</span>
                                                <span className="flex items-center gap-1"><Eye className="h-3 w-3" />{article.view_count} views</span>
                                            </div>
                                        </div>
                                        {/* Actions */}
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild><Button variant="ghost" size="icon"><MoreHorizontal className="h-4 w-4" /></Button></DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem onClick={() => window.open(`/blog/${article.slug}`, "_blank")}><Eye className="h-4 w-4 mr-2" />Preview</DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => openEditForm(article)}><Pencil className="h-4 w-4 mr-2" />Edit</DropdownMenuItem>
                                                {article.status === "draft" ? (
                                                    <DropdownMenuItem onClick={() => handlePublish(article)}><Eye className="h-4 w-4 mr-2" />Publish</DropdownMenuItem>
                                                ) : article.status === "published" ? (
                                                    <DropdownMenuItem onClick={() => handleUnpublish(article)}><EyeOff className="h-4 w-4 mr-2" />Unpublish</DropdownMenuItem>
                                                ) : null}
                                                <DropdownMenuSeparator />
                                                <DropdownMenuItem onClick={() => setDeleteArticleItem(article)} className="text-red-600"><Trash2 className="h-4 w-4 mr-2" />Delete</DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                ))}
                            </div>
                        )}
                        {totalPages > 1 && (
                            <div className="flex items-center justify-between mt-6 pt-6 border-t">
                                <p className="text-sm text-muted-foreground">Page {page} of {totalPages}</p>
                                <div className="flex gap-2">
                                    <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Previous</Button>
                                    <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>Next</Button>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Create/Edit Dialog */}
            <Dialog open={isFormOpen} onOpenChange={(open) => { if (!open) resetForm(); setIsFormOpen(open) }}>
                <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>{editingArticle ? "Edit Article" : "Create Article"}</DialogTitle>
                        <DialogDescription>{editingArticle ? "Update the article details." : "Create a new blog article."}</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        {/* Image Upload */}
                        <div className="space-y-2">
                            <Label>Featured Image</Label>
                            <div className="border-2 border-dashed rounded-lg p-4">
                                {formImagePreview ? (
                                    <div className="relative">
                                        <img src={formImagePreview} alt="Preview" className="w-full h-48 object-cover rounded-lg" />
                                        <Button variant="destructive" size="icon" className="absolute top-2 right-2" onClick={removeImage}><X className="h-4 w-4" /></Button>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center py-8 cursor-pointer" onClick={() => fileInputRef.current?.click()}>
                                        <Upload className="h-10 w-10 text-muted-foreground mb-2" />
                                        <p className="text-sm text-muted-foreground">Click to upload image (max 5MB)</p>
                                    </div>
                                )}
                                <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleImageChange} />
                            </div>
                        </div>
                        <div className="grid gap-2">
                            <Label>Title *</Label>
                            <Input placeholder="Article title..." value={formTitle} onChange={(e) => { setFormTitle(e.target.value); if (!editingArticle) setFormSlug(generateSlug(e.target.value)) }} />
                        </div>
                        <div className="grid gap-2">
                            <Label>Slug *</Label>
                            <Input placeholder="article-url-slug" value={formSlug} onChange={(e) => setFormSlug(e.target.value)} />
                        </div>
                        <div className="grid gap-2">
                            <Label>Excerpt</Label>
                            <Textarea placeholder="Brief summary..." value={formExcerpt} onChange={(e) => setFormExcerpt(e.target.value)} rows={2} />
                        </div>
                        <div className="grid gap-2">
                            <Label>Content * (HTML supported)</Label>
                            <Textarea placeholder="Article content..." value={formContent} onChange={(e) => setFormContent(e.target.value)} rows={10} className="font-mono text-sm" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label>Category</Label>
                                <Select value={formCategory} onValueChange={setFormCategory}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>{defaultCategories.map(cat => <SelectItem key={cat} value={cat}>{cat}</SelectItem>)}</SelectContent>
                                </Select>
                            </div>
                            <div className="grid gap-2">
                                <Label>Read Time (min)</Label>
                                <Input type="number" min={1} value={formReadTime} onChange={(e) => setFormReadTime(parseInt(e.target.value) || 5)} />
                            </div>
                        </div>
                        <div className="grid gap-2">
                            <Label>Tags (comma separated)</Label>
                            <Input placeholder="youtube, automation, tips" value={formTags} onChange={(e) => setFormTags(e.target.value)} />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label>Meta Title (SEO)</Label>
                                <Input placeholder="SEO title..." value={formMetaTitle} onChange={(e) => setFormMetaTitle(e.target.value)} />
                            </div>
                            <div className="grid gap-2">
                                <Label>Meta Description</Label>
                                <Input placeholder="SEO description..." value={formMetaDescription} onChange={(e) => setFormMetaDescription(e.target.value)} />
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <div><Label>Featured Article</Label><p className="text-sm text-muted-foreground">Display prominently</p></div>
                            <Switch checked={formFeatured} onCheckedChange={setFormFeatured} />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsFormOpen(false)}>Cancel</Button>
                        <Button onClick={handleSave} disabled={!formTitle.trim() || !formContent.trim() || !formSlug.trim() || isSaving}>
                            {isSaving ? <RefreshCcw className="h-4 w-4 mr-2 animate-spin" /> : null}{isSaving ? "Saving..." : editingArticle ? "Update" : "Create"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Dialog */}
            <Dialog open={!!deleteArticleItem} onOpenChange={() => setDeleteArticleItem(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Article</DialogTitle>
                        <DialogDescription>Are you sure you want to delete &quot;{deleteArticleItem?.title}&quot;?</DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDeleteArticleItem(null)}>Cancel</Button>
                        <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>{isDeleting ? "Deleting..." : "Delete"}</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* AI Generation Dialog */}
            <Dialog open={isAIDialogOpen} onOpenChange={setIsAIDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-violet-500" />
                            Generate Blog with AI
                        </DialogTitle>
                        <DialogDescription>
                            Let AI create a complete blog post for you. Just describe the topic and select options.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Topic / Subject *</Label>
                            <Textarea
                                placeholder="e.g., How to grow YouTube subscribers fast in 2024, Tips for better video SEO, etc."
                                value={aiTopic}
                                onChange={(e) => setAiTopic(e.target.value)}
                                rows={3}
                            />
                            <p className="text-xs text-muted-foreground">Be specific for better results</p>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Category</Label>
                                <Select value={aiCategory} onValueChange={setAiCategory}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        {defaultCategories.map(cat => (
                                            <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label>Language</Label>
                                <Select value={aiLanguage} onValueChange={setAiLanguage}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="id">Indonesian</SelectItem>
                                        <SelectItem value="en">English</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                            <div>
                                <Label>Generate Thumbnail</Label>
                                <p className="text-xs text-muted-foreground">AI will create a matching image</p>
                            </div>
                            <Switch checked={aiGenerateThumbnail} onCheckedChange={setAiGenerateThumbnail} />
                        </div>
                        {isGenerating && (
                            <div className="p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
                                <div className="flex items-center gap-3">
                                    <div className="h-8 w-8 rounded-full border-2 border-violet-500/30 border-t-violet-500 animate-spin" />
                                    <div>
                                        <p className="font-medium text-violet-700 dark:text-violet-300">Generating content...</p>
                                        <p className="text-xs text-muted-foreground">This may take 30-60 seconds</p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsAIDialogOpen(false)} disabled={isGenerating}>Cancel</Button>
                        <Button
                            onClick={handleAIGenerate}
                            disabled={!aiTopic.trim() || isGenerating}
                            className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700"
                        >
                            {isGenerating ? (
                                <>
                                    <RefreshCcw className="h-4 w-4 mr-2 animate-spin" />
                                    Generating...
                                </>
                            ) : (
                                <>
                                    <Wand2 className="h-4 w-4 mr-2" />
                                    Generate
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AdminLayout>
    )
}
