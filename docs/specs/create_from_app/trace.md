# Implementation Trace for create_from_app

## User Story Summary
As a mobile user, I can create a learning unit from the app by entering a topic (required), choosing difficulty, and optionally a target lesson count. The unit is created immediately in an in-progress state, appears at the top of the list with a progress indicator and disabled interaction, and is generated in the background via the flow engine. When complete, the unit becomes interactive; on failure, it shows error state with retry and dismiss actions. Mobile polls for status updates.

## Implementation Trace

### Step 1: Units screen entry point
**Files involved:**
- `mobile/modules/catalog/screens/UnitListScreen.tsx` (lines 56-58): Navigate to creation form when pressing the create button
```56:103:mobile/modules/catalog/screens/UnitListScreen.tsx
  const handleCreateUnit = useCallback(() => {
    navigation.navigate('CreateUnit');
  }, [navigation]);
...
        <TouchableOpacity
          style={styles.createButton}
          onPress={handleCreateUnit}
          testID="create-unit-button"
        >
```
- `mobile/App.tsx` (lines 61-66): Screen registered as `CreateUnit`
```61:66:mobile/App.tsx
      <LearningStack.Screen
        name="CreateUnit"
        component={CreateUnitScreen}
        options={{
          title: 'Create New Unit',
        }}
      />
```

**Implementation reasoning:** The Units list exposes a visible primary action that routes to the creation form; the route is registered in the stack.

**Confidence level:** ✅ High
**Concerns:** None

### Step 2: Create button visible alongside units
**Files involved:**
- `mobile/modules/catalog/screens/UnitListScreen.tsx` (lines 84-104): Header area renders a plus button next to search
```84:104:mobile/modules/catalog/screens/UnitListScreen.tsx
  {/* Search and Create Button */}
  <View style={styles.searchContainer}>
    <View style={styles.searchInputContainer}>
      <Search size={20} color="#9CA3AF" style={styles.searchIcon} />
      <TextInput
        style={styles.searchInput}
        placeholder="Search units..."
        value={searchQuery}
        onChangeText={setSearchQuery}
        placeholderTextColor="#9CA3AF"
        testID="search-input"
      />
    </View>
    <TouchableOpacity
      style={styles.createButton}
      onPress={handleCreateUnit}
      testID="create-unit-button"
    >
```

**Implementation reasoning:** The create button is placed in the toolbar next to search on the Units list.

**Confidence level:** ✅ High
**Concerns:** None

### Step 3: Creation form with topic, difficulty, and target lesson count
**Files involved:**
- `mobile/modules/catalog/screens/CreateUnitScreen.tsx` (lines 48-66): Validation for required topic and target count range
```48:66:mobile/modules/catalog/screens/CreateUnitScreen.tsx
  const validateForm = (): boolean => {
    const newErrors: Partial<CreateUnitFormData> = {};

    if (!formData.topic.trim()) {
      newErrors.topic = 'Topic is required';
    } else if (formData.topic.trim().length < 3) {
      newErrors.topic = 'Topic must be at least 3 characters long';
    }

    if (
      formData.targetLessonCount !== null &&
      (formData.targetLessonCount < 1 || formData.targetLessonCount > 20)
    ) {
      newErrors.targetLessonCount =
        'Target lesson count must be between 1 and 20';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
```
- `mobile/modules/catalog/screens/CreateUnitScreen.tsx` (lines 156-178, 181-208, 213-245): Topic, difficulty segmented control, and target lesson numeric input
```156:178:mobile/modules/catalog/screens/CreateUnitScreen.tsx
  {/* Topic Input */}
  <View style={styles.fieldContainer}>
    <Text style={styles.fieldLabel}>Topic *</Text>
    <TextInput
      style={[styles.textInput, errors.topic && styles.textInputError]}
      placeholder="e.g., JavaScript Promises, Ancient Rome, Quantum Physics"
      placeholderTextColor="#8E8E93"
      value={formData.topic}
      onChangeText={text => {
        setFormData({ ...formData, topic: text });
        if (errors.topic) {
          setErrors({ ...errors, topic: undefined });
        }
      }}
      multiline
      numberOfLines={3}
      textAlignVertical="top"
      editable={!isSubmitting}
    />
```
```181:208:mobile/modules/catalog/screens/CreateUnitScreen.tsx
  {/* Difficulty Selection */}
  <View style={styles.fieldContainer}>
    <Text style={styles.fieldLabel}>Difficulty Level</Text>
    <View style={styles.difficultyContainer}>
      {difficultyOptions.map(option => (
        <TouchableOpacity
          key={option.value}
          style={[
            styles.difficultyOption,
            formData.difficulty === option.value &&
              styles.difficultyOptionSelected,
          ]}
          onPress={() =>
            setFormData({ ...formData, difficulty: option.value })
          }
          disabled={isSubmitting}
        >
          <Text
            style={[
              styles.difficultyText,
              formData.difficulty === option.value &&
                styles.difficultyTextSelected,
            ]}
          >
            {option.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  </View>
```
```213:245:mobile/modules/catalog/screens/CreateUnitScreen.tsx
  {/* Target Lesson Count */}
  <View style={styles.fieldContainer}>
    <Text style={styles.fieldLabel}>
      Target Lesson Count (Optional)
    </Text>
    <TextInput
      style={[
        styles.textInput,
        styles.numberInput,
        errors.targetLessonCount && styles.textInputError,
      ]}
      placeholder="5"
      placeholderTextColor="#8E8E93"
      value={formData.targetLessonCount?.toString() || ''}
      onChangeText={text => {
        const num = text ? parseInt(text, 10) : null;
        setFormData({
          ...formData,
          targetLessonCount: isNaN(num!) ? null : num,
        });
        if (errors.targetLessonCount) {
          setErrors({ ...errors, targetLessonCount: undefined });
        }
      }}
      keyboardType="number-pad"
      editable={!isSubmitting}
    />
```

