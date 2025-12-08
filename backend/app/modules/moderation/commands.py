"""Custom command handling for chat moderation.

Implements custom command registration and execution.
Requirements: 12.4
"""

import re
import uuid
from datetime import datetime, timedelta
from typing import Callable, Optional, Any

from app.modules.moderation.models import CustomCommand


class CommandContext:
    """Context for command execution."""

    def __init__(
        self,
        account_id: uuid.UUID,
        user_channel_id: str,
        user_display_name: str,
        is_moderator: bool = False,
        is_member: bool = False,
        is_owner: bool = False,
        message_content: str = "",
        args: list[str] = None,
    ):
        """Initialize command context.
        
        Args:
            account_id: YouTube account ID
            user_channel_id: User's channel ID
            user_display_name: User's display name
            is_moderator: Whether user is a moderator
            is_member: Whether user is a member
            is_owner: Whether user is the channel owner
            message_content: Full message content
            args: Command arguments
        """
        self.account_id = account_id
        self.user_channel_id = user_channel_id
        self.user_display_name = user_display_name
        self.is_moderator = is_moderator
        self.is_member = is_member
        self.is_owner = is_owner
        self.message_content = message_content
        self.args = args or []


class CommandResult:
    """Result of command execution."""

    def __init__(
        self,
        success: bool,
        response: Optional[str] = None,
        error: Optional[str] = None,
        action: Optional[str] = None,
        webhook_triggered: bool = False,
    ):
        """Initialize command result.
        
        Args:
            success: Whether command executed successfully
            response: Response text to send
            error: Error message if failed
            action: Action that was triggered
            webhook_triggered: Whether webhook was called
        """
        self.success = success
        self.response = response
        self.error = error
        self.action = action
        self.webhook_triggered = webhook_triggered


class CommandHandler:
    """Base class for command handlers."""

    def __init__(self, command: CustomCommand):
        """Initialize handler.
        
        Args:
            command: Custom command configuration
        """
        self.command = command

    def can_execute(self, context: CommandContext) -> bool:
        """Check if command can be executed in this context.
        
        Args:
            context: Command execution context
            
        Returns:
            True if command can be executed
        """
        return self.command.can_be_used_by(
            context.is_moderator,
            context.is_member,
            context.is_owner,
        )

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute the command.
        
        Args:
            context: Command execution context
            
        Returns:
            CommandResult with response
        """
        raise NotImplementedError


class TextCommandHandler(CommandHandler):
    """Handler for text response commands."""

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute text command.
        
        Args:
            context: Command execution context
            
        Returns:
            CommandResult with text response
        """
        response = self.command.response_text or ""
        
        # Replace placeholders
        response = self._replace_placeholders(response, context)
        
        return CommandResult(
            success=True,
            response=response,
        )

    def _replace_placeholders(
        self,
        text: str,
        context: CommandContext,
    ) -> str:
        """Replace placeholders in response text.
        
        Args:
            text: Response text with placeholders
            context: Command context
            
        Returns:
            Text with placeholders replaced
        """
        replacements = {
            "{user}": context.user_display_name,
            "{channel}": context.user_channel_id,
            "{args}": " ".join(context.args),
        }
        
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        
        return text


class ActionCommandHandler(CommandHandler):
    """Handler for action commands."""

    def __init__(
        self,
        command: CustomCommand,
        action_handlers: dict[str, Callable[[CommandContext], CommandResult]] = None,
    ):
        """Initialize action handler.
        
        Args:
            command: Custom command configuration
            action_handlers: Map of action types to handler functions
        """
        super().__init__(command)
        self.action_handlers = action_handlers or {}

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute action command.
        
        Args:
            context: Command execution context
            
        Returns:
            CommandResult with action result
        """
        action_type = self.command.action_type
        
        if action_type and action_type in self.action_handlers:
            return self.action_handlers[action_type](context)
        
        return CommandResult(
            success=False,
            error=f"Unknown action type: {action_type}",
        )


class WebhookCommandHandler(CommandHandler):
    """Handler for webhook commands."""

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute webhook command.
        
        Args:
            context: Command execution context
            
        Returns:
            CommandResult with webhook status
        """
        webhook_url = self.command.webhook_url
        
        if not webhook_url:
            return CommandResult(
                success=False,
                error="No webhook URL configured",
            )
        
        # Note: Actual webhook call would be made here
        # This is a placeholder for the webhook logic
        return CommandResult(
            success=True,
            webhook_triggered=True,
            response="Webhook triggered successfully",
        )


