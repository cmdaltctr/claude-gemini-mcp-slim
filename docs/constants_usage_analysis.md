## Constants Usage Analysis

| Constant             | Functions/Classes Relied | Override Mechanism                      | Exceeding Limit Behavior       |
|----------------------|---------------------------|-----------------------------------------|--------------------------------|
| `MAX_FILE_SIZE`      | `analyze_code`, `validate_file_security` | No (hardcoded in functions)            | Truncate, warning message     |
| `MAX_LINES`          | `analyze_code`, `gemini_mcp_server` | No (hardcoded in functions)            | Truncate, warning message     |
| `CLI_TIMEOUT`        | `execute_gemini_cli`      | No (hardcoded in function)              | Terminate process, error message |
| `max_total_size`     | `ContentAggregator`       | Yes (via config parameter)              | Truncate/skip files           |
| `max_file_size`      | `FileFilter`, `ContentAggregator` | Yes (via config parameter)              | Exclude from analysis         |
| `100000`             | `sanitize_for_prompt`    | Yes (as function argument)              | Text truncation                |
| `10000`, `50000`     | `quick_query`, `analyze_code` | Yes (as function argument)              | Text truncation                |
| `1MB`                | `execute_gemini_cli`      | No (hardcoded in function)              | Return error message          |
| `1KB`                | `validate_file_security`, `ContentAggregator` | No (hardcoded in functions)            | Binary detection, chunk reading |
| `env var overrides`  | `gemini_mcp_server`       | Yes (via environment variables)         | Use value from env var        |

### Notes:
- Some constants like `max_total_size` and `max_file_size` are configured via the config parameter, allowing flexibility in different contexts.
- Sanitization limits are implemented with default values but can be overridden on a per-call basis.
- Environment variables allow specific customizations like model configurations and API key usage.

