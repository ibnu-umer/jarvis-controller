# ScreenTime Module — Design & Implementation Plan

## Overview
The ScreenTime module will track and manage user device/app usage durations, provide aggregated analytics, and enforce usage limits or reminders.

## Goals
- Monitor active window/application usage in real-time.
- Track total daily screen time.
- Track time per application and per category.
- Provide structured logs and analytics.
- Support rules like breaks, daily limits, and blocking.

## Core Features
- Real-time active window detection.
- Usage time logging.
- App category mapping (system, browser, productivity, entertainment, custom).
- Persistence via local storage.
- API actions accessible through the hybrid architecture.

## Planned Actions
| Action | Params | Description |
|--------|---------|--------------|
| start_tracking | None | Starts collection of usage data |
| stop_tracking | None | Stops tracking |
| get_total_time | date | Returns total screen time for the given date |
| get_app_usage | app_name, date | Returns usage metrics for specific app |
| get_usage_report | date | Returns structured analytics summary |
| set_limit | app_name, minutes | Sets maximum usage duration |
| enforce_limit | None | Checks limits & auto block/alert |
| list_tracked_apps | None | Lists all applications with recorded data |

## Data Structure
```json
{
  "date": "YYYY-MM-DD",
  "total_time": 12345,
  "apps": [
    {
      "name": "chrome.exe",
      "duration": 5432,
      "category": "browser"
    }
  ]
}
```

## Implementation Layers
### 1. Window Activity Listener
- Polling via Win32 API to detect active window changes.
- Track timestamps and calculate durations.

### 2. Storage Engine
- JSON/SQLite local DB.
- Incremental saving to avoid loss on shutdown.

### 3. Limit Engine
- Trigger alerts via tray popup.
- Optionally auto-hide app or lock screen.

## Future Extensions
- Sync to cloud.
- Multi-machine merging.
- Productivity scoring.

## Priority Roadmap
1. Basic tracking + data persistence
2. Analytics retrieval actions
3. Limit system
4. UI dashboard / tray integration
