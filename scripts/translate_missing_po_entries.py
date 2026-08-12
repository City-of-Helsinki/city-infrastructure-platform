#!/usr/bin/env python3
"""Translate missing entries in Django .po files using the Anthropic API.

Finds all untranslated entries in the Finnish and Swedish .po files under
``locale/`` and fills them in using Claude. Each translated entry is tagged
with a ``# AI translation - needs human review`` comment so that human
translators can easily find and verify the output.

Usage::

    uv run scripts/translate_missing_po_entries.py [--lang fi] [--lang sv]

Requirements:
    - ``polib`` (``uv add polib`` or ``pip install polib``)
    - ``anthropic`` (``uv add anthropic`` or ``pip install anthropic``)
    - ``ANTHROPIC_API_KEY`` environment variable set

"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import anthropic
import polib

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCALE_DIR = REPO_ROOT / "locale"
AI_COMMENT = "AI translation - needs human review"
BATCH_SIZE = 30
MODEL = "claude-opus-4-5"

LANGUAGE_NAMES: dict[str, str] = {
    "fi": "Finnish",
    "sv": "Swedish",
}

DOMAIN_CONTEXT = """
This is a Django admin interface for managing city infrastructure in Helsinki:
traffic signs (plan and real), road markings, barriers, signposts, city
furniture (benches, bins, etc.), mount types, lifecycle statuses, and related
administrative/metadata concepts.

Finnish terminology reference (from existing translations):
  Plan = Suunnitelma, Real = Toteuma, Traffic sign = Liikennemerkki,
  Road marking = Tiemerkintä, Barrier = Sulkulaite, Mount = Kiinnike/Pylväs,
  Lifecycle = Elinkaari, Owner = Omistaja, Device type = Laitetyyppi,
  Installation = Asennus, Location = Sijainti, Color = Väri, Size = Koko.

Swedish terminology reference (from existing translations):
  Plan = Plan, Real = Implementering, Traffic sign = Trafikmärke,
  Road marking = Vägmarkering, Barrier = Spärranordning,
  Signpost = Lokaliseringsmärke, Mount = Fäste/Stolpe,
  Lifecycle = Livscykel, Owner = Ägare, Device type = Enhetstyp,
  Installation = Installation, Location = Plats/Läge.
"""

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_po_path(lang: str) -> Path:
    """Return the path to the .po file for the given language code.

    Args:
        lang (str): Language code, e.g. ``"fi"`` or ``"sv"``.

    Returns:
        Path: Absolute path to the ``django.po`` file.
    """
    return LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"


def translate_batch(client: anthropic.Anthropic, lang: str, msgids: list[str]) -> list[str]:
    """Translate a batch of English strings into the target language via Claude.

    Args:
        client (anthropic.Anthropic): Authenticated Anthropic client.
        lang (str): Target language code (``"fi"`` or ``"sv"``).
        msgids (list[str]): English source strings to translate.

    Returns:
        list[str]: Translated strings in the same order as *msgids*.

    Raises:
        ValueError: If the API response cannot be parsed as a JSON array with
            the expected number of items.
    """
    language_name = LANGUAGE_NAMES.get(lang, lang)
    numbered = "\n".join(f"{i + 1}. {text}" for i, text in enumerate(msgids))

    prompt = (
        f"You are a professional translator working on a city infrastructure management system.\n\n"
        f"Context:\n{DOMAIN_CONTEXT}\n\n"
        f"Translate the following {len(msgids)} English strings into {language_name}.\n"
        f"Return ONLY a JSON array of translated strings, in the same order, with no extra text.\n\n"
        f"{numbered}"
    )

    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    translations: list[str] = json.loads(raw)
    if len(translations) != len(msgids):
        raise ValueError(f"Expected {len(msgids)} translations, got {len(translations)}: {raw!r}")
    return translations


def translate_po_file(client: anthropic.Anthropic, lang: str) -> int:
    """Translate all missing entries in a single .po file.

    Args:
        client (anthropic.Anthropic): Authenticated Anthropic client.
        lang (str): Language code (``"fi"`` or ``"sv"``).

    Returns:
        int: Number of entries translated.
    """
    po_path = get_po_path(lang)
    if not po_path.exists():
        logger.warning("No .po file found for language %r at %s", lang, po_path)
        return 0

    po = polib.pofile(str(po_path))
    untranslated = po.untranslated_entries()

    if not untranslated:
        logger.info("[%s] No missing translations.", lang)
        return 0

    logger.info("[%s] Found %d untranslated entries.", lang, len(untranslated))
    translated_count = 0

    for batch_start in range(0, len(untranslated), BATCH_SIZE):
        batch = untranslated[batch_start : batch_start + BATCH_SIZE]
        msgids = [entry.msgid for entry in batch]

        logger.info(
            "[%s] Translating entries %d–%d of %d…",
            lang,
            batch_start + 1,
            batch_start + len(batch),
            len(untranslated),
        )

        translations = translate_batch(client, lang, msgids)

        for entry, translation in zip(batch, translations):
            entry.msgstr = translation
            if AI_COMMENT not in (entry.comment or ""):
                entry.comment = f"{AI_COMMENT}\n{entry.comment}" if entry.comment else AI_COMMENT

        translated_count += len(batch)

    po.save(str(po_path))
    logger.info("[%s] Saved %d translations to %s", lang, translated_count, po_path)
    return translated_count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv (list[str] | None): Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Translate missing .po entries using Claude.",
    )
    parser.add_argument(
        "--lang",
        action="append",
        choices=list(LANGUAGE_NAMES.keys()),
        dest="langs",
        metavar="LANG",
        help="Language code to process (may be repeated). Defaults to all languages.",
    )
    return parser.parse_args(argv)


def main() -> None:
    """Entry point: translate missing .po entries for the requested languages."""
    args = parse_args()
    langs = args.langs or list(LANGUAGE_NAMES.keys())

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    total = 0
    for lang in langs:
        total += translate_po_file(client, lang)

    logger.info("Done. Total entries translated: %d", total)


if __name__ == "__main__":
    main()
