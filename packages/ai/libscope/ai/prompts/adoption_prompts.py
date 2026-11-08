"""
Prompt templates for adoption analysis.
"""

ADOPTION_ANALYSIS_PROMPT = """Analyze the real-world adoption evidence for package '{name}':

PACKAGE ADOPTION TELEMETRY:
- Ecosystem: {ecosystem}
- Monthly Downloads: {monthly_downloads:,}
- Verified External Manifest Usages: {verified_adoptions}
- Sample Discovered Adopters:
{adopters_sample}
- Package Category: {category}

Analyze whether this package demonstrates genuine independent ecosystem adoption or if the downloads are disproportionately inflated by CI/CD mirrors and build automation. Adhere strictly to the requested schema.
"""

