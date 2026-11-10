"""Jev (TypeSafe) judge.

Jev answers atomic questions; the decision logic below is plain code over those answers.
Only the file name and its last two folder names are sent for a sample (never the full path),
and only the plugin name and format for a plugin.

Two transports return the same normalized answers: OpenRouter (OPENROUTER_API_KEY, standard
library only, the default) and the `typesafe-sdk` package (TYPESAFE_API_KEY, extra `jev`).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from . import (
    DRUM_TYPES,
    PLUGIN_CATEGORIES,
    JudgeError,
    PluginJudgment,
    SampleJudgment,
    verdict,
)

OPENROUTER_URL = "https://openrouter.ai/api/alpha/decisions"  # alpha path: keep it in one place
OPENROUTER_MODEL = "typesafe/jev-1.14"


class OpenRouterTransport:
    name = "openrouter"

    def __init__(self, api_key: str | None = None, url: str = OPENROUTER_URL, timeout: float = 30):
        key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise JudgeError("OPENROUTER_API_KEY is not set")
        self._key, self._url, self._timeout = key, url, timeout

    def ask(self, state: dict, questions: dict) -> dict:
        body = {"model": OPENROUTER_MODEL, "state": state, "questions": questions}
        req = urllib.request.Request(
            self._url,
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.load(resp)["answers"]
        except urllib.error.HTTPError as exc:
            raise JudgeError(f"Jev request failed: HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
            raise JudgeError(f"Jev request failed: {type(exc).__name__}") from exc


class SdkTransport:
    name = "typesafe-sdk"

    def __init__(self, client=None):
        try:
            from typesafe_sdk import TypeSafeClient
        except ImportError as exc:
            raise JudgeError("direct TypeSafe needs: pip install 'abletonlivemcp[jev]'") from exc
        self._client = client if client is not None else TypeSafeClient()

    def ask(self, state: dict, questions: dict) -> dict:
        from typesafe_sdk import Choice, Noul, TypeSafeError

        built = {
            k: Noul(instructions=q["instructions"])
            if q["type"] == "noul"
            else Choice(instructions=q["instructions"], criteria=q["criteria"])
            for k, q in questions.items()
        }
        try:
            r = self._client.system_one(state=state, questions=built)
        except TypeSafeError as exc:
            raise JudgeError(f"Jev request failed: {exc}") from exc
        return {
            **{k: {"noul": v.noul} for k, v in r.nouls.items()},
            **{k: {"choice": v.choice} for k, v in r.choices.items()},
        }


def default_transport():
    if os.environ.get("OPENROUTER_API_KEY"):
        return OpenRouterTransport()
    if os.environ.get("TYPESAFE_API_KEY"):
        return SdkTransport()
    raise JudgeError("set OPENROUTER_API_KEY (or TYPESAFE_API_KEY with the jev extra) to use Jev")


def _noul(text: str) -> dict:
    return {"type": "noul", "instructions": text}


def _choice(text: str, options: tuple[str, ...]) -> dict:
    return {"type": "choice", "instructions": text, "criteria": {o: None for o in options}}


class JevJudge:
    name = "jev"

    def __init__(self, transport=None):
        self._t = transport if transport is not None else default_transport()

    def _ask(self, state: dict, questions: dict) -> dict:
        answers = self._t.ask(state, questions)
        try:
            return {
                k: answers[k]["noul" if q["type"] == "noul" else "choice"]
                for k, q in questions.items()
            }
        except (KeyError, TypeError) as exc:
            raise JudgeError("Jev returned an answer in an unexpected shape") from exc

    def classify_sample(self, file_name: str, folders: list[str]) -> SampleJudgment:
        state = {"sample": {"file_name": file_name, "folders": folders[-2:]}}
        a = self._ask(
            state,
            {
                "one_shot": _noul(
                    "Is `sample` a single one-shot hit rather than a loop or phrase?"
                ),
                "is_drum": _noul("Is `sample` a drum or percussion sound?"),
                "drum_type": _choice("Which drum or percussion type is `sample`?", DRUM_TYPES),
            },
        )
        drum = a["drum_type"] if verdict(a["is_drum"]) == "yes" else None
        return SampleJudgment(
            file_name,
            verdict(a["one_shot"]),
            drum,
            self.name,
            {"one_shot_p": a["one_shot"], "is_drum_p": a["is_drum"]},
        )

    def classify_plugin(self, plugin_name: str, plugin_format: str | None) -> PluginJudgment:
        state = {"plugin": {"name": plugin_name, "format": plugin_format}}
        a = self._ask(
            state,
            {
                "fits": _noul("Does `plugin` fit one of the audio-production categories?"),
                "category": _choice("Which category is `plugin`?", PLUGIN_CATEGORIES),
            },
        )
        category = a["category"] if verdict(a["fits"]) == "yes" else None
        return PluginJudgment(plugin_name, category, self.name, {"fits_p": a["fits"]})
