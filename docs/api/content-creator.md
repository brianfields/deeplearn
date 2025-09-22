# Content Creator API

This document describes the Content Creator API endpoints for mobile unit creation functionality.

## Base URL

```
/api/v1/content-creator
```

## Endpoints

### Create Unit from Mobile App

Creates a new learning unit from a topic specification. Unit creation happens asynchronously in the background.

**Endpoint:** `POST /units`

**Request Body:**
```json
{
  "topic": "string",
  "difficulty": "beginner" | "intermediate" | "advanced",
  "target_lesson_count": number | null
}
```

**Request Fields:**
- `topic` (required): The topic for the unit (e.g., "Introduction to Machine Learning")
- `difficulty` (optional): Difficulty level, defaults to "beginner"
- `target_lesson_count` (optional): Number of lessons to generate, null for default

**Response:** `201 Created`
```json
{
  "unit_id": "string",
  "status": "in_progress",
  "title": "string"
}
```

**Response Fields:**
- `unit_id`: Unique identifier for the created unit
- `status`: Will be "in_progress" initially
- `title`: Generated title for the unit (usually matches the topic)

**Error Responses:**
- `400 Bad Request`: Invalid request data (e.g., empty topic, invalid difficulty)
- `500 Internal Server Error`: Server error during unit creation

**Example:**
```bash
curl -X POST /api/v1/content-creator/units \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Introduction to Neural Networks",
    "difficulty": "beginner",
    "target_lesson_count": 5
  }'
```

### Retry Unit Creation

Retries the creation process for a failed unit. Resets the unit to "in_progress" status and restarts background processing.

**Endpoint:** `POST /units/{unit_id}/retry`

**Path Parameters:**
- `unit_id` (required): ID of the unit to retry

**Response:** `200 OK`
```json
{
  "unit_id": "string",
  "status": "in_progress",
  "title": "string"
}
```

**Error Responses:**
- `404 Not Found`: Unit not found
- `400 Bad Request`: Unit cannot be retried (e.g., not in failed state)
- `500 Internal Server Error`: Server error during retry

**Example:**
```bash
curl -X POST /api/v1/content-creator/units/abc-123-def/retry
```

### Dismiss Unit

Permanently deletes a failed unit from the database. This action cannot be undone.

**Endpoint:** `DELETE /units/{unit_id}`

**Path Parameters:**
- `unit_id` (required): ID of the unit to dismiss

**Response:** `200 OK`
```json
{
  "message": "Unit dismissed successfully"
}
```

**Error Responses:**
- `404 Not Found`: Unit not found
- `500 Internal Server Error`: Server error during dismissal

**Example:**
```bash
curl -X DELETE /api/v1/content-creator/units/abc-123-def
```

## Unit Status Flow

Units progress through the following statuses:

1. **draft**: Unit created but processing not started
2. **in_progress**: Unit is being generated in the background
3. **completed**: Unit generation finished successfully, unit is ready for use
4. **failed**: Unit generation failed with an error

## Background Processing

Unit creation happens asynchronously:

1. Client submits a `POST /units` request
2. Server immediately returns with `status: "in_progress"`
3. Client should poll the units list endpoint to check for status updates
4. When complete, status becomes `"completed"` and unit becomes interactive
5. If creation fails, status becomes `"failed"` with error details

### Background Execution Flow Diagram

