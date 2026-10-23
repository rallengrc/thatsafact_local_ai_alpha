---
title: "PyCharm MCP Server Reference & Tool Definitions"
description: "Comprehensive guide and parameter reference for PyCharm integrated Model Context Protocol (MCP) server."
keywords: [PyCharm, JetBrains, MCP, ModelContextProtocol, Tools, IDE-Integration, Python]
category: reference
last_updated: 2026-10-23
author: Copilot
related:
  - Resources/copilot/MCP_SETUP.md
  - Resources/copilot/search-router/TOOLS_REFERENCE.md
classification: 🟢🛡️ General
ai_search_aliases: ["pycharm mcp server", "jetbrains mcp tools", "pycharm mcp tool definitions"]
---

# PyCharm MCP Server Reference & Tool Definitions

> **Source:** [JetBrains PyCharm Documentation — MCP Server](https://www.jetbrains.com/help/pycharm/mcp-server.html)  
> **Availability:** PyCharm 2025.2+ (bundled via the MCP Server plugin).

---

## 1. Overview & Setup

The PyCharm integrated MCP Server allows external clients (such as Claude Code, Codex, VS Code, GitHub Copilot CLI, Junie, Air) to access IDE tools, execute actions, inspect code, run configurations, and query databases directly via Model Context Protocol (MCP).

### Enabling the Server
1. Go to **Settings / Preferences** (`Ctrl+Alt+S` or `Cmd+,`).
2. Verify the **MCP Server** plugin is enabled under **Plugins**.
3. Under **Tools > MCP Server**, check **Enable MCP Server**.
4. Configure transports (SSE, Stdio, or HTTP Stream).

### Client Configuration Modes
- **Clients Auto-Configuration:** Automatically updates configuration files of detected external clients.
- **Project-Level Client Setup:** Writes connection settings directly to project working directory config files for project-specific MCP server availability.
- **Manual Client Setup:** Export/copy configs (`Copy SSE Config`, `Copy Stdio Config`, `Copy HTTP Stream Config`) and paste into custom client configurations.
- **Brave Mode (Execution without confirmation):** Enable *"Run shell commands or run configurations without confirmation"* under Command Execution settings to allow unattended execution.
- **Router-Only Tools:** Mark tools as *Router-only* in IDE settings so they are hidden from standard tool listings and invoked solely through `execute_tool`.

---

## 2. Toolset Catalog & Definitions

### 2.1 Analysis Tools

#### `analyze_calls`
Builds the IDE Call Hierarchy tree for a method, function, constructor, or supported type target.
- **Required Parameters:**
  - `symbolFqn` *(string)*: Plain fully qualified symbol name (e.g. `com.example.Service.run`) or exact signature returned by ambiguity error / rendered child node.
  - `analysisKind` *(string)*: Call analysis direction: `INCOMING_CALLS` (callers) or `OUTGOING_CALLS` (callees).
- **Optional Parameters:**
  - `depth` *(integer)*: Maximum call levels below requested subtree root (default: 5; 0 for root only).
  - `maxChildren` *(integer)*: Maximum direct children per node (default: 50).
  - `maxNodes` *(integer)*: Maximum total rendered call nodes (default: 1000).
  - `treePath` *(array/string)*: Path to subtree root from previous call result (null/omitted = root `[]`).
  - `childOffset` *(integer)*: Offset for paging direct children of the node (default: 0).
  - `timeout` *(integer)*: Timeout in milliseconds.
  - `projectPath` *(string)*: Absolute path or working directory of the project.

#### `build_project`
Triggers building of the project or specific files, waits for completion, and returns build errors/warnings.
- **Optional Parameters:**
  - `rebuild` *(boolean)*: Full project rebuild (default: false; effective only when `filesToRebuild` is omitted).
  - `filesToRebuild` *(array of strings)*: Specific file paths to compile (relative to project root).
  - `timeout` *(integer)*: Timeout in milliseconds.
  - `projectPath` *(string)*: Project path.

#### `get_file_problems`
Analyzes a specified file for errors and warnings using IDE inspections.
- **Optional Parameters:**
  - `filePath` *(string)*: File path relative to project root.
  - `errorsOnly` *(boolean)*: Filter for errors only vs errors and warnings.
  - `timeout` *(integer)*: Timeout in milliseconds.
  - `projectPath` *(string)*: Project path.

#### `get_project_dependencies`
Returns structured information of all libraries/dependencies defined in the project.
- **Optional Parameters:**
  - `projectPath` *(string)*: Project path.

#### `get_project_modules`
Returns a list of all modules in the project with their names and types.
- **Optional Parameters:**
  - `projectPath` *(string)*: Project path.

#### `lint_files`
Batch analysis of multiple files for errors and warnings using IDE inspections.
- **Required Parameters:**
  - `files` *(array of strings)*: List of project-relative file paths to analyze.
- **Optional Parameters:**
  - `min_severity` *(string)*: Minimum severity filter (`warning` or `error`; default: `warning`).
  - `timeout` *(integer)*: Timeout in milliseconds.
  - `projectPath` *(string)*: Project path.

---

### 2.2 Code Insight Tools

#### `get_symbol_info`
Retrieves Quick Documentation, declaration snippet, signature, and type info at a specified cursor coordinate.
- **Optional Parameters:**
  - `filePath` *(string)*: Path relative to project root.
  - `line` *(integer)*: 1-based line number.
  - `column` *(integer)*: 1-based column number.
  - `projectPath` *(string)*: Project path.

---

### 2.3 Database Tools

*(Note: Requires configured database data sources in PyCharm/DataGrip)*

#### `cancel_sql_query`
Cancels a running query session.
- **Optional Parameters:**
  - `sessionId` *(string)*: Query session ID.

#### `create_database_connection`
Creates a new database data source.
- **Required Parameters:**
  - `name` *(string)*: Unique connection name.
- **Optional Parameters:**
  - `dbms` *(string)*: DBMS identifier/name.
  - `url` *(string)*: JDBC connection URL.
  - `needToCheckDs` *(boolean)*: Test connection immediately upon creation.
  - `projectPath` *(string)*: Project path.

#### `edit_database_connection`
Edits driver and JDBC URL for an existing connection.
- **Optional Parameters:**
  - `connectionId` *(string)*: Unique connection ID.
  - `dbms` *(string)*: DBMS identifier/name.
  - `url` *(string)*: JDBC URL.
  - `needToCheckDs` *(boolean)*: Test connection immediately upon edit.
  - `projectPath` *(string)*: Project path.

#### `execute_sql_query`
Executes SQL query against target connection and returns status and CSV data.
- **Optional Parameters:**
  - `connectionId` *(string)*: Unique connection ID.
  - `queryText` *(string)*: SQL query text.

#### `fetch_query_result`
Paginates through an existing query result set.
- **Required Parameters:**
  - `resultSetId` *(string)*: Result set ID from previous execution.
  - `offset` *(integer)*: Row offset to start fetching from (default: 0).
- **Optional Parameters:**
  - `projectPath` *(string)*: Project path.

#### `get_database_object_description`
Retrieves hierarchical structure (columns, types, keys, indexes) of a database object.
- **Optional Parameters:**
  - `connectionId` *(string)*: Unique connection ID.
  - `databaseName` *(string)*: Database name (can be empty if DBMS uses schemas only).
  - `schemaName` *(string)*: Schema name.
  - `kind` *(string)*: Object kind code filter (or null for all).
  - `objectName` *(string)*: Name of table/view/object.
  - `projectPath` *(string)*: Project path.

#### `introspect_schema`
Triggers schema metadata introspection or refresh.
- **Optional Parameters:**
  - `connectionId` *(string)*: Unique connection ID.
  - `databaseName` *(string)*: Database name.
  - `schemaName` *(string)*: Schema name.
  - `projectPath` *(string)*: Project path.

#### `list_database_connections`
Lists configured data sources with ID, name, DBMS, and driver.
- *(No mandatory parameters)*

#### `list_database_schemas`
Lists schemas for a given connection.
- **Optional Parameters:**
  - `connectionId` *(string)*: Unique connection ID.
  - `selectedOnly` *(boolean)*: Filter for selected schemas in database tool window.

#### `list_recent_sql_queries`
Retrieves history and current state of SQL queries.
- **Optional Parameters:**
  - `connectionId` *(string)*: Unique connection ID.

#### `list_schema_object_kinds`
Lists supported object types/kinds for the connection.
- **Optional Parameters:**
  - `connectionId` *(string)*: Unique connection ID.

#### `list_schema_objects`
Lists database objects in a schema.
- **Optional Parameters:**
  - `connectionId` *(string)*: Unique connection ID.
  - `schemaName` *(string)*: Schema name.
  - `databaseName` *(string)*: Database name.
  - `kind` *(string)*: Object kind filter code.

#### `preview_table_data`
Returns preview rows in CSV format.
- **Optional Parameters:**
  - `connectionId` *(string)*: Unique connection ID.
  - `schemaName` *(string)*: Schema name.
  - `databaseName` *(string)*: Database name.
  - `tableName` *(string)*: Target table name.
  - `maxRowCount` *(integer)*: Maximum rows to return (default: 100).

#### `test_database_connection`
Runs diagnostic connection probe.
- **Optional Parameters:**
  - `id` *(string)*: Unique connection ID.

---

### 2.4 Execution & Run Configuration Tools

#### `execute_run_configuration`
Executes an existing project run configuration by name, or a temporary configuration created from code context (`filePath` + `line`).
- **Optional Parameters:**
  - `configurationName` *(string)*: Existing run configuration name (mutually exclusive with `filePath`+`line`).
  - `filePath` *(string)*: File path relative to project root.
  - `line` *(integer)*: 1-based line number for run point.
  - `timeout` *(integer)*: Timeout in milliseconds.
  - `waitForExit` *(boolean)*: Wait for termination (`true`) or return upon start (`false`).
  - `programArguments` *(string)*: One-time CLI argument override (whitespace-only string clears).
  - `workingDirectory` *(string)*: One-time working directory override.
  - `envs` *(object/map)*: One-time environment variables override.
  - `projectPath` *(string)*: Project path.

#### `get_run_configurations`
Discovers existing run configurations or executable entry points in a file.
- **Optional Parameters:**
  - `filePath` *(string)*: When provided, returns run points (methods, main, tests) in the file; when omitted, lists project-wide configurations.
  - `projectPath` *(string)*: Project path.

---

### 2.5 File Tools

#### `create_new_file`
Creates a file in the project.
- **Optional Parameters:**
  - `pathInProject` *(string)*: Target path relative to project root.
  - `text` *(string)*: File content.
  - `overwrite` *(boolean)*: Overwrite existing file flag.
  - `projectPath` *(string)*: Project path.

#### `get_all_open_file_paths`
Returns relative paths of all currently open files in editor tabs.
- **Optional Parameters:**
  - `projectPath` *(string)*: Project path.

#### `list_directory_tree`
Generates a pseudo-graphic directory tree hierarchy.
- **Optional Parameters:**
  - `directoryPath` *(string)*: Path relative to project root.
  - `maxDepth` *(integer)*: Recursion depth limit.
  - `timeout` *(integer)*: Timeout in milliseconds.
  - `projectPath` *(string)*: Project path.

#### `open_file_in_editor`
Opens target file in active IDE editor window.
- **Optional Parameters:**
  - `filePath` *(string)*: Absolute or project-relative file path.
  - `projectPath` *(string)*: Project path.

---

### 2.6 Formatting & Refactoring Tools

#### `reformat_file`
Applies IDE code style and formatting rules to target file.
- **Optional Parameters:**
  - `path` *(string)*: File path relative to project root.
  - `projectPath` *(string)*: Project path.

#### `rename_refactoring`
Context-aware symbol renaming that updates references project-wide.
- **Optional Parameters:**
  - `pathInProject` *(string)*: File containing definition/reference.
  - `symbolName` *(string)*: Existing symbol name.
  - `newName` *(string)*: New target symbol name.
  - `projectPath` *(string)*: Project path.

---

### 2.7 Jupyter Notebook Tools

#### `create_notebook`
Creates an empty `.ipynb` file (nbformat 4.5 schema).
- **Optional Parameters:**
  - `file_path` *(string)*: Absolute or project-relative path.
  - `projectPath` *(string)*: Project path.

#### `edit_notebook`
Inserts, replaces, or deletes cells in an `.ipynb` file.
- **Optional Parameters:**
  - `file_path` *(string)*: Path to notebook file.
  - `cell_id` *(string)*: Target cell ID.
  - `new_source` *(string)*: Cell source code or Markdown text.
  - `cell_type` *(string)*: `code` or `markdown` (required for insert mode).
  - `edit_mode` *(string)*: `replace` (default), `insert`, or `delete`.
  - `projectPath` *(string)*: Project path.

#### `execute_code_on_kernel`
Executes ephemeral Python snippet on active kernel without modifying the notebook.
- **Optional Parameters:**
  - `file_path` *(string)*: Path to notebook file.
  - `code` *(string)*: Python code snippet.
  - `projectPath` *(string)*: Project path.

#### `get_notebook_state`
Checks execution state (idle, busy, queued cells).
- **Optional Parameters:**
  - `file_path` *(string)*: Path to notebook file.
  - `projectPath` *(string)*: Project path.

#### `interrupt_notebook`
Interrupts running kernel computation.
- **Optional Parameters:**
  - `file_path` *(string)*: Path to notebook file.
  - `projectPath` *(string)*: Project path.

#### `kill_notebook`
Terminates notebook kernel process.
- **Optional Parameters:**
  - `file_path` *(string)*: Path to notebook file.
  - `projectPath` *(string)*: Project path.

#### `read_notebook`
Reads entire notebook structure with cell sources and outputs.
- **Optional Parameters:**
  - `file_path` *(string)*: Path to notebook file.
  - `projectPath` *(string)*: Project path.

#### `read_notebook_cell`
Reads single cell contents or rendered outputs.
- **Optional Parameters:**
  - `file_path` *(string)*: Path to notebook file.
  - `cell_id` *(string)*: Target cell ID.
  - `read_mode` *(string)*: `all`, `source`, or `output`.
  - `output_mode` *(string)*: `delta` (default) or `full`.
  - `projectPath` *(string)*: Project path.

#### `run_notebook_cell`
Runs designated or all cells and collects outputs.
- **Optional Parameters:**
  - `file_path` *(string)*: Path to notebook file.
  - `cell_ids` *(array of strings)*: List of cell IDs to run (runs all if omitted).
  - `projectPath` *(string)*: Project path.

#### `wait_cell_execution`
Blocks until specified cell completes execution.
- **Optional Parameters:**
  - `file_path` *(string)*: Path to notebook file.
  - `cell_id` *(string)*: Cell ID to wait for.
  - `projectPath` *(string)*: Project path.

---

### 2.8 Inspection KTS Tools

#### `generate_inspection_kts_api`
Retrieves Inspection KTS API documentation for Java or Kotlin.
- **Optional Parameters:**
  - `language` *(string)*: `'Java'` or `'Kotlin'`.
  - `wrapInTags` *(boolean)*: Wrap output in `<API>` tags.
  - `projectPath` *(string)*: Project path.

#### `generate_inspection_kts_examples`
Returns sample inspection.kts templates and curated patterns.
- **Optional Parameters:**
  - `language` *(string)*: `'Java'` or `'Kotlin'`.
  - `includeAdditionalExamples` *(boolean)*: Include extra curated examples.
  - `projectPath` *(string)*: Project path.

#### `generate_psi_tree`
Generates indented PSI (Program Structure Interface) tree for code snippet.
- **Optional Parameters:**
  - `code` *(string)*: Source snippet.
  - `language` *(string)*: `'Java'` or `'Kotlin'`.
  - `projectPath` *(string)*: Project path.

#### `run_inspection_kts`
Runs inspection script against project file or source string.
- **Optional Parameters:**
  - `inspectionKtsCode` *(string)*: Script source code.
  - `contextPath` *(string)*: Relative path of file to analyze.
  - `targetFileContent` *(string)*: Direct file content override.
  - `projectPath` *(string)*: Project path.

#### `validate_inspection_kts`
Validates inspection.kts against specification test cases.
- **Optional Parameters:**
  - `inspectionKtsCode` *(string)*: Inspection script code.
  - `pathToSpecification` *(string)*: Path to test case specification.
  - `projectPath` *(string)*: Project path.

---

### 2.9 Patch Tools

#### `apply_patch`
Applies a patch in Codex patch format or unified git diff format (supports Add, Delete, Update, Move).
- **Optional Parameters:**
  - `input` *(string)*: Unified diff or patch text.
  - `patch` *(string)*: Alias of `input`.
  - `projectPath` *(string)*: Project path.

---

### 2.10 Python Environment Tools

#### `configure_python_interpreter`
Configures or attaches a local Python interpreter/venv for the target module.
- **Optional Parameters:**
  - `filePath` *(string)*: Path to Python file in target module.
  - `projectPath` *(string)*: Project path.

#### `get_python_environment`
Returns active Python version, environment type (venv, conda, etc.), executable path, and package manager.
- **Optional Parameters:**
  - `filePath` *(string)*: Path to Python file in target module.
  - `projectPath` *(string)*: Project path.

---

### 2.11 Read Tools

#### `read_file`
Reads files in workspace, dependencies, external libraries, or decompiles `.class` files.
- **Optional Parameters:**
  - `file_path` *(string)*: Project-relative path, absolute path, archive path (`lib.jar!/pkg/Foo.class`), or URI (`file://`, `jar://`).
  - `mode` *(string)*: Read mode: `slice`, `lines`, `line_columns`, `offsets`, or `indentation`.
  - `start_line` *(integer)*: 1-based start line.
  - `max_lines` *(integer)*: Maximum lines to return.
  - `end_line` *(integer)*: 1-based end line.
  - `start_column` *(integer)*: 1-based start column.
  - `end_column` *(integer)*: 1-based end column.
  - `start_offset` *(integer)*: 0-based start character offset.
  - `end_offset` *(integer)*: 0-based end character offset.
  - `context_lines` *(integer)*: Surrounding lines of context.
  - `max_levels` *(integer)*: Maximum indentation levels to include.
  - `include_siblings` *(boolean)*: Include sibling blocks at same indent level.
  - `include_header` *(boolean)*: Include comments/annotations above anchor.
  - `projectPath` *(string)*: Project path.

---

### 2.12 Search Tools

#### `search_file`
Finds files by glob syntax.
- **Optional Parameters:**
  - `q` *(string)*: Glob pattern (e.g., `"**/*.py"`, `"src/**/test_*.py"`).
  - `paths` *(array of strings)*: Path filters (`!` excludes supported).
  - `includeExcluded` *(boolean)*: Include ignored/excluded files.
  - `limit` *(integer)*: Max results.
  - `projectPath` *(string)*: Project path.

#### `search_regex`
Finds code matching regular expression with line/column coordinates.
- **Optional Parameters:**
  - `q` *(string)*: Regex pattern.
  - `paths` *(array of strings)*: Project-relative glob filters.
  - `limit` *(integer)*: Max results.
  - `projectPath` *(string)*: Project path.

#### `search_symbol`
Semantic symbol search across project (classes, methods, fields).
- **Optional Parameters:**
  - `q` *(string)*: Symbol query name or fragment.
  - `paths` *(array of strings)*: Path filters.
  - `include_external` *(boolean)*: Include SDK and external library symbols (default: false).
  - `limit` *(integer)*: Max results.
  - `projectPath` *(string)*: Project path.

#### `search_text`
Fast literal substring text search.
- **Optional Parameters:**
  - `q` *(string)*: Substring text.
  - `paths` *(array of strings)*: Path filters.
  - `limit` *(integer)*: Max results.
  - `projectPath` *(string)*: Project path.

#### `skill_search`
Unified search entrypoint supporting all search types.
- **Required Parameters:**
  - `mode` *(string)*: `'file'`, `'text'`, `'regex'`, or `'symbol'`.
  - `q` *(string)*: Search query (glob for file mode, regex for regex mode).
- **Optional Parameters:**
  - `paths` *(array of strings)*: Project-relative glob filters.
  - `include_external` *(boolean)*: Include SDK/library symbols (`mode=symbol`).
  - `includeExcluded` *(boolean)*: Include excluded files (`mode=file`).
  - `limit` *(integer)*: Max results.
  - `projectPath` *(string)*: Project path.

---

### 2.13 Terminal Tools

#### `execute_terminal_command`
Executes shell commands in IDE's integrated terminal.
- **Optional Parameters:**
  - `command` *(string)*: Shell command string.
  - `executeInShell` *(boolean)*: Run in user's default shell (`true`) or direct process (`false`).
  - `reuseExistingTerminalWindow` *(boolean)*: Reuse active terminal session.
  - `timeout` *(integer)*: Timeout in milliseconds.
  - `maxLinesCount` *(integer)*: Max output lines (default max: 2000).
  - `truncateMode` *(string)*: Truncation behavior (`start`, `middle`, `end`, `none`).
  - `projectPath` *(string)*: Project path.

---

### 2.14 Universal Router Tool

#### `execute_tool`
Universal dispatcher to invoke router-only or standard MCP tools via command-line syntax.
- **Required Parameters:**
  - `command` *(string)*: Command string specifying tool name and arguments.
- **Optional Parameters:**
  - `projectPath` *(string)*: Project path.

---

### 2.15 Version Control (VCS) Tools

#### `get_repositories`
Discovers all VCS root directories in project.
- **Optional Parameters:**
  - `projectPath` *(string)*: Project path.

#### `git_status`
Returns porcelain-style index and worktree status.
- **Optional Parameters:**
  - `repositoryPathRelativeToProject` *(string)*: Specific repository filter.
  - `includeUntracked` *(boolean)*: Include untracked files.
  - `includeIgnored` *(boolean)*: Include ignored files.
  - `limit` *(integer)*: Result entry limit.
  - `projectPath` *(string)*: Project path.

---

## 3. Essential Operational Guidelines

1. **`projectPath` Best Practice:**
   - Always supply `projectPath` across tool calls when operating in multi-root workspaces or when the client process working directory differs from the IDE project root.
2. **Context Economy via Router-Only Mode:**
   - Enabling `Router-only` mode in PyCharm hides detailed schemas from the client's system prompt and routes dynamic queries through `execute_tool`.
3. **Brave Mode for Autonomous Execution:**
   - If running autonomous agent workflows (e.g. CI/CD or background scripts), ensure *"Run shell commands or run configurations without confirmation"* is checked in IDE settings to avoid blocking prompts.
4. **Read-Only Database Hygiene:**
   - To safeguard databases during AI access, configure the database connection with read-only credentials and restricted schema privileges.
