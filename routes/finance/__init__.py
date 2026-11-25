"""Finance HTTP API: connection, rules, reports and Ask.

Importing handlers registers them on the shared blueprint exactly once.
"""

from .shared import blueprint
from . import connection, rules, reports, chat
