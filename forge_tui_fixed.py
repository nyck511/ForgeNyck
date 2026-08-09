"""Compatibility entrypoint for Forge's TUI.

Keeps the upstream TUI intact while fixing regeneration after reference-driven
Emulate/Reforge runs. Ctrl+R now replays the original reference, mode and
optional retarget goal instead of degrading into a normal text request.
"""

from __future__ import annotations

from typing import Optional

import forge_tui as upstream


class FixedForgeApp(upstream.ForgeApp):
    """ForgeApp with reference-aware regeneration state."""

    def __init__(self) -> None:
        super().__init__()
        self._last_reference: Optional[dict[str, str]] = None

    def _submit_ask(self, val: str) -> None:
        # A normal ask becomes the new regeneration target, so any prior
        # reference-driven state must no longer win on Ctrl+R.
        self._last_reference = None
        super()._submit_ask(val)

    def _submit_reference(self, ref: str, mode: str = "emulate", goal: str = "") -> None:
        if mode == "send":
            self._last_reference = None
        else:
            self._last_reference = {
                "ref": ref,
                "mode": mode,
                "goal": goal,
            }
        super()._submit_reference(ref, mode=mode, goal=goal)

    def action_regen(self) -> None:
        if self.busy:
            self._info("[#FF9A1F]still drafting, hold on[/#FF9A1F]")
            return
        if not self.last_ask:
            self._info("nothing to regen yet")
            return

        # Drop the previous exchange so context doesn't carry the old draft.
        if self.messages and self.messages[-1]["role"] == "assistant":
            self.messages.pop()
        if self.messages and self.messages[-1]["role"] == "user":
            self.messages.pop()

        self._info(
            f"[dim]regen ({self.backend.name}/{self.model}, style={self.style})[/dim]"
        )

        if self._last_reference is not None:
            ref_state = dict(self._last_reference)
            self._submit_reference(**ref_state)
            return

        self._submit_ask(self.last_ask)


def main() -> int:
    FixedForgeApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
