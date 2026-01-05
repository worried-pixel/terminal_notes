================================================================================
                         WHY TERMINAL NOTES IS BUILT THIS WAY
               Design Decisions, Constraints, and First Principles
================================================================================

This document explains *why* TERMINAL NOTES was designed and implemented
the way it is.

These choices were not accidents.
They were not limitations.
They were deliberate system-level decisions made to preserve correctness,
portability, and long-term survivability.

--------------------------------------------------------------------------------
CORE PHILOSOPHY
--------------------------------------------------------------------------------

TERMINAL NOTES is not optimized for:
- fast prototyping
- developer convenience
- trendy frameworks
- visual polish

It is optimized for:
- correctness under failure
- minimal resource usage
- deterministic behavior
- long-term stability
- independence from fragile ecosystems
- conceptual integrity of the system

This is a systems project, not a UI toy.

--------------------------------------------------------------------------------
WHY NO EXTERNAL LIBRARIES
--------------------------------------------------------------------------------

TERMINAL NOTES intentionally uses **only**:
- Python standard library
- Git
- POSIX-compatible terminals

This decision guarantees:

- Runs on any system with Python and Git
- No dependency installation
- No ABI or version conflicts
- No supply-chain risk
- No dependency rot
- No hidden background behavior

This includes:
- old servers
- Raspberry Pi
- air-gapped environments
- disaster recovery systems
- minimal containers
- mission-critical environments

Portability was treated as a **hard requirement**, not a convenience.

--------------------------------------------------------------------------------
WHY NO BACKGROUND PROCESSES
--------------------------------------------------------------------------------

TERMINAL NOTES does NOT run:
- daemons
- watchers
- polling loops
- background threads
- idle tasks

Every operation is:
- user-initiated
- executed once
- completed fully
- persisted atomically
- exited cleanly

This guarantees:
- predictable resource usage
- zero idle CPU cost
- no hidden state
- easier reasoning about correctness
- fewer failure modes

This is how infrastructure-grade systems are built.

--------------------------------------------------------------------------------
WHY ATOMIC OPERATIONS EVERYWHERE
--------------------------------------------------------------------------------

All state-changing operations are designed to be atomic.

The system explicitly accounts for:
- crashes
- power loss
- interrupted execution
- partial writes
- editor failures

Recovery is a **first-class design concern**, not an afterthought.

The goal:
> The system should never leave the user in an undefined state.

This philosophy directly influenced:
- storage layout
- write ordering
- recovery mechanisms
- UI behavior after failure

--------------------------------------------------------------------------------
WHY ITEM-LEVEL IDENTITY (UUIDs) OVER FILE HISTORY
--------------------------------------------------------------------------------

Git tracks files.
Human thought tracks *items*.

TERMINAL NOTES introduces permanent item identity using UUIDs embedded
in Git commits.

This allows:
- history preservation across renames
- history preservation across moves
- resurrection of deleted items
- temporal queries across structural change

This solves a well-known but rarely implemented problem in version control:
**file identity ≠ item identity**.

--------------------------------------------------------------------------------
WHY A TERMINAL UI
--------------------------------------------------------------------------------

The terminal was chosen intentionally.

Reasons:
- available everywhere
- keyboard-first interaction
- minimal resource usage
- works over SSH
- no GUI assumptions
- compatible with constrained systems

The UI is not menu-driven.
It is model-driven.

Key principles:
- no hidden modes
- visible state
- progressive disclosure
- navigation mirrors data structure
- historical state is explicit, not buried

The UI teaches the system as it is used.

--------------------------------------------------------------------------------
WHY INFINITE HIERARCHY AND NUMBERED JUMP NAVIGATION
--------------------------------------------------------------------------------

Most systems fail at deep hierarchy navigation.

TERMINAL NOTES introduces:
- infinite nesting
- relative numbered navigation
- instant teleportation (J1 / J2 / J3)
- width-aware truncation
- stable spatial mapping

This solves a long-standing HCI problem:
> Deep structures become unusable without spatial anchors.

Numbers act as *contextual anchors*, not paths.

--------------------------------------------------------------------------------
WHY SINGLE-INSTANCE, SINGLE-INTENT EXECUTION
--------------------------------------------------------------------------------

The system is intentionally simple in execution model:
- one instance
- one operation at a time
- explicit user intent

This reduces:
- race conditions
- synchronization complexity
- mental overhead
- hidden state interactions

Simplicity here is not lack of power.
It is **control**.

--------------------------------------------------------------------------------
WHY THIS WAS BUILT WITHOUT PRIOR PYTHON KNOWLEDGE
--------------------------------------------------------------------------------

This project separates:
- system design
- implementation mechanics

The architecture, invariants, and intent were designed first.
AI was used strictly as an implementation engine under constraint.

This demonstrates:
- architecture-first development
- specification-driven implementation
- AI as leverage, not decision-maker

The result is a coherent system built from first principles.

--------------------------------------------------------------------------------
WHY THIS MATTERS
--------------------------------------------------------------------------------

Modern software often fails not because of missing features,
but because of:
- hidden complexity
- uncontrolled dependencies
- implicit behavior
- fragile assumptions

TERMINAL NOTES demonstrates an alternative:
- fewer abstractions
- stronger invariants
- explicit behavior
- systems that can be reasoned about

This project is not about nostalgia.
It is about durability.

--------------------------------------------------------------------------------
FINAL NOTE
--------------------------------------------------------------------------------

Every choice in TERMINAL NOTES increases cognitive load for the builder
and reduces cognitive load for the user.

That tradeoff was intentional.

This system was built to last.

================================================================================
