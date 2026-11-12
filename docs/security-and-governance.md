# Security and data governance

- Keep approved cohort files, `.env`, model artifacts, exports, note text, and audit records private. Git and Docker ignore files exclude common local sensitive artifacts.
- API-key comparison uses a constant-time comparison. Production refuses requests without a configured key; configure TLS and user-level authorization at the deployment boundary.
- API audit records contain event time, action, status, and model version only. Request notes and feature payloads are not written to the audit log. Error responses omit exception detail.
- Clinical-note processing requires an explicit `approved_deidentified` acknowledgement, limits input size, and does not persist note content.
- Cohort validation and monitoring payloads require the same acknowledgement and are not stored as rows.
- PostgreSQL queries are parameterized. Separate runtime and migration roles and grant only necessary access in a governed deployment.
- This prototype does not implement encryption at rest or TLS itself, user identity, role-based authorization, rate limiting, or legal/institutional approvals. Add these before processing any sensitive data.
- Never put restricted patient data in public repositories, public logs, screenshots, or public demo deployments.
