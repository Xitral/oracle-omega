# ORACLE-Omega Concept

ORACLE-Omega is an early research prototype for visualizing spatial assurance checks in simulated 3D scenarios.

The initial goal is simple: load a scenario, forecast a planned path, run geometric checks, and produce an evidence card explaining whether the path satisfies the scenario constraints.

This repository is for educational and research use only. The prototype is standalone simulation software and does not connect to any real system.

## Core idea

A user should be able to see:

- the current scene state,
- the planned path,
- transparent safety volumes,
- any predicted violation point,
- the rule that was violated,
- and a replayable evidence log.

## First milestone

The first milestone is a local scenario evaluator with a small set of geometry checks and YAML-defined example scenarios.