**Implementation reasoning:** The form provides exactly the three inputs required with client-side validation.

**Confidence level:** ✅ High
**Concerns:** None

### Step 4: Submitting the form triggers unit creation
**Files involved:**
- `mobile/modules/catalog/screens/CreateUnitScreen.tsx` (lines 69-115): Submit calls mutation then navigates back
```69:115:mobile/modules/catalog/screens/CreateUnitScreen.tsx
  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }
...
    try {
      const response = await createUnit.mutateAsync({
        topic: formData.topic.trim(),
        difficulty: formData.difficulty,
        targetLessonCount: formData.targetLessonCount,
      });
...
      navigation.goBack();
...
      setTimeout(() => {
        Alert.alert(
          'Unit Creation Started! 🎉',
          `Your unit "${response.title}" is being created in the background. You can track its progress in the Units list.`,
          [{ text: 'Got it!' }]
        );
      }, 100);
    } catch (error: any) {
```
- `mobile/modules/catalog/queries.ts` (lines 191-201): Mutation invokes repo API
```191:201:mobile/modules/catalog/queries.ts
  return useMutation({
    mutationFn: (request: UnitCreationRequest) => catalog.createUnit(request),
    onSuccess: response => {
      // Invalidate units list to show the new unit
      queryClient.invalidateQueries({
        queryKey: catalogKeys.units(),
      });

      // Optimistically add the new unit to the cache with in_progress status
      // This will make it appear immediately in the units list
```

**Implementation reasoning:** Submission path goes through a React Query mutation to the backend and provides immediate UI feedback.

**Confidence level:** ✅ High
**Concerns:** None

