"""Prove Detective and Wesker resolve to the local checkouts, not the PyPI build.

Run once per session, through `just detective-resolution` (~/tools/Detective/AGENTS.md, "Standing invocation").
Both paths must print under ~/tools/.
"""

import Detective
import Wesker

print("Detective ->", Detective.__file__)
print("Wesker    ->", Wesker.__file__)