```
Mobile Client                 API Server                   Flow Engine               Database
      |                           |                           |                        |
      | POST /units              |                           |                        |
      |------------------------->|                           |                        |
      |                          |                           |                        |
      |                          | 1. Create unit record     |                        |
      |                          |--------------------------------------------->    |
      |                          |   (status=in_progress)    |                        |
      |                          |                           |                        |
      |                          | 2. Start background task  |                        |
      |                          |-------------------------->|                        |
      |                          |                           |                        |
      | 201 Created              |                           |                        |
      | {status: in_progress}    |                           |                        |
      |<-------------------------|                           |                        |
      |                          |                           |                        |
      |                          |                           | 3. Execute flow       |
      |                          |                           |   (async task)        |
      |                          |                           |                        |
      | GET /catalog/units       |                           |                        |
      | (polling for updates)    |                           |                        |
      |------------------------->|                           |                        |
      |                          |                           |                        |
      |                          | Query current status      |                        |
      |                          |--------------------------------------------->    |
      |                          |                           |                        |
      | 200 OK                   |                           |                        |
      | {status: in_progress}    |                           |                        |
      |<-------------------------|                           |                        |
      |                          |                           |                        |
      |                          |                           | 4. Update progress    |
      |                          |                           |-------------------->  |
      |                          |                           |   (periodic updates)   |
      |                          |                           |                        |
      |                          |                           | 5. Complete/Fail      |
      |                          |                           |-------------------->  |
      |                          |                           |   (final status)       |
      |                          |                           |                        |
      | GET /catalog/units       |                           |                        |
      |------------------------->|                           |                        |
      |                          |                           |                        |
      |                          | Query final status        |                        |
      |                          |--------------------------------------------->    |
      |                          |                           |                        |
      | 200 OK                   |                           |                        |
      | {status: completed}      |                           |                        |
      |<-------------------------|                           |                        |
```

### Error Handling Flow

```
Mobile Client                 API Server                   Flow Engine               Database
      |                           |                           |                        |
      | POST /units              |                           |                        |
      |------------------------->|                           |                        |
      |                          |                           |                        |
      |                          | Create unit & start task  |                        |
      |                          |-------------------------->|                        |
      |                          |                           |                        |
      | 201 Created              |                           |                        |
      |<-------------------------|                           |                        |
      |                          |                           |                        |
      |                          |                           | Execute flow          |
      |                          |                           | (encounters error)    |
      |                          |                           |                        |
      |                          |                           | Update status=failed  |
      |                          |                           |-------------------->  |
      |                          |                           | + error_message        |
      |                          |                           |                        |
      | GET /catalog/units       |                           |                        |
      |------------------------->|                           |                        |
      |                          |                           |                        |
      | 200 OK                   |                           |                        |
      | {status: failed,         |                           |                        |
      |  error_message: "..."}   |                           |                        |
      |<-------------------------|                           |                        |
      |                          |                           |                        |
      | User chooses retry       |                           |                        |
      | POST /units/{id}/retry   |                           |                        |
      |------------------------->|                           |                        |
      |                          |                           |                        |
      |                          | Reset status & restart    |                        |
      |                          |-------------------------->|                        |
      |                          |                           |                        |
      | 200 OK                   |                           |                        |
      | {status: in_progress}    |                           |                        |
      |<-------------------------|                           |                        |
      |                          |                           |                        |
      | (polling continues...)   |                           |                        |
```

### Recovery Options Flow

```
Failed Unit State
       |
       |
   User sees error indicator
       |
       ├─── Retry Option ────────┐
       |                        |
       |                        | POST /units/{id}/retry
       |                        |         |
       |                        |         v
       |                    Reset to in_progress
       |                    Restart background task
       |                             |
       |                             v
       |                    (Normal flow resumes)
       |
       └─── Dismiss Option ──────┐
                                |
                                | DELETE /units/{id}
                                |         |
                                |         v
                            Remove from database
                            Remove from UI list
                                     |
                                     v
                               Unit permanently deleted
```

## Polling for Status Updates

To check unit status, use the main units endpoint:

```bash
GET /api/v1/catalog/units
```

This will return all units including their current status. Filter by unit ID if needed.

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Success
- `201 Created`: Resource created successfully  
- `400 Bad Request`: Invalid input data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a `detail` field with a human-readable error message:

```json
{
  "detail": "Topic is required"
}
```

### Error Codes and Recovery Procedures

#### API Error Codes

| Error Code | HTTP Status | Message | Recovery Action |
|------------|-------------|---------|----------------|
| `TOPIC_REQUIRED` | 400 | "Topic is required" | Provide a non-empty topic string |
| `INVALID_DIFFICULTY` | 400 | "Invalid difficulty level" | Use one of: "beginner", "intermediate", "advanced" |
| `INVALID_LESSON_COUNT` | 400 | "Target lesson count must be between 1 and 20" | Provide count between 1-20 or null for default |
| `UNIT_NOT_FOUND` | 404 | "Unit not found" | Check unit ID or refresh unit list |
| `UNIT_NOT_FAILED` | 400 | "Unit is not in failed state" | Only failed units can be retried |
| `BACKGROUND_TASK_ERROR` | 500 | "Failed to start background task" | Retry the request or check server logs |
| `DATABASE_ERROR` | 500 | "Database operation failed" | Retry the request, may be temporary |