### Step 5: Immediate in-progress unit at top, with indicator and disabled interaction
**Files involved:**
- `mobile/modules/catalog/queries.ts` (lines 204-224): Optimistic unit added to the beginning of the list with `in_progress` status
```204:224:mobile/modules/catalog/queries.ts
      queryClient.setQueryData(catalogKeys.units(), (oldData: any) => {
        if (!oldData) return oldData;

        // Create optimistic unit data
        const optimisticUnit = {
          id: response.unitId,
          title: response.title,
          description: null,
          difficulty: 'beginner' as any,
          lessonCount: 0,
          difficultyLabel: 'Beginner',
          targetLessonCount: null,
          generatedFromTopic: true,
          status: response.status,
          creationProgress: null,
          errorMessage: null,
          statusLabel: 'Creating...',
          isInteractive: false,
          progressMessage: 'Creating unit content...',
        };

        // Add to the beginning of the array (newest first)
        return [optimisticUnit, ...oldData];
      });
```
- `mobile/modules/catalog/components/UnitCard.tsx` (lines 15-21, 73-80): Card is disabled until interactive and shows a status indicator
```15:21:mobile/modules/catalog/components/UnitCard.tsx
  const handlePress = () => {
    // Only allow interaction if unit is completed
    if (unit.isInteractive) {
      onPress(unit);
    }
  };
```
```73:80:mobile/modules/catalog/components/UnitCard.tsx
  {/* Status indicator for non-completed units */}
  {unit.status !== 'completed' && (
    <View style={styles.statusContainer}>
      <UnitProgressIndicator
        status={unit.status}
        progress={unit.creationProgress}
        errorMessage={unit.errorMessage}
      />
    </View>
  )}
```
- `mobile/modules/catalog/components/UnitProgressIndicator.tsx` (lines 35-41): Spinner for in-progress
```35:41:mobile/modules/catalog/components/UnitProgressIndicator.tsx
      case 'in_progress':
        return (
          <View style={[styles.statusIcon, styles.progressIcon]}>
            <ActivityIndicator
              size={size === 'large' ? 'large' : 'small'}
              color="#007AFF"
            />
          </View>
        );
```
- Backend ordering when listing units keeps newest on top
```73:76:backend/modules/content/repo.py
    def list_units(self, limit: int = 100, offset: int = 0) -> list[UnitModel]:
        """List units with pagination, ordered by updated_at descending (newest first)."""
        return self.s.query(UnitModel).order_by(desc(UnitModel.updated_at)).offset(offset).limit(limit).all()
```

**Implementation reasoning:** The mutation adds a placeholder unit at the top immediately, with disabled state and an in-progress indicator; backend also orders by latest updates.

**Confidence level:** ⚠️ Medium
**Concerns:** Listing endpoint currently does not include `status`/`creation_progress` fields (see Step 6/API). After the first refetch, units may appear as `completed` due to frontend default, disabling polling and enabling interaction prematurely.

### Step 6: Background unit creation via flow engine
**Files involved:**
- `backend/modules/content_creator/service.py` (lines 601-608, 609-638): Start background task and update status/progress
```601:608:backend/modules/content_creator/service.py
  async def _start_background_unit_creation(self, unit_id: str, topic: str, difficulty: str, target_lesson_count: int | None) -> None:
    """Start background task to create unit content."""
    # Create background task - don't await it
    self._tsk = asyncio.create_task(self._execute_background_unit_creation(unit_id=unit_id, topic=topic, difficulty=difficulty, target_lesson_count=target_lesson_count))

    # Don't wait for the task to complete
    logger.info(f"🚀 Background unit creation task started for unit {unit_id}")
```
```615:638:backend/modules/content_creator/service.py
    # Update progress
    self.content.update_unit_status(unit_id=unit_id, status=UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "planning", "message": "Planning unit structure..."})
...
    # Update progress
    self.content.update_unit_status(unit_id=unit_id, status=UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "generating", "message": "Generating lessons..."})
...
    # This will create lessons and associate them with the unit
    result = await self.create_unit_from_topic(request)
...
    # Mark as completed
    self.content.update_unit_status(unit_id=unit_id, status=UnitStatus.COMPLETED.value, creation_progress={"stage": "completed", "message": "Unit creation completed successfully"})
```
- `backend/modules/flow_engine/base_flow.py` (lines 146-161): Generic background flow run mechanism and scheduling
```146:161:backend/modules/flow_engine/base_flow.py
    # Create flow run record with background execution mode
    flow_run_id = await service.create_flow_run_record(flow_name=self.flow_name, inputs=inputs, user_id=user_id)

    # Update execution mode to background
    flow_run = service.flow_run_repo.by_id(flow_run_id)
    if flow_run:
        flow_run.execution_mode = "background"
        service.flow_run_repo.save(flow_run)

# Start background task without waiting
self._tsk = asyncio.create_task(self._execute_background_task(flow_run_id, inputs, **kwargs))

return flow_run_id
```

**Implementation reasoning:** The content creator service launches an asyncio task that orchestrates flow execution; flow engine supports background execution and tracking.

**Confidence level:** ✅ High
**Concerns:** None

