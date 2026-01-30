# Maintenance Mode

This module provides a maintenance mode feature for the City Infrastructure Platform.

## Features

- **Database-driven**: Maintenance mode status is stored in the database, allowing admin users to toggle it on/off
- **Single-row constraint**: The database table enforces that only one configuration row can exist
- **Multilingual messages**: Support for Finnish, Swedish, and English maintenance messages
- **Superuser access**: Superusers can still access admin pages when maintenance mode is active
- **503 Status Code**: Returns proper HTTP 503 Service Unavailable status when blocking requests
- **Performance**: Middleware caches the maintenance mode status for 10 seconds to avoid excessive database queries

## Components

### Model: `MaintenanceMode`
- Located in `maintenance_mode/models.py`
- Single row enforced by database constraint (`id=1`)
- Fields:
  - `is_active`: Boolean to enable/disable maintenance mode
  - `message_fi`, `message_en`, `message_sv`: Multilingual messages
  - `updated_at`: Timestamp of last update
  - `updated_by`: User who last updated the configuration

### Middleware: `MaintenanceModeMiddleware`
- Located in `maintenance_mode/middleware.py`
- Blocks all requests when maintenance mode is active
- Exceptions:
  - Admin login page (`/admin/login/`) is accessible to everyone (so superusers can log in)
  - Authenticated superusers can access all `/admin/` URLs (with or without language prefix)
- Returns 503 status with maintenance page template
- Caches database check for 10 seconds for performance

### Admin: `MaintenanceModeAdmin`
- Located in `maintenance_mode/admin.py`
- Prevents adding multiple instances
- Prevents deletion of the configuration
- Automatically sets `updated_by` to the current user
- Redirects list view to change form (since only one instance exists)

### Template: `maintenance.html`
- Located in `cityinfra/templates/maintenance_mode/maintenance.html`
- Responsive design
- Displays maintenance message in the user's language

## Installation

The maintenance mode is already configured in the project:

1. **App added to `INSTALLED_APPS`**:
   ```python
   "maintenance_mode.apps.MaintenanceModeConfig",
   ```

2. **Middleware added to `MIDDLEWARE`** (after authentication):
   ```python
   "maintenance_mode.middleware.MaintenanceModeMiddleware",
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate maintenance_mode
   ```

## Usage

### Enable/Disable Maintenance Mode

1. Log in to Django admin as a staff user
2. Navigate to "Maintenance Mode" section
3. Toggle the "Maintenance mode active" checkbox
4. Optionally customize the messages in Finnish, Swedish, or English
5. Save the changes

### Programmatic Access

```python
from maintenance_mode.models import MaintenanceMode

# Get the maintenance mode instance
maintenance = MaintenanceMode.get_instance()

# Enable maintenance mode
maintenance.is_active = True
maintenance.save()

# Disable maintenance mode
maintenance.is_active = False
maintenance.save()

# Update message
maintenance.message_en = "We'll be back soon!"
maintenance.save()
```

## Technical Details

### Database Constraint

The model uses a `CheckConstraint` to ensure only one row exists:

```python
constraints = [
    models.CheckConstraint(
        check=models.Q(id=1),
        name="only_one_maintenance_mode_row",
    ),
]
```

### Middleware Placement

The middleware is placed after `AuthenticationMiddleware` to ensure `request.user` is available for checking admin status.

### Performance Optimization

The middleware caches the maintenance mode status for 10 seconds to avoid database queries on every request. This means there may be up to a 10-second delay when toggling maintenance mode on/off.

## Testing

To test the maintenance mode:

1. Enable maintenance mode in the admin
2. Try accessing the site in a non-admin browser/session - you should see the maintenance page with 503 status
3. Log in as a superuser and access `/admin/` - it should work normally
4. Disable maintenance mode and verify normal operation resumes

## Notes

- The maintenance mode configuration **cannot be deleted** through the admin interface
- Only **one configuration row** can exist in the database
- Superusers can always access admin pages, even when maintenance mode is active
- The maintenance message is displayed based on the user's language preference (fi/en/sv)

