"""AI Service for blog content generation using OpenRouter."""

import httpx
import json
import re
from typing import Optional
from uuid import uuid4

from app.core.config import settings


# Category-specific prompts for better content
CATEGORY_PROMPTS = {
    "Growth": "Focus on YouTube channel growth strategies, subscriber acquisition, audience engagement tactics, and viral content creation tips.",
    "Tutorial": "Create step-by-step guides, how-to content, and practical tutorials for YouTube creators.",
    "Analytics": "Cover YouTube analytics, metrics interpretation, data-driven decisions, and performance optimization.",
    "SEO": "Focus on YouTube SEO, video optimization, keyword research, and discoverability strategies.",
    "Monetization": "Cover YouTube monetization, revenue streams, sponsorships, and income optimization for creators.",
    "Community": "Focus on community building, audience engagement, comments management, and creator-viewer relationships.",
    "News": "Cover latest YouTube updates, platform changes, algorithm updates, and industry news.",
    "Updates": "Share product updates, new features, and announcements related to YouTube automation tools.",
}


class AIBlogService:
    """Service for AI-powered blog content generation."""

    def __init__(self):
        self.openrouter_api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.site_url = settings.OPENROUTER_SITE_URL
        self.site_name = settings.OPENROUTER_SITE_NAME

    async def generate_blog_content(
        self,
        topic: str,
        category: str,
        language: str = "en",
    ) -> dict:
        """
        Generate blog content using OpenRouter API.
        
        Returns dict with: title, slug, excerpt, content, tags, meta_title, meta_description, read_time_minutes
        """
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured")

        category_context = CATEGORY_PROMPTS.get(category, "")
        
        # Language instruction
        lang_instruction = ""
        if language == "id":
            lang_instruction = "Write the entire blog post in Indonesian (Bahasa Indonesia)."
        elif language == "en":
            lang_instruction = "Write the entire blog post in English."
        else:
            lang_instruction = f"Write the entire blog post in {language}."

        system_prompt = f"""You are an expert content writer for a YouTube automation platform blog.
{category_context}
{lang_instruction}

Generate a comprehensive, engaging blog post. Return ONLY valid JSON with this exact structure:
{{
    "title": "Catchy, SEO-friendly title (50-60 chars)",
    "slug": "url-friendly-slug-with-dashes",
    "excerpt": "Compelling summary in 2-3 sentences (150-160 chars)",
    "content": "Full HTML blog content with <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em> tags. Include introduction, 3-5 main sections, and conclusion. Minimum 800 words.",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
    "meta_title": "SEO meta title (50-60 chars)",
    "meta_description": "SEO meta description (150-160 chars)",
    "read_time_minutes": 5
}}

Important:
- Content must be original, informative, and actionable
- Use proper HTML formatting for the content field
- Include practical tips and examples
- Make it engaging and easy to read
- Estimate read time based on ~200 words per minute"""

        user_prompt = f"Write a blog post about: {topic}\nCategory: {category}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "HTTP-Referer": self.site_url or "http://localhost:3000",
                    "X-Title": self.site_name,
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4000,
                },
            )

            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"OpenRouter API error: {response.status_code} - {error_text}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Parse JSON from response (handle markdown code blocks)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError(f"Failed to parse AI response as JSON: {content[:500]}")

            # Validate required fields
            required_fields = ["title", "slug", "content"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # Set defaults for optional fields
            result.setdefault("excerpt", result["title"])
            result.setdefault("tags", [category.lower()])
            result.setdefault("meta_title", result["title"])
            result.setdefault("meta_description", result.get("excerpt", ""))
            result.setdefault("read_time_minutes", 5)

            return result

    async def generate_thumbnail_prompt(
        self,
        title: str,
        excerpt: str,
        category: str,
    ) -> str:
        """
        Use AI to generate a creative, specific thumbnail prompt based on article content.
        This creates much better thumbnails than generic prompts.
        """
        if not self.openrouter_api_key:
            # Fallback to basic prompt if no API key
            return self._get_fallback_thumbnail_prompt(title, category)
        
        system_prompt = """You are an expert thumbnail designer for YouTube and tech blogs.
Your job is to create a detailed DALL-E 3 prompt for generating a professional blog thumbnail.

Rules for the prompt you create:
1. NO TEXT or letters in the image - DALL-E struggles with text
2. Use specific visual metaphors related to the article topic
3. Specify exact colors (use hex codes or specific color names)
4. Include 3D elements, gradients, or depth for modern look
5. Mention lighting direction and style
6. Keep background clean (gradient or solid, not busy)
7. YouTube thumbnail style: bold, high contrast, eye-catching
8. Size: 1792x1024 (16:9 landscape)
9. Style: Modern digital illustration, not photorealistic

Return ONLY the prompt text, nothing else. No explanations."""

        user_prompt = f"""Create a DALL-E 3 prompt for a blog thumbnail:

Title: {title}
Summary: {excerpt}
Category: {category}

Generate a creative, specific prompt that captures the essence of this article visually."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "HTTP-Referer": self.site_url or "http://localhost:3000",
                        "X-Title": self.site_name,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.8,
                        "max_tokens": 500,
                    },
                )
                
                if response.status_code == 200:
                    data = response.json()
                    prompt = data["choices"][0]["message"]["content"].strip()
                    # Clean up any markdown or quotes
                    prompt = prompt.strip('"\'`')
                    if prompt.startswith("```"):
                        prompt = prompt.split("```")[1] if "```" in prompt[3:] else prompt[3:]
                    return prompt.strip()
        except Exception as e:
            print(f"Error generating thumbnail prompt: {e}")
        
        # Fallback
        return self._get_fallback_thumbnail_prompt(title, category)
    
    def _get_fallback_thumbnail_prompt(self, title: str, category: str) -> str:
        """Fallback prompt when AI prompt generation fails."""
        category_visuals = {
            "Growth": "A 3D rocket ship launching upward from a YouTube play button, trailing golden particles. Background: deep purple to blue gradient. Glowing green upward arrows surrounding the rocket. Dramatic lighting from below.",
            "Tutorial": "An open glowing book with 3D step icons (1, 2, 3) floating above it in a spiral. YouTube play button integrated into the design. Background: clean white to light blue gradient. Soft studio lighting.",
            "Analytics": "A 3D holographic dashboard with glowing bar charts and pie charts floating in space. YouTube logo subtly integrated. Background: dark blue with cyan grid lines. Neon glow effect on data points.",
            "SEO": "A giant 3D magnifying glass revealing a glowing YouTube play button, with search result cards floating around. Background: orange to teal gradient. Golden light rays emanating from the center.",
            "Monetization": "3D golden coins and dollar bills floating around a YouTube play button that's transforming into a treasure chest. Background: deep green to gold gradient. Sparkle effects.",
            "Community": "Multiple 3D avatar icons connected by glowing lines forming a network, centered around a heart-shaped YouTube logo. Background: warm purple to orange gradient. Soft, friendly lighting.",
            "News": "A 3D breaking news banner with a pulsing YouTube notification bell. Lightning bolt effects. Background: bold red to dark red gradient. Dramatic spotlight lighting.",
            "Updates": "A 3D gift box opening with sparkles and a 'NEW' badge floating above a YouTube play button. Background: fresh cyan to blue gradient. Celebratory particle effects.",
        }
        
        base_visual = category_visuals.get(category, 
            "A modern 3D YouTube play button with glowing edges, floating above a gradient background. Subtle tech circuit patterns. Professional lighting.")
        
        return f"""{base_visual}

Additional context from title "{title}":
- Modern digital illustration style
- No text or letters
- High contrast, bold colors
- Clean composition with space for text overlay
- Professional tech blog aesthetic
- 1792x1024 landscape format"""

    async def generate_thumbnail(
        self,
        title: str,
        category: str,
        excerpt: str = "",
    ) -> Optional[str]:
        """
        Generate blog thumbnail using OpenAI DALL-E 3.
        
        Uses carefully crafted prompts based on category and title
        to generate professional YouTube-style thumbnails.
        
        Returns the storage key of the uploaded image.
        """
        from app.core.storage import get_storage
        import io
        
        # Check if OpenAI API key is available
        if not settings.OPENAI_API_KEY:
            print("OPENAI_API_KEY not configured, skipping thumbnail generation")
            return None
        
        # Use direct, well-crafted prompt instead of AI-generated prompt
        prompt = self._build_thumbnail_prompt(title, category)
        print(f"Thumbnail prompt: {prompt[:300]}...")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": "1792x1024",
                        "quality": "standard",
                        "response_format": "url",
                    },
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"DALL-E API error: {response.status_code} - {error_text}")
                    return None
                
                data = response.json()
                image_url = data["data"][0]["url"]
                
                # Download the generated image
                image_response = await client.get(image_url)
                if image_response.status_code != 200:
                    print(f"Failed to download generated image: {image_response.status_code}")
                    return None
                
                image_data = image_response.content
                
                # Upload to storage
                filename = f"blog/{uuid4()}.png"
                
                storage = get_storage()
                result = storage.upload_fileobj(
                    io.BytesIO(image_data),
                    filename,
                    content_type="image/png",
                )
                
                if not result.success:
                    print(f"Failed to upload thumbnail: {result.error_message}")
                    return None
                
                return filename
                
        except Exception as e:
            print(f"Error generating thumbnail with DALL-E: {e}")
            return None

    def _build_thumbnail_prompt(self, title: str, category: str) -> str:
        """
        Build a professional DALL-E prompt for YouTube-style blog thumbnail.
        
        Based on proven thumbnail design principles:
        - Bold, high contrast colors
        - 3D elements for depth
        - Clean background (gradient)
        - No text (will be added separately)
        - YouTube/tech aesthetic
        """
        # Category-specific visual elements
        category_designs = {
            "Growth": {
                "main_element": "a 3D rocket ship launching upward with flame trail",
                "secondary": "glowing green upward arrows and a YouTube play button",
                "colors": "deep purple (#6B21A8) to electric blue (#0EA5E9) gradient background",
                "accent": "golden yellow (#FBBF24) particle effects",
            },
            "Tutorial": {
                "main_element": "a 3D open book with glowing pages and floating step numbers (1, 2, 3)",
                "secondary": "a YouTube play button integrated into the book design",
                "colors": "clean white to sky blue (#0EA5E9) gradient background",
                "accent": "soft orange (#F97316) highlights on the steps",
            },
            "Analytics": {
                "main_element": "a 3D holographic dashboard with floating bar charts and line graphs",
                "secondary": "glowing data points and a subtle YouTube logo",
                "colors": "dark navy (#1E3A5F) to purple (#7C3AED) gradient background",
                "accent": "cyan (#06B6D4) neon glow on data elements",
            },
            "SEO": {
                "main_element": "a giant 3D magnifying glass with search icon",
                "secondary": "YouTube play button being revealed, floating keywords tags",
                "colors": "orange (#F97316) to teal (#14B8A6) gradient background",
                "accent": "golden (#FBBF24) light rays from the magnifying glass",
            },
            "Monetization": {
                "main_element": "3D golden coins and dollar symbols floating upward",
                "secondary": "a YouTube play button transforming into a treasure chest",
                "colors": "deep emerald green (#047857) to gold (#D97706) gradient background",
                "accent": "sparkle and shine effects on coins",
            },
            "Community": {
                "main_element": "multiple 3D avatar icons connected by glowing network lines",
                "secondary": "a heart-shaped YouTube logo at the center",
                "colors": "warm purple (#9333EA) to coral orange (#F97316) gradient background",
                "accent": "soft white glow on connection lines",
            },
            "News": {
                "main_element": "a 3D breaking news banner with alert icon",
                "secondary": "YouTube notification bell with pulse effect",
                "colors": "bold red (#DC2626) to dark red (#7F1D1D) gradient background",
                "accent": "white (#FFFFFF) spotlight effect",
            },
            "Updates": {
                "main_element": "a 3D gift box opening with sparkles flying out",
                "secondary": "a 'NEW' badge and YouTube play button",
                "colors": "fresh cyan (#06B6D4) to blue (#3B82F6) gradient background",
                "accent": "golden (#FBBF24) sparkle particles",
            },
        }
        
        # Get design for category or use default
        design = category_designs.get(category, {
            "main_element": "a modern 3D YouTube play button with glowing edges",
            "secondary": "floating tech elements and circuit patterns",
            "colors": "purple (#7C3AED) to blue (#3B82F6) gradient background",
            "accent": "white glow effects",
        })
        
        # Build the prompt
        prompt = f"""Create a professional YouTube-style blog thumbnail image.

MAIN VISUAL: {design['main_element']}
SECONDARY ELEMENTS: {design['secondary']}
BACKGROUND: {design['colors']}
ACCENT EFFECTS: {design['accent']}

STYLE REQUIREMENTS:
- Modern 3D digital illustration style (NOT photorealistic, NOT cartoon)
- High contrast, bold and vibrant colors
- Clean composition with the main element centered or slightly off-center
- Leave empty space in top-left or top-right corner for text overlay
- Dramatic lighting with soft shadows
- Glossy, polished look on 3D elements
- NO TEXT, NO LETTERS, NO WORDS, NO NUMBERS in the image
- NO human faces or people
- Professional tech blog aesthetic
- 16:9 landscape format (1792x1024)

CONTEXT: This thumbnail is for a blog article titled "{title}" in the {category} category.
The image should visually represent growth, success, and YouTube content creation."""

        return prompt

    async def generate_blog_with_thumbnail(
        self,
        topic: str,
        category: str,
        language: str = "en",
        generate_image: bool = True,
    ) -> dict:
        """
        Generate complete blog post with optional thumbnail.
        
        Returns dict with all blog fields including featured_image if generated.
        """
        # Generate blog content
        blog_data = await self.generate_blog_content(topic, category, language)
        
        # Generate thumbnail if requested
        if generate_image:
            thumbnail_key = await self.generate_thumbnail(
                title=blog_data["title"],
                category=category,
                excerpt=blog_data.get("excerpt", ""),  # Pass excerpt for better prompt
            )
            if thumbnail_key:
                blog_data["featured_image"] = thumbnail_key
        
        return blog_data


# Singleton instance
ai_blog_service = AIBlogService()