### Step 7: Auto-update to interactive on completion
**Files involved:**
- `backend/modules/content_creator/service.py` (lines 636-638): Status set to completed
```636:638:backend/modules/content_creator/service.py
    # Mark as completed
    self.content.update_unit_status(unit_id=unit_id, status=UnitStatus.COMPLETED.value, creation_progress={"stage": "completed", "message": "Unit creation completed successfully"})
```
- `mobile/modules/catalog/models.ts` (lines 419-424): Units are interactive when status is completed
```419:424:mobile/modules/catalog/models.ts
  return {
    id: api.id,
    title: api.title,
    description: api.description,
    difficulty,
    lessonCount: api.lesson_count,
    difficultyLabel: formatDifficultyLevel(difficulty),
    targetLessonCount: api.target_lesson_count ?? null,
    generatedFromTopic: !!api.generated_from_topic,
    status,
    creationProgress: api.creation_progress || null,
    errorMessage: api.error_message || null,
    statusLabel: formatUnitStatusLabel(status),
    isInteractive: status === 'completed',
```

**Implementation reasoning:** When the background task finishes, the unit’s status flips to `completed`, and the UI enables interaction based on that status.

**Confidence level:** ⚠️ Medium
**Concerns:** Depends on the list endpoint surfacing status fields; otherwise `status` defaults to `completed` on the frontend, masking actual state.

### Step 8: Failure shows error state with clear indicator
**Files involved:**
- `backend/modules/content_creator/service.py` (lines 641-646): Mark failed with error message and progress
```641:646:backend/modules/content_creator/service.py
  except Exception as e:
    logger.error(f"❌ Background unit creation failed for unit {unit_id}: {e}")

    # Mark as failed
    self.content.update_unit_status(unit_id=unit_id, status=UnitStatus.FAILED.value, error_message=str(e), creation_progress={"stage": "failed", "message": f"Creation failed: {e!s}"})
```
- `mobile/modules/catalog/components/UnitCard.tsx` (lines 190-196): Error styling
```190:196:mobile/modules/catalog/components/UnitCard.tsx
  cardFailed: {
    borderLeftWidth: 4,
    borderLeftColor: '#EF4444',
  },
  titleFailed: {
    color: '#DC2626',
  },
```
- `mobile/modules/catalog/components/UnitProgressIndicator.tsx` (lines 69-72): Failure message display
```69:72:mobile/modules/catalog/components/UnitProgressIndicator.tsx
      case 'failed':
        return errorMessage || 'Creation failed';
      default:
        return 'Unknown status';
```

**Implementation reasoning:** Backend sets failed status and message; UI renders a red-accented card with an error indicator and message.

**Confidence level:** ⚠️ Medium
**Concerns:** Frontend depends on failed status being present in the list endpoint payload.

### Step 9: Completed units open normally
**Files involved:**
- `mobile/modules/catalog/components/UnitCard.tsx` (lines 15-21): Guarded press handler
```15:21:mobile/modules/catalog/components/UnitCard.tsx
  const handlePress = () => {
    // Only allow interaction if unit is completed
    if (unit.isInteractive) {
      onPress(unit);
    }
  };
```
- `mobile/modules/catalog/screens/UnitListScreen.tsx` (lines 49-54): Navigate to UnitDetail
```49:54:mobile/modules/catalog/screens/UnitListScreen.tsx
  const handleUnitPress = useCallback(
    (unit: Unit) => {
      navigation.navigate('UnitDetail', { unitId: unit.id });
    },
    [navigation]
  );
```

**Implementation reasoning:** Interaction is gated on completion; completed items navigate to the detail screen.

**Confidence level:** ✅ High
**Concerns:** None