#### Background Processing Error Codes

These errors are stored in the `error_message` field when units fail during background processing:

| Error Type | Description | Recovery Action |
|------------|-------------|----------------|
| `CONTENT_GENERATION_FAILED` | LLM service failed to generate content | Retry unit creation - may succeed on retry |
| `FLOW_EXECUTION_ERROR` | Flow engine encountered an error | Retry unit creation or check server resources |
| `TIMEOUT_ERROR` | Unit creation took too long | Retry with simpler topic or fewer lessons |
| `RESOURCE_EXHAUSTION` | Server out of memory/resources | Wait and retry later, or contact admin |
| `VALIDATION_ERROR` | Generated content failed validation | Retry unit creation - usually succeeds on retry |
| `EXTERNAL_SERVICE_ERROR` | External API (LLM) unavailable | Wait for service recovery, then retry |

#### Client-Side Error Handling Strategy

```typescript
// Recommended error handling pattern for mobile clients

interface ErrorHandlingStrategy {
  // Immediate API errors (400/404/500)
  handleApiError(error: ApiError): void {
    switch (error.statusCode) {
      case 400:
        // Show validation error to user
        showUserError(error.detail);
        break;
      case 404:
        // Refresh data, unit may have been deleted
        refreshUnitList();
        break;
      case 500:
        // Offer retry option
        showRetryDialog();
        break;
    }
  }

  // Background processing errors
  handleUnitFailure(unit: Unit): void {
    const errorType = this.categorizeError(unit.error_message);
    
    switch (errorType) {
      case 'TRANSIENT':
        // Automatically suggest retry
        showRetryOption(unit.id);
        break;
      case 'PERMANENT':
        // Suggest dismissal or topic change
        showDismissOption(unit.id);
        break;
      case 'RESOURCE':
        // Suggest waiting and trying later
        showWaitSuggestion();
        break;
    }
  }
}
```

#### Recovery Procedures by Scenario

**Scenario 1: API Request Validation Failed**
- **Symptoms**: 400 Bad Request with validation message
- **Recovery**: 
  1. Fix validation issues in request data
  2. Retry the API call
  3. No server-side action needed

**Scenario 2: Unit Creation Failed During Processing**
- **Symptoms**: Unit status becomes "failed" with error_message
- **Recovery**:
  1. User sees error indicator in UI
  2. User can choose "Retry" → POST /units/{id}/retry
  3. User can choose "Dismiss" → DELETE /units/{id}
  4. For repeated failures, suggest simpler topic

**Scenario 3: Server Temporarily Unavailable**
- **Symptoms**: 500 Internal Server Error
- **Recovery**:
  1. Client implements exponential backoff retry
  2. Show user-friendly "try again later" message
  3. For unit creation, check if unit was created despite error

**Scenario 4: Network Interruption During Creation**
- **Symptoms**: Unit stuck in "in_progress" state
- **Recovery**:
  1. Client continues polling for status updates
  2. If stuck >30 minutes, suggest refresh/retry
  3. Server cleanup job can mark stale units as failed

**Scenario 5: Polling Timeout**
- **Symptoms**: Unit remains "in_progress" for extended period
- **Recovery**:
  1. Continue polling at reduced frequency (every 30s)
  2. Show user that processing is taking longer than usual
  3. Offer "Cancel" option that dismisses the unit

#### Client Implementation Guidelines

1. **Exponential Backoff**: For transient errors, retry with increasing delays
2. **User Feedback**: Always inform users about error states and recovery options
3. **Graceful Degradation**: Don't block entire app when unit creation fails
4. **Status Monitoring**: Poll unit status at reasonable intervals (5-10 seconds)
5. **Cleanup**: Provide UI to dismiss failed/stuck units

## Rate Limiting

Currently no rate limiting is implemented, but consider implementing reasonable limits in production to prevent abuse of the background processing system.