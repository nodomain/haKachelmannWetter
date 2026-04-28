# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 2.x     | ✅ Yes             |
| < 2.0   | ❌ No              |

## Reporting a Vulnerability

If you discover a security vulnerability in this integration, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please use [GitHub Security Advisories](https://github.com/nodomain/haKachelmannWetter/security/advisories/new) to report the vulnerability privately.

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response time

- Acknowledgment within 48 hours
- Fix within 7 days for critical issues

## Security considerations

This integration handles:

- **API keys** — stored in HA's encrypted config entries, redacted in diagnostics
- **Location data** — latitude/longitude stored in config entries
- **Network requests** — all API calls use HTTPS with 10s timeout

The integration does NOT:

- Store credentials in plain text files
- Make requests to third-party services other than `api.kachelmannwetter.com`
- Execute arbitrary code from API responses
- Expose API keys in logs (debug logging redacts sensitive data)