### Step 10: Retry or dismiss failed units
**Files involved:**
- `mobile/modules/catalog/components/UnitCard.tsx` (lines 85-105): Retry and Dismiss action buttons
```85:105:mobile/modules/catalog/components/UnitCard.tsx
  {/* Failed unit actions */}
  {showFailedActions && (
    <View style={styles.actionContainer}>
      {onRetry && (
        <TouchableOpacity
          style={[styles.actionButton, styles.retryButton]}
          onPress={handleRetry}
          testID={`retry-button-${index}`}
        >
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      )}
      {onDismiss && (
        <TouchableOpacity
          style={[styles.actionButton, styles.dismissButton]}
          onPress={handleDismiss}
          testID={`dismiss-button-${index}`}
        >
          <Text style={styles.dismissButtonText}>Dismiss</Text>
        </TouchableOpacity>
      )}
    </View>
  )}
```
- `mobile/modules/catalog/queries.ts` (lines 239-269, 278-299): Retry and dismiss mutations update cache
```239:269:mobile/modules/catalog/queries.ts
  return useMutation({
    mutationFn: (unitId: string) => catalog.retryUnitCreation(unitId),
    onSuccess: response => {
      // Invalidate units list to refresh status
      queryClient.invalidateQueries({
        queryKey: catalogKeys.units(),
      });

      // Optimistically update the unit status in cache
      queryClient.setQueryData(catalogKeys.units(), (oldData: any) => {
        if (!oldData) return oldData;

        return oldData.map((unit: any) =>
          unit.id === response.unitId
            ? {
                ...unit,
                status: response.status,
                errorMessage: null,
                statusLabel: 'Creating...',
                isInteractive: false,
                progressMessage: 'Retrying unit creation...',
                creationProgress: {
                  stage: 'retrying',
                  message: 'Retrying unit creation...',
                },
              }
            : unit
        );
      });
    },
```
```278:299:mobile/modules/catalog/queries.ts
  return useMutation({
    mutationFn: (unitId: string) => catalog.dismissUnit(unitId),
    onSuccess: (_: any, unitId: string) => {
      // Invalidate units list to refresh
      queryClient.invalidateQueries({
        queryKey: catalogKeys.units(),
      });

      // Optimistically remove the unit from cache
      queryClient.setQueryData(catalogKeys.units(), (oldData: any) => {
        if (!oldData) return oldData;

        return oldData.filter((unit: any) => unit.id !== unitId);
      });
    },
  });
```
- Backend endpoints for retry/dismiss
```82:107:backend/modules/content_creator/routes.py
@router.post("/units/{unit_id}/retry", response_model=MobileUnitCreateResponse)
async def retry_unit_creation(unit_id: str, service: ContentCreatorService = Depends(get_content_creator_service)) -> MobileUnitCreateResponse:
  ...
```
```110:127:backend/modules/content_creator/routes.py
@router.delete("/units/{unit_id}")
def dismiss_unit(unit_id: str, service: ContentCreatorService = Depends(get_content_creator_service)) -> dict[str, str]:
  ...
```
- Backend service behavior
```649:684:backend/modules/content_creator/service.py
async def retry_unit_creation(self, unit_id: str) -> "ContentCreatorService.MobileUnitCreationResult | None":
  ...
  self.content.update_unit_status(unit_id=unit_id, status=UnitStatus.IN_PROGRESS.value, error_message=None, creation_progress={"stage": "retrying", "message": "Retrying unit creation..."})
  ...
```

**Implementation reasoning:** Full retry/dismiss flows exist end-to-end: UI actions, mutations, repo calls, API routes, and service logic.

**Confidence level:** ✅ High
**Concerns:** None

