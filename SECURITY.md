# Security Policy

The LibScope team takes the security of our platform, our users, and the open-source software ecosystem very seriously.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within LibScope, please do **NOT** open a public issue.

Instead, please report it privately:

1. **Email**: Send detailed advisory information to `security@libscope.dev`.
2. **GitHub Security Advisory**: Open a private draft security advisory via the GitHub repository's Security tab.

### Please Include:
- A description of the issue and potential impact
- Affected version(s)
- Step-by-step reproduction steps or a minimal proof of concept
- Any potential remediations or patch suggestions

### Our Response Process
- We will acknowledge receipt of your vulnerability report within 48 hours.
- We will provide an initial assessment and timeline within 5 business days.
- We coordinate fix development and release a patch along with public attribution (unless anonymity is requested).

## Security Architecture in LibScope

LibScope incorporates rigorous defensive measures:
- **API Access Control**: Production deployments require `LIBSCOPE_API_KEY` for analysis, report-generation, and demo-seeding requests. The dashboard accepts an operator-provided key in Settings and sends it as an `Authorization: Bearer` header from memory; it is not persisted to browser storage. Never embed the server key in static assets or source control.
- **Transport Security**: Production deployments must terminate TLS at a trusted reverse proxy before bearer credentials are sent.
- **Request Throttling**: Expensive routes have a process-local rate limit. Multi-worker or multi-instance deployments should enforce a shared limit at the ingress or API gateway.
- **SSRF Protection**: LibScope-managed provider requests validate resolved public IPs and reject loopback, private IPv4/IPv6, and cloud metadata hostnames (`169.254.169.254`, `metadata.google.internal`). Custom OpenAI-compatible and Azure AI endpoints are validated before use.
- **Untrusted Content Sanitization**: README excerpts, release notes, and issue comments are tagged as untrusted and scrubbed of prompt injection payloads before passing to AI interpretation layers.
- **Deterministic Separation**: Mathematical calculations, trend metrics, and scores are separated completely from AI interpretation models, preventing hallucinations from corrupting empirical findings.
