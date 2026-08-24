import unittest
import sys

import tests.test_phase1_validation as t1
import tests.test_phase2_ingestion as t2
import tests.test_phase3_assets as t3
import tests.test_phase4_automation as t4
import tests.test_phase5_discovery as t5
import tests.test_phase6_application_pipeline as t6
import tests.test_phase7_career_intelligence as t7

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(t1))
    suite.addTests(loader.loadTestsFromModule(t2))
    suite.addTests(loader.loadTestsFromModule(t3))
    suite.addTests(loader.loadTestsFromModule(t4))
    suite.addTests(loader.loadTestsFromModule(t5))
    suite.addTests(loader.loadTestsFromModule(t6))
    suite.addTests(loader.loadTestsFromModule(t7))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print(f"\n==========================================")
    print(f"TOTAL TESTS RUN: {result.testsRun}")
    print(f"FAILURES: {len(result.failures)}")
    print(f"ERRORS: {len(result.errors)}")
    print(f"==========================================")

    sys.exit(0 if result.wasSuccessful() else 1)
