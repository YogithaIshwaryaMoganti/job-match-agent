"""Job Match & Shortlist Agent backend package.

Uses the OS trust store for TLS verification (via truststore) instead of only
the bundled certifi CA list — needed on networks that terminate TLS with a
corporate/proxy root certificate, harmless everywhere else.
"""

import truststore

truststore.inject_into_ssl()
