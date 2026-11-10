"""Jev (TypeSafe) judge. Importing this module requires the optional `typesafe-sdk` package.

Jev answers atomic questions; the decision logic below is plain code over those answers.
Only the file name and its folder names are sent for a sample (never the full path), and only
the plugin name and format for a plugin.
"""

from __future__ import annotations

from typesafe_sdk import Choice, Noul, TypeSafeClient, TypeSafeError

from . import (
    DRUM_TYPES,
    PLUGIN_CATEGORIES,
    JudgeError,
    PluginJudgment,
    SampleJudgment,
    verdict,
)


class JevJudge:
    name = "jev"

    def __init__(self, client=None):
        # TypeSafeClient() reads TYPESAFE_API_KEY itself; a test double can be injected.
        self._client = client if client is not None else TypeSafeClient()

    def _ask(self, state, questions):
        try:
            return self._client.system_one(state=state, questions=questions)
        except TypeSafeError as exc:
            raise JudgeError(f"Jev request failed: {exc}") from exc

    def classify_sample(self, file_name: str, folders: list[str]) -> SampleJudgment:
        state = {"sample": {"file_name": file_name, "folders": folders[-2:]}}
        r = self._ask(
            state,
            {
                "one_shot": Noul(
                    instructions="Is `sample` a single one-shot hit rather than a loop or phrase?"
                ),
                "is_drum": Noul(instructions="Is `sample` a drum or percussion sound?"),
                "drum_type": Choice(
                    instructions="Which drum or percussion type is `sample`?",
                    criteria={name: None for name in DRUM_TYPES},
                ),
            },
        )
        one_shot_p = r.nouls["one_shot"].noul
        is_drum_p = r.nouls["is_drum"].noul
        drum = r.choices["drum_type"].choice if verdict(is_drum_p) == "yes" else None
        return SampleJudgment(
            file_name,
            verdict(one_shot_p),
            drum,
            self.name,
            {"one_shot_p": one_shot_p, "is_drum_p": is_drum_p},
        )

    def classify_plugin(self, plugin_name: str, plugin_format: str | None) -> PluginJudgment:
        state = {"plugin": {"name": plugin_name, "format": plugin_format}}
        r = self._ask(
            state,
            {
                "fits": Noul(
                    instructions="Does `plugin` fit one of the audio-production categories?"
                ),
                "category": Choice(
                    instructions="Which category is `plugin`?",
                    criteria={name: None for name in PLUGIN_CATEGORIES},
                ),
            },
        )
        fits_p = r.nouls["fits"].noul
        category = r.choices["category"].choice if verdict(fits_p) == "yes" else None
        return PluginJudgment(plugin_name, category, self.name, {"fits_p": fits_p})
