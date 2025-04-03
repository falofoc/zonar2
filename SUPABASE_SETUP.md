# Supabase Integration for Amazon Tracker

This document provides instructions for setting up and configuring Supabase for the Amazon Tracker application.

## Overview

The application has been updated to use Supabase as the database backend instead of SQLite. Supabase is a PostgreSQL-based open-source Firebase alternative that provides a suite of tools for building serverless applications, including a real-time database, authentication, and more.

## Setting Up Supabase

1. Go to [Supabase](https://supabase.com/) and sign up for an account.

2. Create a new project:
   - Give it a name (e.g., "amazon-tracker")
   - Choose a strong password for the database
   - Select a region closest to your users

3. After the project is created, go to the project dashboard.

4. In the Supabase dashboard, navigate to "Settings" > "API" to get your API credentials:
   - **Project URL**: This will be your `SUPABASE_URL`
   - **anon public key**: This will be your `SUPABASE_KEY`
   - **service_role key**: This will be your `SUPABASE_SERVICE_KEY` (keep this very secure!)

5. Update your `.env` file with these credentials:
   ```
   SUPABASE_URL=your-project-url
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-role-key
   ```

## Setting Up Database Tables

You need to create the database tables in Supabase before running the application. There are two ways to do this:

### Option 1: Using the SQL Editor in Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to the "SQL Editor" section
3. Create a new query
4. Copy the contents of the `supabase_tables.sql` file from this project
5. Run the SQL script to create all the necessary tables

### Option 2: Creating Tables Through the Table Editor

Alternatively, you can manually create the tables through the Table Editor:

1. Go to the "Table Editor" section of your Supabase project
2. Click "Create a new table" for each of the following tables:

#### Users Table
- Name: `users`
- Columns:
  - `id`: integer (primary key, auto-increment)
  - `username`: varchar, unique, not null
  - `email`: varchar, unique, not null
  - `password_hash`: varchar, not null
  - `language`: varchar, default: 'ar'
  - `theme`: varchar, default: 'light'
  - `created_at`: timestamp, default: now()
  - `reset_token`: varchar, nullable
  - `reset_token_expiry`: timestamp, nullable
  - `verification_token`: varchar, nullable
  - `verification_token_expiry`: timestamp, nullable
  - `email_verified`: boolean, default: false
  - `is_admin`: boolean, default: false
  - `push_subscription`: text, nullable
  - `notifications_enabled`: boolean, default: false
  - `device_info`: text, nullable

#### Products Table
- Name: `products`
- Columns:
  - `id`: integer (primary key, auto-increment)
  - `url`: varchar, not null
  - `name`: varchar, not null
  - `custom_name`: varchar, nullable
  - `current_price`: float, not null
  - `target_price`: float, nullable
  - `image_url`: varchar, nullable
  - `price_history`: text, default: '[]'
  - `tracking_enabled`: boolean, default: true
  - `notify_on_any_change`: boolean, default: false
  - `last_checked`: timestamp, default: now()
  - `user_id`: integer, foreign key to users.id, not null
  - `created_at`: timestamp, default: now()

#### Notifications Table
- Name: `notifications`
- Columns:
  - `id`: integer (primary key, auto-increment)
  - `message`: varchar, not null
  - `read`: boolean, default: false
  - `created_at`: timestamp, default: now()
  - `user_id`: integer, foreign key to users.id, not null

## Migrating Existing Data

If you have existing data in SQLite that you want to migrate to Supabase, you can use the provided migration script:

```bash
python migrate_to_supabase.py
```

This script will:
1. Connect to your SQLite database
2. Fetch all data from users, products, and notifications tables
3. Insert the data into the corresponding Supabase tables

## Deployment Considerations

When deploying the application with Supabase:

1. Ensure your `.env` file contains the correct Supabase credentials.
2. Make sure your deployment environment has network access to Supabase (check firewall settings).
3. For enhanced security, consider using environment variables instead of the `.env` file for the production deployment.
4. Update any backup/maintenance scripts to account for the new database infrastructure.

## Troubleshooting

- **Connection Issues**: If you have trouble connecting to Supabase, verify your credentials and check if your network allows connections to the Supabase server.
- **Missing Tables**: If tables are missing, run the SQL script provided in `supabase_tables.sql` using the SQL Editor in the Supabase dashboard.
- **Migration Errors**: If data migration fails, check that your SQLite database schema matches what the migration script expects.

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/) 