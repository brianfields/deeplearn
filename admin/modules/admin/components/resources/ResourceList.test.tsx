import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ResourceList } from './ResourceList';
import type { ResourceSummary } from '@/modules/admin/models';

const pushMock = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
    prefetch: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
}));

vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: any) => (
    <a href={typeof href === 'string' ? href : '#'} {...rest}>
      {children}
    </a>
  ),
}));

describe('ResourceList', () => {
  beforeEach(() => {
    pushMock.mockReset();
  });

  it('highlights generated source resources with badge and open details action', () => {
    const resources: ResourceSummary[] = [
      {
        id: 'gen-1',
        resource_type: 'generated_source',
        filename: null,
        source_url: null,
        file_size: null,
        created_at: new Date('2024-01-01T00:00:00Z'),
        preview_text: 'Supplemental coverage details',
      },
    ];

    render(<ResourceList resources={resources} />);

    expect(screen.getByText('Generated Source')).toBeInTheDocument();
    const badge = screen.getByTestId('resource-type-generated_source');
    expect(badge).toHaveClass('bg-violet-100');
    expect(screen.getByRole('link', { name: /Open details/i })).toHaveAttribute('href', '/resources/gen-1');
  });

  it('falls back to default styling for unknown resource types', () => {
    const resources: ResourceSummary[] = [
      {
        id: 'custom-1',
        resource_type: 'custom_type',
        filename: 'lesson-notes.txt',
        source_url: 'https://example.com/resource',
        file_size: 2048,
        created_at: new Date('2024-02-02T00:00:00Z'),
        preview_text: 'Notes preview',
      },
    ];

    render(<ResourceList resources={resources} />);

    const badge = screen.getByTestId('resource-type-custom_type');
    expect(badge).toHaveClass('bg-gray-100');
    expect(screen.getByText('lesson-notes.txt')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Open source/i })).toHaveAttribute(
      'href',
      'https://example.com/resource'
    );
  });
});
