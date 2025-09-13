# Admin Dashboard

Administrative dashboard for monitoring and managing the DeepLearn platform.

## Features

- **Flow Management**: Monitor flow executions, drill down into steps, and view LLM request details
- **LLM Request Monitoring**: View detailed information about LLM requests and responses
- **Real-time Updates**: Live status updates and monitoring
- **Responsive Design**: Works on desktop and mobile devices

## Architecture

This is a Next.js 14 application using the App Router with a modular architecture:

- **Single Admin Module**: All admin functionality is contained in `modules/admin/`
- **Thin Page Components**: Pages in `app/` are thin routing layers that import from the admin module
- **React Query**: Server state management with caching and real-time updates
- **Zustand**: Client state management for UI state and filters
- **Tailwind CSS**: Utility-first CSS framework for styling

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
admin/
├── app/                    # Next.js App Router (thin routing)
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Dashboard overview
│   ├── flows/             # Flow management pages
│   └── llm-requests/      # LLM request pages
├── modules/admin/         # Single admin module (vertical slice)
│   ├── models.ts          # Type definitions and DTOs
│   ├── repo.ts            # HTTP client for API calls
│   ├── service.ts         # Business logic and data transformation
│   ├── queries.ts         # React Query hooks
│   ├── store.ts           # Zustand state management
│   └── components/        # All UI components
├── lib/                   # Shared utilities
└── types/                 # Global type definitions
```

## API Integration

The dashboard connects to the backend admin API at `/api/v1/admin/` with the following endpoints:

- `GET /flows` - List flow runs with pagination
- `GET /flows/{id}` - Get flow run details
- `GET /flows/{flowId}/steps/{stepId}` - Get flow step details
- `GET /llm-requests/{id}` - Get LLM request details

## Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Environment Variables

Create a `.env.local` file with:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
