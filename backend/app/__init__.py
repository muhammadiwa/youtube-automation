"""YouTube Automation Backend Application.

A SaaS platform for managing multiple YouTube accounts, automating live streaming,
and leveraging AI for content optimization.

Modules:
    - core: Configuration, database, Redis, Celery setup
    - modules.auth: User authentication and security
    - modules.account: YouTube account OAuth integration
    - modules.video: Video upload and metadata management
    - modules.stream: Live streaming automation
    - modules.ai: AI-powered content optimization
    - modules.analytics: Metrics and reporting
    - modules.moderation: Chat and comment moderation
    - modules.notification: Multi-channel alerts
    - modules.billing: Subscription and usage metering
    - modules.agent: Worker/agent management
    - modules.job: Background job processing
"""

__version__ = "0.1.0"