## Deployment Configuration

The maintenance mode whitelist can be customized per environment using Kubernetes ConfigMaps or environment variables.

### Environment Variables

The following environment variables control which paths remain accessible during maintenance mode:

- **MAINTENANCE_MODE_HEALTH_CHECKS**: Comma-separated list of health check endpoints (default: `healthz,readiness`)
- **MAINTENANCE_MODE_AUTH_PREFIXES**: Comma-separated list of authentication path prefixes (default: `ha,auth`)
- **MAINTENANCE_MODE_ADMIN_PATHS**: Comma-separated list of admin-related paths (default: `admin/jsi18n`)
- **MAINTENANCE_MODE_LANGUAGES**: Comma-separated list of supported language codes (default: `fi,sv,en`)

### Kubernetes ConfigMap Example

#### Production Environment (Minimal Whitelist)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: city-infrastructure-platform-config
  namespace: production
data:
  # Use defaults - only essential paths accessible during maintenance
  MAINTENANCE_MODE_HEALTH_CHECKS: ${MAINTENANCE_MODE_HEALTH_CHECKS:-healthz,readiness}
  MAINTENANCE_MODE_AUTH_PREFIXES: ${MAINTENANCE_MODE_AUTH_PREFIXES:-ha,auth}
  MAINTENANCE_MODE_ADMIN_PATHS: ${MAINTENANCE_MODE_ADMIN_PATHS:-admin/jsi18n}
  MAINTENANCE_MODE_LANGUAGES: ${MAINTENANCE_MODE_LANGUAGES:-fi,sv,en}
```

#### Development/Test Environment (Extended Whitelist)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: city-infrastructure-platform-config
  namespace: dev
data:
  # Allow additional paths for API debugging during maintenance
  MAINTENANCE_MODE_HEALTH_CHECKS: ${MAINTENANCE_MODE_HEALTH_CHECKS:-healthz,readiness}
  MAINTENANCE_MODE_AUTH_PREFIXES: ${MAINTENANCE_MODE_AUTH_PREFIXES:-ha,auth,swagger,redoc,openapi.yaml}
  MAINTENANCE_MODE_ADMIN_PATHS: ${MAINTENANCE_MODE_ADMIN_PATHS:-admin/jsi18n}
  MAINTENANCE_MODE_LANGUAGES: ${MAINTENANCE_MODE_LANGUAGES:-fi,sv,en}
```

### Why Each Whitelist Category Exists

**Health Checks** (`healthz`, `readiness`):
- Required for Kubernetes liveness and readiness probes
- Without these, pods would be marked unhealthy and continuously restarted during maintenance
- Must always be accessible for production stability

**Authentication Prefixes** (`ha`, `auth`):
- `ha/`: Helsinki Users (helusers) authentication endpoints
- `auth/`: Social auth (social-auth-app-django) OIDC/OAuth flow
- Critical for admin users to log in via Tunnistamo during maintenance mode
- Includes login initiation, OAuth callbacks, and logout endpoints

**Admin Paths** (`admin/jsi18n`):
- Django admin JavaScript internationalization catalog
- Required for translated UI text on admin login page
- Without this, login page may not display properly

**Supported Languages** (`fi`, `sv`, `en`):
- Determines which language prefixes are recognized in URLs
- Used for both path whitelisting and language detection
- Must match Django's LANGUAGES setting

### Use Cases

**Adding API documentation access in staging:**
```bash
# In staging ConfigMap
MAINTENANCE_MODE_AUTH_PREFIXES: "ha,auth,swagger,redoc"
```

**Allowing specific monitoring endpoints:**
```bash
# Custom health check paths
MAINTENANCE_MODE_HEALTH_CHECKS: "healthz,readiness,metrics,status"
```

**Restricting languages in region-specific deployment:**
```bash
# Finland-only deployment
MAINTENANCE_MODE_LANGUAGES: "fi"
```
