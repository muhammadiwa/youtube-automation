"use client"

import { useEditor, EditorContent, Editor, Extension } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import Underline from "@tiptap/extension-underline"
import TextAlign from "@tiptap/extension-text-align"
import Link from "@tiptap/extension-link"
import Placeholder from "@tiptap/extension-placeholder"
import { TextStyle } from "@tiptap/extension-text-style"
import {
    Bold,
    Italic,
    Underline as UnderlineIcon,
    Strikethrough,
    List,
    ListOrdered,
    AlignLeft,
    AlignCenter,
    AlignRight,
    AlignJustify,
    Heading1,
    Heading2,
    Heading3,
    Link as LinkIcon,
    Unlink,
    Undo,
    Redo,
    Quote,
    Minus,
    Type,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useCallback, useEffect } from "react"

// Custom FontSize extension
declare module "@tiptap/core" {
    interface Commands<ReturnType> {
        fontSize: {
            setFontSize: (size: string) => ReturnType
            unsetFontSize: () => ReturnType
        }
    }
}

const FontSize = Extension.create({
    name: "fontSize",
    addOptions() {
        return {
            types: ["textStyle"],
        }
    },
    addGlobalAttributes() {
        return [
            {
                types: this.options.types,
                attributes: {
                    fontSize: {
                        default: null,
                        parseHTML: (element) => element.style.fontSize?.replace(/['"]+/g, ""),
                        renderHTML: (attributes) => {
                            if (!attributes.fontSize) {
                                return {}
                            }
                            return {
                                style: `font-size: ${attributes.fontSize}`,
                            }
                        },
                    },
                },
            },
        ]
    },
    addCommands() {
        return {
            setFontSize:
                (fontSize: string) =>
                    ({ chain }) => {
                        return chain().setMark("textStyle", { fontSize }).run()
                    },
            unsetFontSize:
                () =>
                    ({ chain }) => {
                        return chain().setMark("textStyle", { fontSize: null }).removeEmptyTextStyle().run()
                    },
        }
    },
})

interface RichTextEditorProps {
    content: string
    onChange: (html: string) => void
    placeholder?: string
    className?: string
    minHeight?: string
}

const fontSizes = [
    { label: "Small (12px)", value: "12px" },
    { label: "Normal (14px)", value: "14px" },
    { label: "Medium (16px)", value: "16px" },
    { label: "Large (18px)", value: "18px" },
    { label: "X-Large (24px)", value: "24px" },
    { label: "XX-Large (32px)", value: "32px" },
]


// Toolbar button component
function ToolbarButton({
    onClick,
    isActive,
    disabled,
    tooltip,
    children,
}: {
    onClick: () => void
    isActive?: boolean
    disabled?: boolean
    tooltip: string
    children: React.ReactNode
}) {
    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger asChild>
                    <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                            e.preventDefault()
                            onClick()
                        }}
                        disabled={disabled}
                        className={cn(
                            "h-8 w-8 p-0",
                            isActive && "bg-primary/20 text-primary"
                        )}
                    >
                        {children}
                    </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">
                    {tooltip}
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    )
}

