<div align="center">

# Security Policy

</div>

---

## Supported Versions

| Version | Supported |
|---|---|
| `0.1.x` (current) | ✅ Actively maintained |
| Earlier releases | ❌ No longer supported |

---

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

If you discover a security issue, report it privately so it can be addressed before public disclosure.

### How to report

1. **Email** — send details to the maintainer at the address listed on their GitHub profile.
2. **Subject line** — use `[SECURITY] Network Monitoring Utility — <short description>`.
3. Include in your report:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (optional)

### What to expect

| Timeline | Action |
|---|---|
| Within **48 hours** | Acknowledgement of your report |
| Within **7 days** | Initial assessment and severity rating |
| Within **30 days** | Patch released (critical issues may be faster) |

You will be credited in the release notes unless you prefer to remain anonymous.

---

## Scope

The following are **in scope** for security reports:

- Injection vulnerabilities (SQL, command, etc.)
- Unauthenticated access to sensitive API endpoints
- Insecure storage of data in the SQLite database
- Dependencies with known CVEs that affect this project

The following are **out of scope**:

- Vulnerabilities in operating system or network infrastructure
- Denial-of-service attacks requiring physical access
- Social engineering

---

## Security Considerations for Deployment

This utility is designed for **trusted internal networks**. Before exposing it to the internet:

- Place the FastAPI backend behind a reverse proxy (nginx, Caddy) with TLS.
- Add authentication (API keys or OAuth2) to the `/nodes` and `/logs` endpoints.
- Run the application as a non-root user — ICMP checks use unprivileged UDP mode (`privileged=False`) and do not require root.
- Restrict database file permissions (`network_monitor.db`) to the application user only.
