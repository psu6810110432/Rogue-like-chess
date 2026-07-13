# Technical Summary and Implementation Plan

## 1. Heuristic-Based Scoring System

- The current `ChessAI` implementation in [logic/ai_logic.py](logic/ai_logic.py) is a handcrafted heuristic evaluator rather than a full game-tree search engine.
- `get_best_move()` collects all legal moves for the AI side and scores each candidate move independently.
- The evaluation is driven by a static piece-value table:
  - Pawn: 10
  - Knight: 30
  - Bishop: 30
  - Rook: 50
  - Queen: 90
  - King: 900
- A candidate move receives a stronger score when it captures an enemy piece, because the captured piece’s value is added to the move score.
- Positional weighting is also present: moves that move into the central area of the board receive a modest bonus.
- In Hard mode, the heuristic expands to include tactical safety checks:
  - the AI checks whether the originating square is currently threatened,
  - then simulates the move on a temporary board state,
  - and penalizes choices that leave the moved piece exposed to enemy attack.
- This means the current AI is best described as a tactical one-ply heuristic selector with limited defensive awareness.

## 2. Difficulty Tiers Implementation

- The current project resolves the AI difficulty from the running Kivy application via `App.get_running_app()` and the attribute `ai_difficulty`.
- The code path in [logic/ai_controller.py](logic/ai_controller.py) distinguishes the three tiers as follows:
  - Easy: intentionally noisy and occasionally random behavior; the AI may return a random legal move with about 50% probability.
  - Normal: standard heuristic evaluation and best-move selection.
  - Hard: same heuristic evaluation framework, but with extra safety analysis and more aggressive tactical awareness.
- Item usage is also difficulty-sensitive in the controller:
  - Hard uses items with a higher probability (0.60)
  - Normal uses items with a moderate probability (0.40)
  - Easy uses items less frequently (0.25)
- However, item usage in the current implementation is still mostly opportunistic and random rather than truly strategic.

## 3. Search Algorithm

- The existing move-selection logic is not a true recursive minimax tree search.
- It is a single-step scoring loop:
  1. enumerate legal moves,
  2. evaluate each move by heuristic score,
  3. keep the highest value,
  4. break ties randomly.
- The code does not implement recursive minimax depth expansion or alpha-beta pruning in its current state.
- As a result, the “Hard” mode is not a full deep search AI; it is a stronger tactical heuristic that includes short-range safety analysis.
- In academic terms, the present architecture is best classified as an evaluation-based greedy selector, not a deep adversarial search algorithm.

## 4. Concurrency / Non-Blocking UI

- The AI turn is scheduled through Kivy’s event loop using `Clock.schedule_once(...)` in [logic/ai_controller.py](logic/ai_controller.py).
- This introduces a brief delay before the AI move is executed, allowing the turn system to remain orderly and the controller to keep the game flow predictable.
- The current move calculation itself, however, still runs synchronously inside the AI evaluation function in [logic/ai_logic.py](logic/ai_logic.py).
- There is no active use of background threading, `ThreadPoolExecutor`, or `asyncio.to_thread` in the current code for the search calculation itself.
- Therefore, the present implementation offers only limited UI decoupling: the AI turn is deferred, but the heavy decision logic is not yet offloaded to a worker thread.
- This is the main technical gap if the project later needs deeper search depth without freezing the Kivy interface.

## Recommended Future Architecture

- Preserve the current heuristic metrics as the evaluation foundation.
- Introduce a true recursive minimax search with difficulty-controlled depth.
- Add alpha-beta pruning to reduce the branching cost of deeper search.
- Offload the search computation to a background thread or asynchronous executor to prevent UI freezing.
- Upgrade item selection into a situation-aware decision process, especially for Hard mode.

## Conclusion

The current AI system demonstrates a practical heuristic-based design tailored to the project’s chess-like game rules and item mechanics. Its main strengths are its simple interpretability, fast move generation, and tactical awareness in Hard mode. Its main limitation is that it does not yet implement a true minimax-based search tree with proper concurrency for CPU-bound reasoning.