// Toolbar component
function Toolbar({ editor }: { editor: Editor | null }) {
    const setLink = useCallback(() => {
        if (!editor) return
        const previousUrl = editor.getAttributes("link").href
        const url = window.prompt("Enter URL:", previousUrl)

        if (url === null) return
        if (url === "") {
            editor.chain().focus().extendMarkRange("link").unsetLink().run()
            return
        }

        editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run()
    }, [editor])

    const removeLink = useCallback(() => {
        if (!editor) return
        editor.chain().focus().unsetLink().run()
    }, [editor])

    if (!editor) return null

    return (
        <div className="flex flex-wrap items-center gap-0.5 p-2 border-b bg-slate-50 dark:bg-slate-900/50 rounded-t-lg">
            {/* Undo/Redo */}
            <ToolbarButton
                onClick={() => editor.chain().focus().undo().run()}
                disabled={!editor.can().undo()}
                tooltip="Undo (Ctrl+Z)"
            >
                <Undo className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={() => editor.chain().focus().redo().run()}
                disabled={!editor.can().redo()}
                tooltip="Redo (Ctrl+Y)"
            >
                <Redo className="h-4 w-4" />
            </ToolbarButton>

            <Separator orientation="vertical" className="mx-1 h-6" />

            {/* Font Size Dropdown */}
            <DropdownMenu>
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <DropdownMenuTrigger asChild>
                                <Button type="button" variant="ghost" size="sm" className="h-8 px-2 gap-1">
                                    <Type className="h-4 w-4" />
                                    <span className="text-xs hidden sm:inline">Size</span>
                                </Button>
                            </DropdownMenuTrigger>
                        </TooltipTrigger>
                        <TooltipContent side="bottom" className="text-xs">
                            Font Size
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
                <DropdownMenuContent>
                    {fontSizes.map((size) => (
                        <DropdownMenuItem
                            key={size.value}
                            onClick={() => editor.chain().focus().setFontSize(size.value).run()}
                            className="cursor-pointer"
                        >
                            <span style={{ fontSize: size.value }}>{size.label}</span>
                        </DropdownMenuItem>
                    ))}
                    <DropdownMenuItem
                        onClick={() => editor.chain().focus().unsetFontSize().run()}
                        className="cursor-pointer text-slate-500"
                    >
                        Reset Size
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            <Separator orientation="vertical" className="mx-1 h-6" />

            {/* Headings */}
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                isActive={editor.isActive("heading", { level: 1 })}
                tooltip="Heading 1"
            >
                <Heading1 className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                isActive={editor.isActive("heading", { level: 2 })}
                tooltip="Heading 2"
            >
                <Heading2 className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
                isActive={editor.isActive("heading", { level: 3 })}
                tooltip="Heading 3"
            >
                <Heading3 className="h-4 w-4" />
            </ToolbarButton>

            <Separator orientation="vertical" className="mx-1 h-6" />

            {/* Text formatting */}
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleBold().run()}
                isActive={editor.isActive("bold")}
                tooltip="Bold (Ctrl+B)"
            >
                <Bold className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleItalic().run()}
                isActive={editor.isActive("italic")}
                tooltip="Italic (Ctrl+I)"
            >
                <Italic className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleUnderline().run()}
                isActive={editor.isActive("underline")}
                tooltip="Underline (Ctrl+U)"
            >
                <UnderlineIcon className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleStrike().run()}
                isActive={editor.isActive("strike")}
                tooltip="Strikethrough"
            >
                <Strikethrough className="h-4 w-4" />
            </ToolbarButton>

            <Separator orientation="vertical" className="mx-1 h-6" />

            {/* Lists */}
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleBulletList().run()}
                isActive={editor.isActive("bulletList")}
                tooltip="Bullet List"
            >
                <List className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleOrderedList().run()}
                isActive={editor.isActive("orderedList")}
                tooltip="Numbered List"
            >
                <ListOrdered className="h-4 w-4" />
            </ToolbarButton>

            <Separator orientation="vertical" className="mx-1 h-6" />

            {/* Alignment */}
            <ToolbarButton
                onClick={() => editor.chain().focus().setTextAlign("left").run()}
                isActive={editor.isActive({ textAlign: "left" })}
                tooltip="Align Left"
            >
                <AlignLeft className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={() => editor.chain().focus().setTextAlign("center").run()}
                isActive={editor.isActive({ textAlign: "center" })}
                tooltip="Align Center"
            >
                <AlignCenter className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={() => editor.chain().focus().setTextAlign("right").run()}
                isActive={editor.isActive({ textAlign: "right" })}
                tooltip="Align Right"
            >
                <AlignRight className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={() => editor.chain().focus().setTextAlign("justify").run()}
                isActive={editor.isActive({ textAlign: "justify" })}
                tooltip="Justify"
            >
                <AlignJustify className="h-4 w-4" />
            </ToolbarButton>

            <Separator orientation="vertical" className="mx-1 h-6" />

            {/* Other */}
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleBlockquote().run()}
                isActive={editor.isActive("blockquote")}
                tooltip="Quote"
            >
                <Quote className="h-4 w-4" />
            </ToolbarButton>
            <ToolbarButton
                onClick={setLink}
                isActive={editor.isActive("link")}
                tooltip="Add Link"
            >
                <LinkIcon className="h-4 w-4" />
            </ToolbarButton>
            {editor.isActive("link") && (
                <ToolbarButton
                    onClick={removeLink}
                    tooltip="Remove Link"
                >
                    <Unlink className="h-4 w-4" />
                </ToolbarButton>
            )}
            <ToolbarButton
                onClick={() => editor.chain().focus().setHorizontalRule().run()}
                tooltip="Horizontal Line"
            >
                <Minus className="h-4 w-4" />
            </ToolbarButton>
        </div>
    )
}


export function RichTextEditor({
    content,
    onChange,
    placeholder = "Start typing...",
    className,
    minHeight = "200px",
}: RichTextEditorProps) {
    const editor = useEditor({
        immediatelyRender: false,
        extensions: [
            StarterKit.configure({
                heading: {
                    levels: [1, 2, 3],
                },
            }),
            Underline,
            TextStyle,
            FontSize,
            TextAlign.configure({
                types: ["heading", "paragraph"],
            }),
            Link.configure({
                openOnClick: false,
                HTMLAttributes: {
                    class: "text-blue-600 underline hover:text-blue-800",
                },
            }),
            Placeholder.configure({
                placeholder,
            }),
        ],
        content,
        editorProps: {
            attributes: {
                class: cn(
                    "prose prose-sm dark:prose-invert max-w-none focus:outline-none min-h-[150px]",
                    "prose-headings:font-semibold prose-headings:text-gray-900 dark:prose-headings:text-white",
                    "prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:my-2",
                    "prose-ul:list-disc prose-ol:list-decimal prose-li:my-0",
                    "prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-4 prose-blockquote:italic"
                ),
            },
        },
        onUpdate: ({ editor }) => {
            onChange(editor.getHTML())
        },
    })

    useEffect(() => {
        if (editor && content !== editor.getHTML()) {
            editor.commands.setContent(content)
        }
    }, [content, editor])

    return (
        <div className={cn("border rounded-lg overflow-hidden bg-white dark:bg-gray-950", className)}>
            <Toolbar editor={editor} />
            <div
                className="p-4 overflow-y-auto"
                style={{ minHeight }}
            >
                <EditorContent editor={editor} className="min-h-full" />
            </div>
        </div>
    )
}

// Read-only viewer for displaying rich text content
export function RichTextViewer({
    content,
    className,
}: {
    content: string
    className?: string
}) {
    return (
        <div
            className={cn(
                "prose prose-sm dark:prose-invert max-w-none",
                "prose-headings:font-semibold prose-headings:text-gray-900 dark:prose-headings:text-white",
                "prose-p:text-gray-700 dark:prose-p:text-gray-300",
                "prose-ul:list-disc prose-ol:list-decimal",
                "prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-4 prose-blockquote:italic",
                className
            )}
            dangerouslySetInnerHTML={{ __html: content }}
        />
    )
}
