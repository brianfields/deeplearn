# /backend/modules/admin/models.py
"""
Admin Module - Database Models

SQLAlchemy ORM models for admin-specific data (if any).
Currently, the admin module primarily aggregates data from other modules,
so it may not need its own database tables.
"""


# Note: Admin module primarily aggregates data from other modules
# via their public interfaces. If admin-specific tables are needed
# in the future (e.g., admin user sessions, audit logs), they would
# be defined here.

# Example of potential admin-specific model:
# class AdminSessionModel(Base):
#     """Admin user session tracking."""
#     __tablename__ = "admin_sessions"
#     # ... fields would go here
