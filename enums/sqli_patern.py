import re

SQLI_PATTERN = re.compile(
    r"(?i)("

    # Boolean-based
    r"\bor\b\s+\d+\s*=\s*\d+"
    r"|\bor\b\s+'[^']+'\s*=\s*'[^']+'"
    r"|\band\b\s+\d+\s*=\s*\d+"
    r"|\band\b\s+'[^']+'\s*=\s*'[^']+'"
    r"|\bor\s+true\b"
    r"|\bor\s+1=1\b"
    r"|\band\s+1=1\b"
    r"|\bor\s+'x'='x'"

    # Union-based
    r"|\bunion\b\s+(\ball\b\s+)?\bselect\b"
    r"|\bunion\b.*\bselect\b.*(from|version|user|database)"

    # Stacked queries
    r"|;.*\bdrop\b\s+\btable\b"
    r"|;.*\bshutdown\b"
    r"|;.*\bupdate\b"
    r"|;.*\binsert\b"
    r"|;.*\bdelete\b\s+from\b"

    # UPDATE/INSERT/DELETE patterns
    r"|\bupdate\b\s+\w+\s+\bset\b"
    r"|\binsert\b\s+into\b"
    r"|\bdelete\b\s+from\b"

    # SELECT patterns
    r"|\bselect\b.+\bfrom\b"
    r"|\bselect\b\s+\*?\s*from\b"

    # Error-based injections (MySQL)
    r"|\bextractvalue\s*\("
    r"|\bupdatexml\s*\("
    r"|\bgeometrycollection\s*\("
    r"|\bpolygon\s*\("
    r"|\bconvert\s*\("
    r"|\bconcat_ws\s*\("
    r"|\bbenchmark\s*\("
    r"|\brand\s*\("
    r"|\bif\s*\(.*sleep"

    # Time-based
    r"|\bsleep\s*\("
    r"|\bwaitfor\s+delay\b"

    # Comments (SQL)
    r"|--"
    r"|#"
    r"|/\*.*\*/"

    # Hex-based
    r"|0x[0-9a-fA-F]+"

    # SQL keywords unlikely in login
    r"|\border\b\s+by\b"
    r"|\bgroup\b\s+by\b"

    # Payload signs: `'='` trick
    r"|'[^']*'\s*=\s*'[^']*'"

    # URL encoded injections
    r"|%27"
    r"|%23"
    r"|%2F%2A"
    r"|%2D%2D"

    ")"
)