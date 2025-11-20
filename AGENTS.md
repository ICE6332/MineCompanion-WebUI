# Repository Guidelines

## Project Structure & Module Organization
Primary Fabric mod sources live in `src/main/java/com/aicompanion/...` (commands, networking, state). Client-only features belong in `src/client/java`. Shared assets, mixins, and `fabric.mod.json` sit under `src/main/resources`. Docs remain in `docs/` (mostly Chinese reference material). Keep the upstream mirror in `MineCompanion-BOT/`; only run git there. Temporary Gradle outputs (`run/`, `build/`) must stay uncommitted.

## Build, Test, and Development Commands
Use `build-mod.bat setup|build|run|clean` from the project root for the common workflow: download sources, build the remapped JAR, launch the dev client, or clean artifacts. Direct Gradle is fine (`gradlew.bat build`, `gradlew.bat runClient`) when scripting. Prefer relative paths when referencing the frontend (`npm --prefix MineCompanionAI-WebUI run dev`).

### Python / 后端依赖管理（强制）
- 一律使用 `uv` 管理与安装依赖、创建虚拟环境和运行命令；禁止使用 `pip install`（包含 `--user` 或系统级安装）。
- 项目虚拟环境路径固定为 `.venv`，缓存目录可用 `UV_CACHE_DIR` 指定（默认 `.uv-cache`）。
- 安装/同步依赖示例：`UV_PROJECT_ENV=.venv uv sync --dev --extra dev`
- 运行工具或测试示例：`UV_PROJECT_ENV=.venv uv run uvicorn main:app --host 0.0.0.0 --port 8080`；`uv run --with pytest --with pytest-asyncio --with pytest-cov pytest -q`

### Frontend Component Workflow
- Before building or adding frontend components, verify the installed component library CLI version (e.g., `npm --prefix frontend ls @shadcn/ui` or an equivalent check).
- Components must be scaffolded via the component library CLI; do not hand-write component skeletons.
- Default to the shadcn/ui component library; any library change requires prior review and an update to this file.

## Coding Style & Naming Conventions
Target Java 21 with 4-space indentation and no tabs. Classes are `PascalCase`, methods/fields `camelCase`, constants `UPPER_SNAKE_CASE`. Namespace code under `com.aicompanion.<area>` (for example `network`, `state`, `player`). Use SLF4J `LOGGER` instead of `System.out`. Keep identifiers, file names, and types in English even when UI text is localized.

## Testing Guidelines
Manual smoke tests run through `build-mod.bat run` inside a dedicated world that exercises commands and WebSocket flows. Future automated tests belong in `src/test/java` with the `*Test.java` suffix and execute via `gradlew.bat test`. Focus coverage on protocol encoding/decoding, configuration parsing, and world-state collectors.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`). PRs should summarize behavior changes, list manual/automated tests, link issues or design docs, and attach screenshots/logs for user-visible deltas. Keep patches scoped and avoid restructuring the project root without approval.

### Git 身份
- 默认作者/提交人：`MomentieEmiya <Momentie173@outlook.com>`；提交前请确认 `git config user.name` 与 `user.email` 已匹配。

## Security & Configuration Tips
Read secrets from the Fabric config folder (`.minecraft/config/aicompanion/AICompanionConfig`). Never hard-code tokens or absolute filesystem paths. Maintain parity with the upstream `MineCompanion-BOT/` behavior when touching shared components.

## Cross-Platform Paths & Scripts
Configuration files and scripts must never reference absolute or WSL paths such as `/mnt/g/...`. Use project-relative references (`./MineCompanionAI-WebUI`) and cross-platform commands (`python3`, `npm --prefix <dir>`). Avoid shell-only idioms (`cd dir && …`); use helpers like `cross-env` when environment detection is required.

## Language & Agent Instructions
All user-facing responses, UI copy, and code comments must be Simplified Chinese, while internal reasoning stays in English and remains private. Frontend identifiers stay English, but any rendered text, placeholders, and notifications must be Chinese. Do not expose intermediate analysis to players or reviewers.
