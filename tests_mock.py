from unittest.mock import AsyncMock\nfrom app.database.connection import db\ndb.connect = AsyncMock()\ndb.disconnect = AsyncMock()
