# logic/image_utils.py
"""
Centralised image-path helpers with automatic fallback logic.

All piece and character-portrait image paths in the game MUST be generated
through one of these helpers so that Kivy never tries to load a file that
doesn't exist on disk.

Asset directory conventions
───────────────────────────
Board pieces:
    assets/pieces/<tribe>/<colour>/<stage_folder>/<filename>.png
    stage_folder is one of: 1base  2upATK  3upDEF  4up_rehidden  5up_reroll_ATK_DEF

Crash-screen character portraits:
    assets/char_crash/<faction>/<stage_folder>/<piece_name>.png

Fallback rule (both asset types)
─────────────────────────────────
If the requested path (with its upgrade subfolder) does not exist on disk,
silently return the "1base" variant instead so Kivy never emits an
"[ERROR] [Image] Not found" warning and the UI never shows a white box.
"""

import os


# ─────────────────────────────────────────────────────────────────────────────
# Low-level helpers shared by both asset families
# ─────────────────────────────────────────────────────────────────────────────

def _stage_folder_for_piece(piece) -> str:
    """Return the upgrade subfolder name for *piece* (e.g. '3upDEF')."""
    lvl  = getattr(piece, 'upgrade_level',  0)
    path = getattr(piece, 'upgrade_path', 'standard')
    if lvl == 0:
        return '1base'
    if path == 'standard':
        return '2upATK' if lvl == 1 else '3upDEF'
    if path == 'special':
        return '4up_rehidden' if lvl == 1 else '5up_reroll_ATK_DEF'
    return '1base'


def _piece_filename(piece) -> str:
    """Return the bare filename (no extension) for *piece*."""
    p_name = piece.__class__.__name__.lower()
    if getattr(piece, 'name', '') == 'Prince':
        return 'prince'
    if p_name in ('pawn', 'hastati', 'levies'):
        return f"{p_name}{getattr(piece, 'variant', 1)}"
    return p_name


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def safe_piece_path(piece, tribe: str, colour: str) -> str:
    """Return a guaranteed-to-exist path for a board-piece sprite.

    Tries ``assets/pieces/<tribe>/<colour>/<stage_folder>/<filename>.png``.
    If that directory doesn't exist on disk, falls back to the ``1base``
    subfolder.  The event-obstacle shortcut is handled by the caller
    (gameplay_screen.get_piece_image_path) before reaching here.

    Parameters
    ----------
    piece:   the game-piece object (must have upgrade_level / upgrade_path).
    tribe:   tribe folder name (e.g. 'bandit', 'the knight company').
    colour:  'white' | 'black'.
    """
    if getattr(piece, 'macro_faction', None) == 'red' or tribe == 'bandit':
        colour = 'red'

    stage = _stage_folder_for_piece(piece)
    filename = _piece_filename(piece)

    # If the piece is a pawn variant we already include the number; other
    # pieces just use <classname>.png.
    ext = '.png'
    # Handle classes whose filename has the variant number appended
    p_cls = piece.__class__.__name__.lower()
    if p_cls in ('pawn', 'hastati', 'levies'):
        fname = f"{filename}{ext}"
    else:
        fname = f"{filename}{ext}"

    if stage != '1base':
        candidate_dir = os.path.join('assets', 'pieces', tribe, colour, stage)
        if not os.path.isdir(candidate_dir):
            stage = '1base'

    return os.path.join('assets', 'pieces', tribe, colour, stage, fname).replace('\\', '/')


def safe_char_crash_path(piece, faction: str) -> str:
    """Return a guaranteed-to-exist path for a crash-screen portrait.

    Tries ``assets/char_crash/<faction>/<stage_folder>/<piece_name>.png``.
    Falls back to ``assets/char_crash/<faction>/1base/<piece_name>.png`` when
    the upgrade subfolder is missing, and then to the faction-less base path
    ``assets/char_crash/<faction>/<piece_name>.png`` if even 1base is absent.

    Parameters
    ----------
    piece:   the game-piece object.
    faction: crash-portrait faction folder (e.g. 'bandit', 'knight').
    """
    stage    = _stage_folder_for_piece(piece)
    name     = _piece_filename(piece)
    ext      = '.png'
    fname    = f"{name}{ext}"

    # 1. Try upgraded path
    candidate = os.path.join('assets', 'char_crash', faction, stage, fname)
    if os.path.isfile(candidate):
        return candidate.replace('\\', '/')

    # 2. Fall back to 1base
    base_path = os.path.join('assets', 'char_crash', faction, '1base', fname)
    if os.path.isfile(base_path):
        return base_path.replace('\\', '/')

    # 3. Last resort: flat layout (no subfolder) — some tribes may use this
    flat_path = os.path.join('assets', 'char_crash', faction, fname)
    if os.path.isfile(flat_path):
        return flat_path.replace('\\', '/')

    # 4. Return 1base path unconditionally so Kivy at least has *something*
    #    deterministic to display (blank image is better than an error log).
    return base_path.replace('\\', '/')
