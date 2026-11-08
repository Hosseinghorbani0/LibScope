"""
Prompt templates for competitor package comparison.
"""

COMPETITOR_COMPARISON_PROMPT = """Analyze and compare the following software packages based on verified metrics collected by LibScope:

PACKAGES DATA:
{comparison_table}

FAIRNESS AND COMPARABILITY CONSTRAINTS:
- Do not equate raw download counts between packages if one is a low-level build dependency.
- Note any ecosystem differences.
- Contrast verified adoption in independent codebases against GitHub star popularity.

Synthesize an objective comparative report adhering to the requested schema.
"""