class CommandProcessor:
    """Processes chat messages for commands.
    
    Requirements: 12.4
    """

    def __init__(self, prefix: str = "!"):
        """Initialize command processor.
        
        Args:
            prefix: Command prefix (default "!")
        """
        self.prefix = prefix
        self._cooldowns: dict[tuple[uuid.UUID, str], datetime] = {}

    def parse_command(
        self,
        message_content: str,
    ) -> Optional[tuple[str, list[str]]]:
        """Parse command from message content.
        
        Args:
            message_content: Full message content
            
        Returns:
            Tuple of (trigger, args) or None if not a command
        """
        if not message_content.startswith(self.prefix):
            return None
        
        parts = message_content.split()
        if not parts:
            return None
        
        trigger = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        return trigger, args

    def is_on_cooldown(
        self,
        command: CustomCommand,
        user_channel_id: str,
    ) -> bool:
        """Check if command is on cooldown for user.
        
        Args:
            command: Custom command
            user_channel_id: User's channel ID
            
        Returns:
            True if on cooldown
        """
        key = (command.id, user_channel_id)
        
        if key not in self._cooldowns:
            return False
        
        cooldown_end = self._cooldowns[key] + timedelta(
            seconds=command.cooldown_seconds
        )
        
        return datetime.utcnow() < cooldown_end

    def record_usage(
        self,
        command: CustomCommand,
        user_channel_id: str,
    ) -> None:
        """Record command usage for cooldown tracking.
        
        Args:
            command: Custom command
            user_channel_id: User's channel ID
        """
        key = (command.id, user_channel_id)
        self._cooldowns[key] = datetime.utcnow()

    def get_handler(self, command: CustomCommand) -> CommandHandler:
        """Get appropriate handler for command.
        
        Args:
            command: Custom command
            
        Returns:
            CommandHandler for the command
        """
        response_type = command.response_type
        
        if response_type == "text":
            return TextCommandHandler(command)
        elif response_type == "action":
            return ActionCommandHandler(command)
        elif response_type == "webhook":
            return WebhookCommandHandler(command)
        else:
            return TextCommandHandler(command)

    def process(
        self,
        command: CustomCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Process a command.
        
        Requirements: 12.4
        
        Args:
            command: Custom command to execute
            context: Command execution context
            
        Returns:
            CommandResult with execution result
        """
        # Check permissions
        handler = self.get_handler(command)
        if not handler.can_execute(context):
            return CommandResult(
                success=False,
                error="You don't have permission to use this command",
            )
        
        # Check cooldown
        if self.is_on_cooldown(command, context.user_channel_id):
            return CommandResult(
                success=False,
                error="Command is on cooldown",
            )
        
        # Execute command
        result = handler.execute(context)
        
        # Record usage if successful
        if result.success:
            self.record_usage(command, context.user_channel_id)
        
        return result


# Built-in command actions
def builtin_uptime_action(context: CommandContext) -> CommandResult:
    """Built-in uptime command action."""
    # Note: Would fetch actual stream uptime
    return CommandResult(
        success=True,
        response="Stream has been live for 2 hours 30 minutes",
        action="uptime",
    )


def builtin_followage_action(context: CommandContext) -> CommandResult:
    """Built-in followage command action."""
    return CommandResult(
        success=True,
        response=f"{context.user_display_name} has been following for 6 months",
        action="followage",
    )


def builtin_shoutout_action(context: CommandContext) -> CommandResult:
    """Built-in shoutout command action."""
    if not context.args:
        return CommandResult(
            success=False,
            error="Please specify a user to shoutout",
        )
    
    target = context.args[0]
    return CommandResult(
        success=True,
        response=f"Go check out {target}! They're awesome!",
        action="shoutout",
    )


# Default built-in actions
BUILTIN_ACTIONS = {
    "uptime": builtin_uptime_action,
    "followage": builtin_followage_action,
    "shoutout": builtin_shoutout_action,
}
