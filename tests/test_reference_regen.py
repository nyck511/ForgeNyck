from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import forge_tui as upstream
from forge_tui_fixed import FixedForgeApp


class ReferenceRegenTests(TestCase):
    def bare_app(self):
        app = FixedForgeApp.__new__(FixedForgeApp)
        app.busy = False
        app.last_ask = "reforge from reference"
        app.messages = [
            {"role": "user", "content": "old request"},
            {"role": "assistant", "content": "old draft"},
        ]
        app.backend = SimpleNamespace(name="test-backend")
        app.model = "test-model"
        app.style_idx = 0
        app._info = Mock()
        return app

    def test_submit_reference_remembers_full_reference_state(self):
        app = self.bare_app()
        app._last_reference = None

        with patch.object(upstream.ForgeApp, "_submit_reference", autospec=True) as base_submit:
            FixedForgeApp._submit_reference(
                app,
                "REFERENCE BODY",
                mode="reforge",
                goal="new goal",
            )

        self.assertEqual(
            app._last_reference,
            {"ref": "REFERENCE BODY", "mode": "reforge", "goal": "new goal"},
        )
        base_submit.assert_called_once_with(
            app,
            "REFERENCE BODY",
            mode="reforge",
            goal="new goal",
        )

    def test_regen_replays_reference_instead_of_last_ask_label(self):
        app = self.bare_app()
        app._last_reference = {
            "ref": "REFERENCE BODY",
            "mode": "emulate",
            "goal": "retarget this",
        }
        app._submit_reference = Mock()
        app._submit_ask = Mock()

        FixedForgeApp.action_regen(app)

        app._submit_reference.assert_called_once_with(
            ref="REFERENCE BODY",
            mode="emulate",
            goal="retarget this",
        )
        app._submit_ask.assert_not_called()
        self.assertEqual(app.messages, [])

    def test_normal_ask_remains_normal_regen_target(self):
        app = self.bare_app()
        app.last_ask = "plain request"
        app._last_reference = None
        app._submit_reference = Mock()
        app._submit_ask = Mock()

        FixedForgeApp.action_regen(app)

        app._submit_ask.assert_called_once_with("plain request")
        app._submit_reference.assert_not_called()

    def test_new_normal_ask_clears_old_reference_state(self):
        app = self.bare_app()
        app._last_reference = {
            "ref": "OLD REFERENCE",
            "mode": "reforge",
            "goal": "",
        }

        with patch.object(upstream.ForgeApp, "_submit_ask", autospec=True) as base_submit:
            FixedForgeApp._submit_ask(app, "new plain request")

        self.assertIsNone(app._last_reference)
        base_submit.assert_called_once_with(app, "new plain request")


if __name__ == "__main__":
    import unittest

    unittest.main()
