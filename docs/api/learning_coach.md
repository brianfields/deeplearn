# Learning Coach API

Endpoints that power the conversational unit-creation experience. All routes live under
`/api/v1/learning_coach` and require the standard mobile authentication headers.

## Session Lifecycle

### Start a session

- **Endpoint**: `POST /api/v1/learning_coach/session/start`
- **Body**:
  ```json
  {
    "topic": "learning linear algebra",
    "user_id": "<uuid>"
  }
  ```
- **Response**: `201 Created` with the initial `LearningCoachSessionState` payload containing the
  generated conversation ID, metadata, and the coach's opening prompt.

### Send a learner turn

- **Endpoint**: `POST /api/v1/learning_coach/session/message`
- **Body**:
  ```json
  {
    "conversation_id": "<id from start>",
    "message": "I prefer project-based work",
    "user_id": "<uuid>"
  }
  ```
- **Response**: `200 OK` returning the refreshed `LearningCoachSessionState` with the appended learner
  message and the coach's follow-up.

### Accept the proposed brief

- **Endpoint**: `POST /api/v1/learning_coach/session/accept`
- **Body**:
  ```json
  {
    "conversation_id": "<id from start>",
    "brief": {
      "title": "Linear Algebra for Makers",
      "description": "Hands-on primer for hardware enthusiasts",
      "objectives": [
        "Model systems with matrices",
        "Apply eigenvectors to robotics problems"
      ],
      "notes": "Plan for three weekend build sessions"
    },
    "user_id": "<uuid>"
  }
  ```
- **Response**: `200 OK` returning the updated session state with the accepted brief persisted in
  conversation metadata.

### Fetch session state

- **Endpoint**: `GET /api/v1/learning_coach/session/{conversation_id}`
- **Query params**:
  - `include_system_messages` (optional, default `false`) — include hidden system messages when
    debugging.
- **Response**: `200 OK` with the latest `LearningCoachSessionState` so clients can resume active
  conversations.

## Response Model

All endpoints return a `LearningCoachSessionState` payload:

```json
{
  "conversation_id": "uuid",
  "messages": [
    {
      "id": "msg_123",
      "role": "assistant",
      "content": "Let's design a learning plan...",
      "created_at": "2024-03-21T18:42:11.845Z",
      "metadata": {}
    }
  ],
  "metadata": {
    "topic": "Linear Algebra",
    "proposed_brief": {
      "title": "Linear Algebra for Makers",
      "objectives": ["Model systems", "Use eigenvectors"]
    }
  },
  "proposed_brief": {
    "title": "Linear Algebra for Makers",
    "description": "Hands-on primer for hardware enthusiasts",
    "objectives": ["Model systems", "Use eigenvectors"],
    "notes": "Plan for three weekend build sessions"
  },
  "accepted_brief": null
}
```

## Admin QA

The admin dashboard consumes dedicated endpoints under
`/api/v1/admin/learning-coach/conversations` for transcript reviews.

### List conversations

- **Endpoint**: `GET /api/v1/admin/learning-coach/conversations`
- **Query params**:
  - `limit` (optional, default `20`) — page size for the result set.
  - `offset` (optional, default `0`) — zero-based offset for pagination.
- **Response**: `200 OK`

```json
{
  "conversations": [
    {
      "id": "conv_123",
      "user_id": "learner-42",
      "title": "AI for makers",
      "message_count": 7,
      "created_at": "2024-06-09T18:11:00Z",
      "updated_at": "2024-06-10T04:23:00Z",
      "last_message_at": "2024-06-10T04:23:00Z",
      "metadata": {
        "topic": "AI for makers",
        "accepted_at": "2024-06-10T04:21:00Z",
        "accepted_brief": {
          "title": "AI for Makers"
        }
      }
    }
  ],
  "limit": 20,
  "offset": 0,
  "has_next": false
}
```

### Retrieve a transcript

- **Endpoint**: `GET /api/v1/admin/learning-coach/conversations/{conversation_id}`
- **Response**: `200 OK`

```json
{
  "conversation_id": "conv_123",
  "metadata": {
    "topic": "AI for makers",
    "accepted_at": "2024-06-10T04:21:00Z",
    "user_id": "learner-42"
  },
  "messages": [
    {
      "id": "msg_1",
      "role": "assistant",
      "content": "Welcome! Let's design a learning plan...",
      "created_at": "2024-06-09T18:11:00Z",
      "metadata": {}
    }
  ],
  "proposed_brief": {
    "title": "AI for Makers",
    "description": "Hands-on curriculum exploring applied ML concepts.",
    "objectives": [
      "Prototype with vision models",
      "Deploy tinyML workloads"
    ],
    "notes": "Include weekend build checkpoints",
    "level": "Intermediate"
  },
  "accepted_brief": {
    "title": "AI for Makers (Accepted)",
    "description": "Refined plan focusing on robotics applications.",
    "objectives": [
      "Calibrate sensors",
      "Deploy control loops"
    ],
    "notes": null,
    "level": "Intermediate"
  }
}
```

The admin UI surfaces these payloads in paginated tables, transcript viewers, and raw JSON
inspectors so QA teams can review conversation health.