### Backend: Unit status tracking and API
**Files involved:**
- `backend/modules/content/models.py` (lines 73-83): Unit status/progress/error fields with enum constraint
```73:83:backend/modules/content/models.py
  # Status tracking fields for mobile unit creation
  status = Column(String(20), nullable=False, default="completed")
  creation_progress = Column(JSON, nullable=True)
  error_message = Column(Text, nullable=True)
...
  # Add constraint for status enum
  __table_args__ = (CheckConstraint("status IN ('draft', 'in_progress', 'completed', 'failed')", name="check_unit_status"),)
```
- `backend/alembic/versions/eeb77219bb87_add_unit_creation_status.py` (lines 21-37): Migration for status/progress/error and indexes
```21:37:backend/alembic/versions/eeb77219bb87_add_unit_creation_status.py
op.add_column('units', sa.Column('status', sa.String(length=20), nullable=False, server_default="completed"))
op.add_column('units', sa.Column('creation_progress', sa.JSON(), nullable=True))
op.add_column('units', sa.Column('error_message', sa.Text(), nullable=True))
...
op.create_check_constraint(
    'check_unit_status',
    'units',
    "status IN ('draft', 'in_progress', 'completed', 'failed')"
)
...
op.create_index('ix_units_status', 'units', ['status'])
op.create_index('ix_units_status_updated_at', 'units', ['status', 'updated_at'])
```
- `backend/modules/content/repo.py` (lines 77-105): List by status and update status helpers
```77:105:backend/modules/content/repo.py
def get_units_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[UnitModel]:
    """Get units by status, ordered by updated_at descending."""
    return self.s.query(UnitModel).filter(UnitModel.status == status).order_by(desc(UnitModel.updated_at)).offset(offset).limit(limit).all()
...
def update_unit_status(self, unit_id: str, status: str, error_message: str | None = None, creation_progress: dict[str, Any] | None = None) -> UnitModel | None:
    """Update unit status and related fields, returning the updated model or None if not found."""
    unit = self.get_unit_by_id(unit_id)
    if not unit:
        return None

    unit.status = status  # type: ignore[assignment]
    if error_message is not None:
        unit.error_message = error_message  # type: ignore[assignment]
    if creation_progress is not None:
        unit.creation_progress = creation_progress  # type: ignore[assignment]

    # Update timestamp
    unit.updated_at = datetime.now(UTC)  # type: ignore[assignment]
```
- `backend/modules/content/service.py` (lines 31-37, 329-337): Status enum and service wrappers
```31:37:backend/modules/content/service.py
class UnitStatus(str, Enum):
    """Valid unit statuses for creation flow tracking."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
```
```329:337:backend/modules/content/service.py
def get_units_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]:
    """Get units filtered by status."""
    arr = self.repo.get_units_by_status(status=status, limit=limit, offset=offset)
    return [self.UnitRead.model_validate(u) for u in arr]

def update_unit_status(self, unit_id: str, status: str, error_message: str | None = None, creation_progress: dict[str, Any] | None = None) -> ContentService.UnitRead | None:
    """Update unit status and return the updated unit, or None if not found."""
    updated = self.repo.update_unit_status(unit_id=unit_id, status=status, error_message=error_message, creation_progress=creation_progress)
    return self.UnitRead.model_validate(updated) if updated else None
```
- `backend/modules/content_creator/routes.py` (lines 56-72): New mobile creation endpoint
```56:72:backend/modules/content_creator/routes.py
@router.post("/units", response_model=MobileUnitCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_unit_from_mobile(request: MobileUnitCreateRequest, service: ContentCreatorService = Depends(get_content_creator_service)) -> MobileUnitCreateResponse:
  ...
  result = await service.create_unit_from_mobile(topic=request.topic, difficulty=request.difficulty, target_lesson_count=request.target_lesson_count)
  ...
  return MobileUnitCreateResponse(unit_id=result.unit_id, status=result.status, title=result.title)
```
- `backend/server.py` (lines 133-137): Routes registered in FastAPI
```133:137:backend/server.py
# Include modular routers
app.include_router(learning_session_router, tags=["Learning Sessions"])
app.include_router(catalog_router, tags=["Catalog"])
app.include_router(content_creator_router, tags=["Content Creator"])
app.include_router(admin_router, tags=["Admin"])
```

**Implementation reasoning:** Status is modeled end-to-end, and mobile creation API is exposed and registered. Repo/service support status updates and queries, and the migration/bounds are in place.

**Confidence level:** ✅ High
**Concerns:** None for these pieces.

