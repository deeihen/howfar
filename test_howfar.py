import os
import subprocess
import sys
import tempfile
import unittest

import howfar

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "howfar.py")


class HowfarTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)
        os.environ["HOWFAR_FILE"] = self.path

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        del os.environ["HOWFAR_FILE"]

    def run_cmd(self, *args):
        howfar.main(list(args))
        return howfar.load()

    def test_percent_math(self):
        self.run_cmd("plan", "T", "A:1", "B:2")
        self.assertEqual(howfar.percent(howfar.load()), 0)
        self.assertEqual(howfar.percent(self.run_cmd("done", "A")), 33)
        self.assertEqual(howfar.percent(self.run_cmd("done", "B")), 100)

    def test_prefix_matching(self):
        self.run_cmd("plan", "T", "Write tests:50", "Write docs:30", "Ship:20")
        self.assertEqual(self.run_cmd("start", "ship")["current"], "Ship")
        self.assertEqual(self.run_cmd("start", "write t")["current"], "Write tests")
        with self.assertRaises(howfar.Error):
            self.run_cmd("start", "write")  # ambiguous prefix

    def test_exact_match_beats_prefix(self):
        self.run_cmd("plan", "T", "Build:50", "Build docs:50")
        self.assertEqual(self.run_cmd("start", "build")["current"], "Build")

    def test_done_clears_override_and_advances(self):
        self.run_cmd("plan", "T", "A:50", "B:50")
        self.assertEqual(howfar.percent(self.run_cmd("set", "150", "custom")), 100)
        state = self.run_cmd("done", "A")
        self.assertIsNone(state["override"])
        self.assertEqual(howfar.percent(state), 50)
        self.assertEqual(state["current"], "B")
        self.assertEqual(self.run_cmd("done", "B")["current"], "Finished")

    def test_eta_formatting(self):
        self.assertEqual(howfar.eta(100, 0), "estimating...")
        self.assertEqual(howfar.eta(100, 100), "done")
        self.assertEqual(howfar.eta(60, 50), "~1m 00s left")
        self.assertEqual(howfar.eta(10, 50), "~10s left")
        self.assertEqual(howfar.eta(3600, 50), "~1h 00m left")

    def test_version_flag(self):
        result = subprocess.run([sys.executable, SCRIPT, "--version"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), f"howfar {howfar.__version__}")

    def test_error_exit_code(self):
        for args in (["bogus"], ["show"], ["plan", "T", "A:x"]):
            result = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, args)
            self.assertIn("howfar:", result.stderr)
        subprocess.run([sys.executable, SCRIPT, "plan", "T", "A:1"], capture_output=True)
        result = subprocess.run([sys.executable, SCRIPT, "done", "nope"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown step", result.stderr)


if __name__ == "__main__":
    unittest.main()
