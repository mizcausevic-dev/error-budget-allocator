from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.services.allocator_service import build_service


class ErrorBudgetAllocatorTests(unittest.TestCase):
    def test_summary_shape(self) -> None:
        summary = build_service().summary()
        self.assertGreaterEqual(summary["serviceCount"], 5)
        self.assertGreaterEqual(summary["ownerCount"], 4)
        self.assertIn("leadRecommendation", summary)

    def test_allocation_queue_has_hottest_service_first(self) -> None:
        queue = build_service().allocation_queue()
        self.assertGreaterEqual(queue[0]["riskScore"], queue[-1]["riskScore"])
        self.assertIn(queue[0]["verdict"], {"watch", "breach"})

    def test_service_lookup_api(self) -> None:
        client = TestClient(app)
        response = client.get("/api/services/svc-checkout-core")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Checkout Core")


if __name__ == "__main__":
    unittest.main()
