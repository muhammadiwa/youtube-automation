# YouTube Automation Frontend

Next.js frontend for the YouTube Automation platform. This application includes public marketing pages, authentication flows, user dashboards, admin dashboards, internal docs, billing flows, realtime support, video management, and streaming operations.

## Overview

Main stack:

- Next.js 14 App Router
- React 18
- TypeScript
- Tailwind CSS
- Radix UI
- Framer Motion
- Recharts
- Vitest

Important files:

- [package.json](/d:/Project/youtube-automation/frontend/package.json:1)
- [src/app/layout.tsx](/d:/Project/youtube-automation/frontend/src/app/layout.tsx:1)
- [src/middleware.ts](/d:/Project/youtube-automation/frontend/src/middleware.ts:1)

## Application Areas

### Public pages

- `/`
- `/about`
- `/contact`
- `/careers`
- `/privacy`
- `/terms`
- `/blog`

### Auth area

- `/login`
- `/register`
- `/forgot-password`
- `/reset-password`
- `/2fa-setup`
- admin login area

### User dashboard

- `/dashboard`
- `/dashboard/accounts`
- `/dashboard/analytics`
- `/dashboard/streams`
- `/dashboard/videos`
- `/dashboard/moderation`
- `/dashboard/billing`
- `/dashboard/settings`
- `/dashboard/docs`
- `/dashboard/support`

### Admin dashboard

- `/admin`
- `/admin/users`
- `/admin/subscriptions`
- `/admin/compliance`
- `/admin/support`
- `/admin/payment-gateways`
- `/admin/ai`
- `/admin/config`
- `/admin/audit-logs`
- `/admin/backups`
- `/admin/blog`
- `/admin/announcements`
- `/admin/security`

## Frontend Capabilities

- user and admin auth flows
- analytics dashboard overview
- account management UI
- video listing, filtering, bulk actions, upload, import, library, templates, and editing
- stream management UI, analytics, history, and video-live creation
- support chat and realtime hooks
- notification center
- billing, checkout, usage, subscriptions, and payment retry flows
- full admin panel UI for internal operations
- rich domain-specific UI components built on top of Radix primitives

## Directory Structure

```text
frontend/
├── src/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   └── types/
├── public/
├── docs/
├── package.json
├── next.config.mjs
├── tailwind.config.ts
└── .env.local.example
```

## API Configuration

Primary frontend env reference:

- [frontend/.env.local.example](/d:/Project/youtube-automation/frontend/.env.local.example:1)

Minimum configuration:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=YouTube Automation Platform
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

The frontend depends on the FastAPI backend, so make sure the backend is running at the configured API URL.

## Running Locally

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Access:

- App: `http://localhost:3000`

## Available Scripts

Defined in [package.json](/d:/Project/youtube-automation/frontend/package.json:1):

- `npm run dev`
- `npm run build`
- `npm run start`
- `npm run lint`
- `npm test`
- `npm run test:run`
- `npm run test:ui`

## Realtime Integration

The frontend already includes hooks and clients for realtime features, including:

- WebSocket client support
- realtime notifications
- realtime stream health updates
- realtime chat
- admin support realtime flows

Relevant files:

- [src/hooks/use-websocket.ts](/d:/Project/youtube-automation/frontend/src/hooks/use-websocket.ts:1)
- [src/hooks/use-realtime-stream-health.ts](/d:/Project/youtube-automation/frontend/src/hooks/use-realtime-stream-health.ts:1)
- [src/hooks/use-support-realtime.ts](/d:/Project/youtube-automation/frontend/src/hooks/use-support-realtime.ts:1)
- [src/lib/websocket/client.ts](/d:/Project/youtube-automation/frontend/src/lib/websocket/client.ts:1)

## Testing

The frontend uses Vitest.

Run tests:

```bash
cd frontend
npm test
```

Run once:

```bash
npm run test:run
```

Additional documentation:

- [docs/E2E_TESTING.md](/d:/Project/youtube-automation/frontend/docs/E2E_TESTING.md:1)

## Design and Components

The UI is primarily built around:

- `src/components/ui`
- `src/components/dashboard`
- `src/components/admin`
- `src/components/videos`
- `src/components/streams`

This is no longer a generic starter frontend; it already contains a mature set of domain-specific screens and components.

## Docker Build

The frontend is also built and started through the root compose setup:

```bash
make prod
```

Docker build arg used by the frontend image:

- `NEXT_PUBLIC_API_URL=http://backend:8000/api/v1`

For local runtime, the frontend uses:

- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`

## Notes

- The previous frontend README was still the default Next.js template and did not reflect the current application.
- For full setup and architecture context, see [../README.md](/d:/Project/youtube-automation/README.md:1) and [../DEPLOYMENT.md](/d:/Project/youtube-automation/DEPLOYMENT.md:1).
