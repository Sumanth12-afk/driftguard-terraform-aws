# InfraSync Drift Dashboard (Optional)

This directory is reserved for an optional Next.js + Tailwind CSS dashboard that visualizes drift history stored in DynamoDB.

## Getting Started

1. Initialize the app:
   ```bash
   npx create-next-app@latest frontend --typescript --eslint
   cd frontend
   npm install @aws-sdk/client-dynamodb @aws-sdk/lib-dynamodb
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

2. Configure environment variables in `.env.local`:
   ```
   NEXT_PUBLIC_REGION=ap-south-1
   DRIFT_HISTORY_TABLE=infra-sync-drift-guard-drift-history
   ```

3. Implement API routes under `frontend/pages/api/` to query DynamoDB and expose aggregated metrics.

4. Build Tailwind components under `frontend/components/` to render drift tables, trend charts, and alert metrics.

This optional module is not required for the core drift detection workflow but provides a foundation for operational dashboards.

