"use client"

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

// YouTube Video Categories
// https://developers.google.com/youtube/v3/docs/videoCategories/list
export const YOUTUBE_CATEGORIES = [
    { id: "1", name: "Film & Animation" },
    { id: "2", name: "Autos & Vehicles" },
    { id: "10", name: "Music" },
    { id: "15", name: "Pets & Animals" },
    { id: "17", name: "Sports" },
    { id: "18", name: "Short Movies" },
    { id: "19", name: "Travel & Events" },
    { id: "20", name: "Gaming" },
    { id: "21", name: "Videoblogging" },
    { id: "22", name: "People & Blogs" },
    { id: "23", name: "Comedy" },
    { id: "24", name: "Entertainment" },
    { id: "25", name: "News & Politics" },
    { id: "26", name: "Howto & Style" },
    { id: "27", name: "Education" },
    { id: "28", name: "Science & Technology" },
    { id: "29", name: "Nonprofits & Activism" },
    { id: "30", name: "Movies" },
    { id: "31", name: "Anime/Animation" },
    { id: "32", name: "Action/Adventure" },
    { id: "33", name: "Classics" },
    { id: "34", name: "Comedy" },
    { id: "35", name: "Documentary" },
    { id: "36", name: "Drama" },
    { id: "37", name: "Family" },
    { id: "38", name: "Foreign" },
    { id: "39", name: "Horror" },
    { id: "40", name: "Sci-Fi/Fantasy" },
    { id: "41", name: "Thriller" },
    { id: "42", name: "Shorts" },
    { id: "43", name: "Shows" },
    { id: "44", name: "Trailers" },
]

// Most commonly used categories
export const COMMON_CATEGORIES = [
    { id: "22", name: "People & Blogs" },
    { id: "24", name: "Entertainment" },
    { id: "20", name: "Gaming" },
    { id: "28", name: "Science & Technology" },
    { id: "27", name: "Education" },
    { id: "26", name: "Howto & Style" },
    { id: "10", name: "Music" },
    { id: "17", name: "Sports" },
    { id: "1", name: "Film & Animation" },
    { id: "23", name: "Comedy" },
]

interface CategorySelectProps {
    value?: string
    onValueChange: (value: string) => void
    showAllCategories?: boolean
    disabled?: boolean
}

export function CategorySelect({
    value,
    onValueChange,
    showAllCategories = false,
    disabled = false,
}: CategorySelectProps) {
    const categories = showAllCategories ? YOUTUBE_CATEGORIES : COMMON_CATEGORIES

    return (
        <Select value={value} onValueChange={onValueChange} disabled={disabled}>
            <SelectTrigger>
                <SelectValue placeholder="Select a category" />
            </SelectTrigger>
            <SelectContent>
                {categories.map((category) => (
                    <SelectItem key={category.id} value={category.id}>
                        {category.name}
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    )
}

export function getCategoryName(categoryId: string): string {
    const category = YOUTUBE_CATEGORIES.find(c => c.id === categoryId)
    return category?.name || "Unknown"
}

export default CategorySelect
