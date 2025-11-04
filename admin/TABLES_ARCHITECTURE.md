# Admin Dashboard Tables Architecture

This document describes the unified table components used throughout the admin dashboard to reduce code duplication and maintain consistency.

## Overview

All tables in the admin dashboard use one of two reusable components:

1. **ExpandableTable** - For inline expandable rows
2. **DetailViewTable** - For tables that link to detail pages

Both components provide:
- Consistent styling and UX patterns
- Pagination support (DetailViewTable)
- Loading and error states
- Empty states with custom icons
- Type-safe column definitions
- Flexible custom cell rendering

## ExpandableTable

Use this component when clicking on a table row should expand inline details below it.

### Features
- Expandable/collapsible rows
- Pagination support
- Custom render functions for expanded content
- Loading, error, and empty states
- Smooth animations for expand/collapse toggle
- Click anywhere on the row to expand (including pressing Enter or Space for keyboard accessibility)

### Usage

```typescript
<ExpandableTable
  data={conversations}
  columns={[
    {
      key: 'title',
      label: 'Title',
      render: (item) => item.title,
    },
    {
      key: 'status',
      label: 'Status',
      render: (item) => <StatusBadge status={item.status} />,
    },
  ]}
  getRowId={(item) => item.id}
  renderExpandedContent={(item) => <ItemDetails item={item} />}
  isLoading={isLoading}
  error={error}
  emptyMessage="No items found"
  onRetry={() => refetch()}
/>
```

### Components Using ExpandableTable
- `ConversationsList` - Lists conversations with expandable transcript details
- `FlowRunsList` - Lists flow runs with expandable step information
- `LearningSessionsList` - Lists learning sessions with expandable progress details

## DetailViewTable

Use this component when clicking "View details" should navigate to a separate detail page.

### Features
- Click anywhere on the row to navigate to detail page
- Built-in pagination controls
- Custom render functions for cell content
- Loading, error, and empty states
- Works with and without pagination
- Keyboard accessible (Enter or Space to navigate)

### Usage

```typescript
<DetailViewTable
  data={users}
  columns={[
    {
      key: 'name',
      label: 'Name',
      render: (item) => item.name,
    },
    {
      key: 'email',
      label: 'Email',
      render: (item) => item.email,
    },
  ]}
  getRowId={(item) => item.id}
  getDetailHref={(item) => `/users/${item.id}`}
  isLoading={isLoading}
  error={error}
  emptyMessage="No users found"
  pagination={{
    currentPage,
    totalPages,
    totalCount,
    pageSize,
    hasNext,
  }}
  onPageChange={(page) => setPage(page)}
  onRetry={() => refetch()}
/>
```

### Components Using DetailViewTable
- `UserList` - Lists users with links to user detail pages
- `LLMRequestsList` - Lists LLM requests with links to request details
- `ResourceList` - Lists resources with links to resource details

## Column Definition

Both components use a similar column definition interface:

```typescript
interface Column<T> {
  readonly key: string;           // Unique identifier for the column
  readonly label: string;         // Header text
  readonly className?: string;    // Optional Tailwind classes
  readonly render: (item: T) => ReactNode;  // Cell content renderer
}
```

### Example with Complex Rendering

```typescript
{
  key: 'user_info',
  label: 'User',
  render: (item) => (
    <div>
      <div className="font-medium">{item.name}</div>
      <div className="text-xs text-gray-500">{item.email}</div>
    </div>
  ),
}
```

## Common Patterns

### Custom Status Badges

```typescript
{
  key: 'status',
  label: 'Status',
  render: (item) => <StatusBadge status={item.status} size="sm" />,
}
```

### Links Within Cells

```typescript
{
  key: 'user_id',
  label: 'User',
  render: (item) =>
    item.user_id ? (
      <Link href={`/users/${item.user_id}`} className="text-blue-600 hover:text-blue-500">
        {item.user_id}
      </Link>
    ) : (
      <span className="text-gray-500">—</span>
    ),
}
```

### Formatted Dates and Numbers

```typescript
{
  key: 'created_at',
  label: 'Created',
  render: (item) => formatDate(item.created_at),
},
{
  key: 'cost',
  label: 'Cost',
  render: (item) => formatCost(item.cost_estimate),
}
```

### Multi-line Cell Content

```typescript
{
  key: 'tokens',
  label: 'Tokens',
  render: (item) => (
    <div>
      <div>{formatTokens(item.total_tokens)}</div>
      {item.input_tokens && item.output_tokens && (
        <div className="text-xs text-gray-500">
          {formatTokens(item.input_tokens)} in / {formatTokens(item.output_tokens)} out
        </div>
      )}
    </div>
  ),
}
```

## Empty States

Both components support custom empty icons:

```typescript
const emptyIcon = (
  <svg className="h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="..." />
  </svg>
);

<ExpandableTable
  // ...
  emptyMessage="No items found"
  emptyIcon={emptyIcon}
/>
```

## Error Handling

Both components handle errors gracefully:

```typescript
<ExpandableTable
  // ...
  error={error}
  onRetry={() => refetch()}
/>
```

When an error occurs, a user-friendly error message is displayed with a retry button.

## Pagination

### DetailViewTable with Pagination

```typescript
<DetailViewTable
  // ...
  pagination={{
    currentPage: 1,
    totalPages: 5,
    totalCount: 100,
    pageSize: 20,
    hasNext: true,
  }}
  onPageChange={(page) => setPage(page)}
/>
```

### ExpandableTable with Manual Pagination

ExpandableTable doesn't include pagination controls, allowing custom pagination placement above/below the table.

## Styling

Both components use:
- Tailwind CSS for styling
- Consistent gray color palette (gray-50 to gray-900)
- Hover effects for better interactivity
- Responsive design with overflow-x-auto for small screens

## Adding New Tables

To create a new list component:

1. Choose between **ExpandableTable** (inline details) or **DetailViewTable** (separate page)
2. Define your column structure
3. Pass in your data and callbacks
4. Customize the empty state icon if desired

### Example: New ExpandableTable

```typescript
import { ExpandableTable, type ExpandableTableColumn } from '../shared/ExpandableTable';

export function MyList() {
  const { data, isLoading, error, refetch } = useMyData();

  const columns: ExpandableTableColumn<MyItem>[] = [
    // Define columns...
  ];

  return (
    <ExpandableTable
      data={data ?? []}
      columns={columns}
      getRowId={(item) => item.id}
      renderExpandedContent={(item) => <MyItemDetails item={item} />}
      isLoading={isLoading}
      error={error}
      emptyMessage="No items found"
      onRetry={() => refetch()}
    />
  );
}
```

## Benefits of This Architecture

1. **Code Reuse** - Eliminates duplicate table structure across components
2. **Consistency** - All tables follow the same patterns and styling
3. **Maintainability** - Changes to table behavior only need to be made in one place
4. **Type Safety** - Full TypeScript support for data and columns
5. **Flexibility** - Column rendering is fully customizable
6. **Accessibility** - Built-in support for loading, error, and empty states
