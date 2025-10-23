# Feature Description: Improve Frontend Repo Layer

## Current State
Right now, the **service layer is making all the storage decisions**:
- Service directly calls `infrastructure.setStorageItem()` for AsyncStorage
- Service directly calls `offlineCache.getCachedUnit()` for offline cache  
- Service directly calls `outboxProvider.enqueue()` for writes
- Service calls `repo.methodName()` for HTTP

This means the service needs to know about all storage mechanisms and decide which one to use.

## Proposed Architecture (Better!)
The **repo layer should abstract all data access**:

```typescript
// service.ts - just business logic
async startSession(lessonId: string): Promise<LearningSession> {
  const session = { 
    id: this.generateSessionId(), 
    lessonId, 
    status: 'active',
    // ... business logic to construct session
  };
  
  // Repo decides: AsyncStorage + outbox
  await this.repo.writeSession(session);
  
  return session;
}

async getSession(sessionId: string): Promise<LearningSession | null> {
  // Repo decides: read from AsyncStorage
  return await this.repo.readSession(sessionId);
}
```

```typescript
// repo.ts - all data access decisions
async writeSession(session: LearningSession): Promise<void> {
  // Decision 1: Store locally
  await this.infrastructure.setStorageItem(
    `session:${session.id}`, 
    JSON.stringify(session)
  );
  
  // Decision 2: Queue for server sync
  await this.outbox.enqueue({
    endpoint: '/api/v1/learning_session/',
    method: 'POST',
    payload: { session_id: session.id, lesson_id: session.lessonId, ... }
  });
}

async readSession(sessionId: string): Promise<LearningSession | null> {
  // Decision: Always read from local storage
  const stored = await this.infrastructure.getStorageItem(`session:${sessionId}`);
  return stored ? JSON.parse(stored) : null;
}

async syncSessionsFromServer(userId: string): Promise<void> {
  // Decision: Explicit HTTP call, then update local storage
  const response = await this.infrastructure.request<ApiSessionListResponse>(...);
  for (const session of response.sessions) {
    await this.infrastructure.setStorageItem(`session:${session.id}`, ...);
  }
}
```

## Benefits

1. **Consistent with backend**: Just like backend repo abstracts SQLAlchemy, frontend repo would abstract storage
2. **Service focuses on business logic**: Service doesn't need to know about AsyncStorage, offline_cache, or outbox
3. **Easier to change storage**: If we switch from AsyncStorage to SQLite, only repo changes
4. **Clearer contracts**: `repo.writeSession()` clearly means "persist this session" vs service having to know HOW to persist

## AsyncStorage vs offline_cache

To answer your question about these two:

- **AsyncStorage** (via `infrastructure.setStorageItem`): General-purpose key-value store for app state
  - User sessions
  - User progress
  - App preferences
  - Any transient state that needs to survive app restarts

- **offline_cache**: Structured cache specifically for pre-downloaded content
  - Full unit payloads with lessons
  - Asset URLs
  - Designed for bulk downloads
  - Has TTL/eviction logic
  - Knows about unit structure

Think of offline_cache as a specialized cache for "content I explicitly downloaded for offline use", while AsyncStorage is for "anything the app needs to remember."

## Summary

This would be a significant architectural improvement. It would mean:

1. Moving storage decisions from service to repo
2. Repo methods like `writeSession()`, `readSession()`, `writeProgress()`, etc.
3. Service just calls repo methods without knowing about AsyncStorage/outbox/cache
4. Update architecture docs to reflect this

This would make the frontend repo truly analogous to the backend repo layer.