### Frontend: Status handling and polling
**Files involved:**
- `mobile/modules/catalog/models.ts` (lines 343-361, 406-429): Status types, API wire model, and DTO mapping including `creation_progress` and `error_message`
```343:361:mobile/modules/catalog/models.ts
export type UnitStatus = 'draft' | 'in_progress' | 'completed' | 'failed';
...
export interface UnitCreationResponse {
  readonly unitId: string;
  readonly status: UnitStatus;
  readonly title: string;
}
```
```406:429:mobile/modules/catalog/models.ts
export function toUnitDTO(api: ApiUnitSummary): Unit {
  const difficulty = (api.difficulty as Difficulty) ?? 'beginner';
  const status = (api.status as UnitStatus) ?? 'completed';

  return {
    id: api.id,
    title: api.title,
    description: api.description,
    difficulty,
    lessonCount: api.lesson_count,
    difficultyLabel: formatDifficultyLevel(difficulty),
    targetLessonCount: api.target_lesson_count ?? null,
    generatedFromTopic: !!api.generated_from_topic,
    status,
    creationProgress: api.creation_progress || null,
    errorMessage: api.error_message || null,
    statusLabel: formatUnitStatusLabel(status),
    isInteractive: status === 'completed',
    progressMessage: formatUnitProgressMessage(
      status,
      api.creation_progress,
      api.error_message
    ),
  };
}
```
- `mobile/modules/catalog/queries.ts` (lines 129-135): Poll units list when any unit is in progress
```129:135:mobile/modules/catalog/queries.ts
refetchInterval: data => {
  // If any unit is in progress, poll every 5 seconds
  // Otherwise, don't poll automatically
  const hasInProgressUnit =
    Array.isArray(data) && data.some(unit => unit.status === 'in_progress');
  return hasInProgressUnit ? 5000 : false;
},
```

**Implementation reasoning:** The UI relies on status fields from the units listing to drive polling and interaction state.

**Confidence level:** ⚠️ Medium
**Concerns:** Backend units list response currently omits status fields (see below), breaking polling and state.

### API Gap: Units list does not include status/progress/error
**Files involved:**
- `backend/modules/catalog/service.py` (lines 86-99): `UnitSummary` lacks status/progress fields
```86:99:backend/modules/catalog/service.py
class UnitSummary(BaseModel):
    """DTO for unit summary in browsing lists."""

    id: str
    title: str
    description: str | None = None
    difficulty: str
    lesson_count: int
    # New fields surfaced for admin list view
    target_lesson_count: int | None = None
    generated_from_topic: bool = False
    # Flow type used to generate the unit
    flow_type: str = "standard"
```
- `backend/modules/catalog/routes.py` (lines 123-131): Units endpoint returns `UnitSummary` list
```123:131:backend/modules/catalog/routes.py
@router.get("/units", response_model=list[UnitSummary])
def browse_units(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    catalog: CatalogService = Depends(get_catalog_service),
) -> list[UnitSummary]:
    """Browse learning units with simple metadata and lesson counts."""
    return catalog.browse_units(limit=limit, offset=offset)
```

**Implementation reasoning:** The backend listing response model does not carry `status`, `creation_progress`, or `error_message`, so the frontend cannot reflect accurate creation state nor poll correctly.

**Confidence level:** ❌ Low (requirement not met)
**Concerns:** Must extend `UnitSummary`, service mapping, and route response_model to include status fields to satisfy the user story.

## Overall Assessment

### ✅ Requirements Fully Met
- Mobile creation form with topic, difficulty, and target lesson count; validation and UX
- Background unit creation started immediately via asyncio; progress and final status updates
- New unit appears immediately at top via optimistic update
- Retry and dismiss actions for failed units with end-to-end API support
- Disabled interaction until `status === 'completed'` (based on data availability)

### ⚠️ Requirements with Concerns
- In-progress units showing clear status and automatic polling depend on backend including status; currently missing in units list payload
- Completed units becoming interactive relies on accurate status from list endpoint
- Failure state visibility on list similarly depends on list payload
- Pull-to-refresh behavior is stubbed (`onRefresh={() => {}}`) and not wired to refetch
- Resilience to brief network interruptions is not explicitly covered (no offline queue or retry strategy at creation time)

### ❌ Requirements Not Met
- Extend `GET /api/v1/catalog/units` to include `status`, `creation_progress`, and `error_message` fields (as per spec)
- Unit tests for flow engine background execution (spec mentions adding them; not found beyond base tests)

## Recommendations
- Backend catalog:
  - Add `status: str`, `creation_progress: dict | None`, `error_message: str | None` to `UnitSummary` and to the JSON response.
  - Map these from `ContentService.UnitRead` in `CatalogService.browse_units`.
  - Update `response_model` in `catalog/routes.py` accordingly.
- Frontend:
  - Ensure `onRefresh` of `FlatList` triggers a `refetch` of `useCatalogUnits`.
  - Consider showing a subtle toast/snackbar on background failure when the user is on the list.
- QA:
  - Add tests covering background execution path (success/failure) and status transitions.
  - Add mobile tests asserting polling continues while any unit is `in_progress` and stops on completion.
