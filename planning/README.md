# vLLM-MLX POC Planning

This directory contains the planning documents for the vLLM-MLX Local POC project.

## Goal

Prove that **vLLM with MLX backend** is more efficient and faster than running MLX models directly on MacBook unified memory.

## Stages

| Stage | Document | Description |
|-------|----------|-------------|
| 1 | [stage1-memory.md](stage1-memory.md) | Memory detection and model recommendation |
| 2 | [stage2-engine.md](stage2-engine.md) | vLLM + MLX core engine |
| 3 | [stage3-benchmarks.md](stage3-benchmarks.md) | Benchmark suite proving efficiency |
| 4 | [stage4-cursor.md](stage4-cursor.md) | Cursor integration via OpenAI API |

## TDD Workflow

Each stage follows Test-Driven Development:
1. Write failing tests first
2. Implement minimal code to pass tests
3. Refactor while keeping tests green
4. Move to next stage only when all tests pass

## Master Plan

See [plan.md](plan.md) for the complete project plan with architecture diagrams and code snippets.
# Test
