# End-to-End Testing Guide

This document describes the end-to-end testing strategy for the YouTube Automation Platform.

## Overview

The platform uses a combination of:
- **Property-Based E2E Tests**: Automated tests using Hypothesis for comprehensive flow coverage
- **Manual Testing**: For complex user flows and visual verification
- **API Integration Tests**: For backend API validation
- **Component Tests**: For UI component behavior

## Automated E2E Test Suites

The backend includes comprehensive E2E test suites in `backend/tests/e2e/`:

### Test Files
- `test_auth_flow.py` - Authentication flows (registration, login, 2FA, password reset)
- `test_oauth_flow.py` - YouTube OAuth connection flows
- `test_stream_lifecycle.py` - Stream creation, scheduling, health monitoring
- `test_payment_flow.py` - Payment processing, gateway selection, subscriptions
- `test_error_scenarios.py` - Error handling, retries, rate limiting

### Running E2E Tests
```bash
cd backend
python -m pytest tests/e2e/ -v
```

### Test Coverage
- **59 property-based tests** covering all major user flows
- Tests validate requirements from the specification document
- Each test uses Hypothesis for property-based testing with 50 examples per test

## Test Environments

### Development
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/v1`
- WebSocket: `ws://localhost:8000/ws`

### Staging
- Configure via environment variables in `.env.local`

## User Flow Test Cases

### 1. Authentication Flow

#### 1.1 User Registration
1. Navigate to `/register`
2. Fill in email, password, and name
3. Submit form
4. Verify redirect to login page
5. Verify success message

**Expected Results:**
- User account created in database
- Confirmation email sent (if configured)
- Redirect to login page

#### 1.2 User Login
1. Navigate to `/login`
2. Enter valid credentials
3. Submit form
4. Verify redirect to dashboard

**Expected Results:**
- JWT tokens stored in localStorage
- User redirected to `/dashboard`
- User info displayed in header

#### 1.3 2FA Setup and Login
1. Login to account
2. Navigate to Settings > Security
3. Enable 2FA
4. Scan QR code with authenticator app
5. Enter verification code
6. Logout and login again
7. Enter 2FA code when prompted

**Expected Results:**
- 2FA enabled on account
- Backup codes provided
- Login requires 2FA code

#### 1.4 Password Reset
1. Navigate to `/forgot-password`
2. Enter email address
3. Check email for reset link
4. Click link and set new password
5. Login with new password

**Expected Results:**
- Reset email sent
- Password updated
- Can login with new password

### 2. OAuth Flow (YouTube Account Connection)

#### 2.1 Connect YouTube Account
1. Navigate to Dashboard > Accounts
2. Click "Connect Account"
3. Complete Google OAuth flow
4. Grant required permissions
5. Verify account appears in list

**Expected Results:**
- OAuth tokens stored (encrypted)
- Channel metadata fetched
- Account status shows "Active"

#### 2.2 Token Refresh
1. Wait for token to expire (or manually expire)
2. Perform an action requiring API access
3. Verify automatic token refresh

**Expected Results:**
- Token refreshed automatically
- No user intervention required
- Action completes successfully

### 3. Stream Lifecycle Testing

#### 3.1 Create Live Event
1. Navigate to Dashboard > Streams
2. Click "Create Stream"
3. Fill in stream details
4. Select account
5. Configure settings
6. Save stream

**Expected Results:**
- YouTube broadcast created
- Stream key generated
- Event appears in list

#### 3.2 Start Stream
1. Open stream control panel
2. Click "Start Stream"
3. Verify stream status changes to "Live"
4. Check YouTube for live broadcast

**Expected Results:**
- Stream transitions to live
- Health metrics start updating
- Viewer count visible

#### 3.3 Monitor Stream Health
1. While stream is live
2. Observe health metrics
3. Verify real-time updates (every 10 seconds)
4. Check for alerts on degradation

**Expected Results:**
- Bitrate, frame rate displayed
- Connection status indicator
- Alerts on threshold breach

#### 3.4 Stop Stream
1. Click "End Stream"
2. Confirm action
3. Verify stream ends gracefully

**Expected Results:**
- Stream status changes to "Ended"
- YouTube broadcast ends
- Analytics available

### 4. Payment Flow Testing

#### 4.1 View Available Plans
1. Navigate to Dashboard > Billing
2. View subscription options
3. Compare plan features

**Expected Results:**
- All plans displayed
- Features clearly listed
- Current plan highlighted

#### 4.2 Upgrade Subscription (Stripe)
1. Select a paid plan
2. Choose Stripe as payment method
3. Enter test card details
4. Complete checkout

**Test Card Numbers:**
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- 3D Secure: `4000 0025 0000 3155`

**Expected Results:**
- Payment processed
- Subscription activated
- Features unlocked

#### 4.3 Payment with Alternative Gateway
1. Initiate payment with Stripe
2. Simulate failure
3. Retry with PayPal
4. Complete payment

**Expected Results:**
- Failure handled gracefully
- Alternative gateways offered
- Payment completes on retry

### 5. Error Scenario Testing

#### 5.1 Network Errors
1. Disconnect network
2. Attempt API action
3. Verify error handling
4. Reconnect and retry

**Expected Results:**
- Error toast displayed
- Retry option available
- Action completes on retry

#### 5.2 Session Expiry
1. Login to application
2. Manually clear tokens
3. Attempt protected action
4. Verify redirect to login

**Expected Results:**
- 401 error handled
- User redirected to login
- Session cleared

#### 5.3 Rate Limiting
1. Make rapid API requests
2. Trigger rate limit
3. Verify handling

**Expected Results:**
- 429 error displayed
- Retry-after respected
- Requests resume after cooldown

## API Integration Tests

### Running Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Key Test Suites
- `tests/auth/` - Authentication tests
- `tests/account/` - YouTube account tests
- `tests/stream/` - Streaming tests
- `tests/billing/` - Payment tests
- `tests/payment_gateway/` - Gateway tests

## WebSocket Testing

### Connection Test
1. Login to application
2. Open browser DevTools > Network > WS
3. Verify WebSocket connection established
4. Check for heartbeat messages

### Real-time Updates Test
1. Open stream control panel
2. Start a stream
3. Verify health updates arrive via WebSocket
4. Check update frequency (every 10 seconds)

## Performance Checklist

- [ ] Page load time < 3 seconds
- [ ] API response time < 500ms
- [ ] WebSocket latency < 100ms
- [ ] No memory leaks on long sessions
- [ ] Smooth animations (60fps)

## Accessibility Checklist

- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Color contrast meets WCAG AA
- [ ] Focus indicators visible
- [ ] Form labels present

## Browser Compatibility

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari
- [ ] Mobile Chrome

## Test Data

### Test Users
Create test users via the registration flow or seed script.

### Test YouTube Accounts
Use YouTube API sandbox or test channels for OAuth testing.

### Test Payment Cards
See payment gateway documentation for test card numbers.

## Reporting Issues

When reporting test failures:
1. Describe the test case
2. List steps to reproduce
3. Include expected vs actual results
4. Attach screenshots/logs
5. Note browser/environment
