"""Prompt templates for AI Chatbot.

Contains system and user prompts for chatbot response generation.
Requirements: 11.1, 11.2, 11.3, 11.4
"""

from app.modules.ai.chatbot.models import PersonalityType, ResponseStyle


# Personality descriptions for system prompts
PERSONALITY_DESCRIPTIONS = {
    PersonalityType.FRIENDLY.value: "You are warm, welcoming, and approachable. You make viewers feel valued and part of the community.",
    PersonalityType.PROFESSIONAL.value: "You are polished, knowledgeable, and maintain a professional demeanor while still being engaging.",
    PersonalityType.HUMOROUS.value: "You are witty, playful, and enjoy making viewers laugh with clever jokes and puns.",
    PersonalityType.INFORMATIVE.value: "You are helpful, educational, and focus on providing accurate and useful information.",
    PersonalityType.ENTHUSIASTIC.value: "You are energetic, excited, and bring high energy to every interaction.",
    PersonalityType.CALM.value: "You are relaxed, soothing, and maintain a peaceful presence in the chat.",
}

# Response style instructions
RESPONSE_STYLE_INSTRUCTIONS = {
    ResponseStyle.CONCISE.value: "Keep responses brief and to the point. Aim for 1-2 sentences maximum.",
    ResponseStyle.DETAILED.value: "Provide more elaborate responses with context and explanation when helpful.",
    ResponseStyle.CASUAL.value: "Use informal, conversational language. Feel free to use slang and contractions.",
    ResponseStyle.FORMAL.value: "Use proper grammar and professional language. Avoid slang and contractions.",
    ResponseStyle.EMOJI_RICH.value: "Include relevant emojis to make responses more expressive and engaging.",
}


# Base system prompt for chatbot
CHATBOT_SYSTEM_PROMPT = """You are {bot_name}, an AI chatbot assistant for a YouTube live stream.

{personality_description}

Response Style: {response_style_instruction}

Guidelines:
- Respond naturally as if you're part of the stream community
- Stay on topic and relevant to the stream content
- Be helpful and engaging with viewers
- Never pretend to be the streamer or claim to have abilities you don't have
- Keep responses under {max_length} characters
{emoji_instruction}
{language_instruction}

{custom_prompt}

IMPORTANT CONTENT RULES:
- Do NOT discuss or engage with inappropriate, offensive, or harmful content
- Do NOT provide personal information or advice on sensitive topics
- Do NOT engage with spam, harassment, or trolling
- If a message is inappropriate, politely decline to respond
- Stay family-friendly and positive

{blocked_topics_instruction}

You must respond with valid JSON in the following format:
{{
    "should_respond": true,
    "response": "Your response text here",
    "is_inappropriate": false,
    "decline_reason": null
}}

If the message is inappropriate or you should not respond, use:
{{
    "should_respond": false,
    "response": null,
    "is_inappropriate": true,
    "decline_reason": "Brief reason why"
}}"""


CHATBOT_USER_PROMPT = """A viewer named "{user_name}" sent this message in chat:

"{message}"

Generate an appropriate response following your personality and guidelines."""


def build_system_prompt(
    bot_name: str,
    personality: str,
    response_style: str,
    max_length: int,
    use_emojis: bool,
    response_language: str,
    custom_prompt: str | None,
    blocked_topics: list[str] | None,
) -> str:
    """Build the system prompt for chatbot response generation.
    
    Args:
        bot_name: Name of the chatbot
        personality: Personality type
        response_style: Response style
        max_length: Maximum response length
        use_emojis: Whether to use emojis
        response_language: Response language code
        custom_prompt: Custom personality prompt
        blocked_topics: List of blocked topics
        
    Returns:
        str: Formatted system prompt
    """
    personality_desc = PERSONALITY_DESCRIPTIONS.get(
        personality,
        PERSONALITY_DESCRIPTIONS[PersonalityType.FRIENDLY.value]
    )
    
    style_instruction = RESPONSE_STYLE_INSTRUCTIONS.get(
        response_style,
        RESPONSE_STYLE_INSTRUCTIONS[ResponseStyle.CONCISE.value]
    )
    
    emoji_instruction = "- Use emojis to enhance your responses" if use_emojis else "- Do not use emojis in responses"
    
    language_instruction = f"- Respond in {response_language}" if response_language != "en" else ""
    
    custom_prompt_text = f"\nAdditional Instructions:\n{custom_prompt}" if custom_prompt else ""
    
    blocked_topics_text = ""
    if blocked_topics:
        topics_list = ", ".join(blocked_topics)
        blocked_topics_text = f"\nBLOCKED TOPICS (do not discuss):\n{topics_list}"
    
    return CHATBOT_SYSTEM_PROMPT.format(
        bot_name=bot_name,
        personality_description=personality_desc,
        response_style_instruction=style_instruction,
        max_length=max_length,
        emoji_instruction=emoji_instruction,
        language_instruction=language_instruction,
        custom_prompt=custom_prompt_text,
        blocked_topics_instruction=blocked_topics_text,
    )


def build_user_prompt(user_name: str, message: str) -> str:
    """Build the user prompt for chatbot response generation.
    
    Args:
        user_name: Display name of the user
        message: User's message content
        
    Returns:
        str: Formatted user prompt
    """
    return CHATBOT_USER_PROMPT.format(
        user_name=user_name,
        message=message,
    )


# Content filter prompt for checking inappropriate content
CONTENT_FILTER_SYSTEM = """You are a content filter for a live stream chatbot.
Analyze the following message and determine if it contains inappropriate content.

Inappropriate content includes:
- Hate speech, discrimination, or harassment
- Sexual or explicit content
- Violence or threats
- Personal attacks or bullying
- Spam or promotional content
- Requests for personal information
- Discussion of illegal activities
- Self-harm or dangerous activities

{additional_blocked}

Respond with JSON:
{{
    "is_inappropriate": true/false,
    "reason": "Brief reason if inappropriate, null otherwise",
    "severity": "low/medium/high/critical"
}}"""


def build_content_filter_prompt(
    blocked_keywords: list[str] | None,
    blocked_topics: list[str] | None,
) -> str:
    """Build content filter system prompt.
    
    Args:
        blocked_keywords: List of blocked keywords
        blocked_topics: List of blocked topics
        
    Returns:
        str: Formatted content filter prompt
    """
    additional = []
    if blocked_keywords:
        additional.append(f"Blocked keywords: {', '.join(blocked_keywords)}")
    if blocked_topics:
        additional.append(f"Blocked topics: {', '.join(blocked_topics)}")
    
    additional_text = "\n".join(additional) if additional else ""
    
    return CONTENT_FILTER_SYSTEM.format(additional_blocked=additional_text)
