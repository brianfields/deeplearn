import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import { CatalogUnitCard } from '../CatalogUnitCard';
import type { Unit } from '../../../content/public';

function createUnit(overrides: Partial<Unit> = {}): Unit {
  return {
    id: 'unit-1',
    title: 'Sample Unit',
    description: 'Learn interesting things',
    difficulty: 'beginner',
    lessonCount: 4,
    difficultyLabel: 'Beginner',
    targetLessonCount: null,
    generatedFromTopic: false,
    learningObjectives: null,
    status: 'completed',
    creationProgress: null,
    errorMessage: null,
    statusLabel: 'Ready',
    isInteractive: true,
    progressMessage: 'Ready to learn',
    ownerUserId: 42,
    isGlobal: true,
    ownershipLabel: 'Shared Globally',
    isOwnedByCurrentUser: false,
    hasPodcast: false,
    podcastVoice: null,
    podcastDurationSeconds: null,
    artImageUrl: null,
    artImageDescription: null,
    cacheMode: 'minimal',
    downloadStatus: 'idle',
    downloadedAt: null,
    syncedAt: null,
    createdAt: null,
    updatedAt: null,
    ...overrides,
  };
}

describe('CatalogUnitCard', () => {
  it('renders add button when unit is not in My Units', () => {
    const unit = createUnit();
    const onAdd = jest.fn();
    const { getByTestId, queryByTestId } = render(
      <CatalogUnitCard
        unit={unit}
        isInMyUnits={false}
        onAdd={onAdd}
        onRemove={jest.fn()}
      />
    );

    const addButton = getByTestId('catalog-unit-add-button');
    expect(addButton).toBeTruthy();
    expect(queryByTestId('catalog-unit-remove-button')).toBeNull();

    fireEvent.press(addButton);
    expect(onAdd).toHaveBeenCalledWith(unit);
  });

  it('renders remove button when unit is already in My Units', () => {
    const unit = createUnit({ id: 'unit-2' });
    const onRemove = jest.fn();
    const { getByTestId, queryByTestId } = render(
      <CatalogUnitCard
        unit={unit}
        isInMyUnits={true}
        onAdd={jest.fn()}
        onRemove={onRemove}
      />
    );

    const removeButton = getByTestId('catalog-unit-remove-button');
    expect(removeButton).toBeTruthy();
    expect(queryByTestId('catalog-unit-add-button')).toBeNull();

    fireEvent.press(removeButton);
    expect(onRemove).toHaveBeenCalledWith(unit);
  });
});
