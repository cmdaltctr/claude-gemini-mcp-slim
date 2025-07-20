# Hybrid Streaming Progress Utility

A Python utility that provides incremental dots/spinners while waiting, then switches to full output when response chunks arrive. Perfect for MCP servers and CLI tools.

## Features

**Four Progress Types**
- **Dots**: `Processing.` → `Processing..` → `Processing...` → `Processing....`
- **Spinner**: `| Processing...` → `/ Processing...` → `- Processing...` → `\ Processing...`  
- **Pulse**: Modern Unicode spinner with smooth animation
- **Bar**: Moving progress bar with elapsed time display

**Hybrid Streaming**
- Shows progress indicators while waiting for responses
- Automatically switches to streaming actual content when chunks arrive
- Clean transitions between progress and content modes

**Customizable**
- Colors, prefixes, suffixes, update intervals
- Custom spinner characters and progress bar width
- Separate streams for progress (stderr) and content (stdout)

**Easy Integration**
- Drop-in replacement for existing progress indicators
- Context manager support for automatic cleanup
- Thread-safe implementation with proper cleanup

## Quick Start

### Basic Usage

```python
from hybrid_progress import create_spinner_progress

# Create and start progress
progress = create_spinner_progress("API Request")
progress.start()

# ... your long-running operation ...

# When you get response chunks, stream them
progress.stream_chunk("Hello World!")
progress.stream_chunk("This is streaming content.")

# Complete the operation
progress.complete("Request completed")
```

### Context Manager (Recommended)

```python
from hybrid_progress import create_dots_progress

with create_dots_progress("Processing").progress_context() as progress:
    # ... your operation ...
    progress.stream_chunk("Results are ready!")
    # Automatically cleaned up when context exits
```

## Integration with Existing MCP Server

Here's how to integrate the hybrid progress utility into your existing `gemini_helper.py`:

### 1. Import the Utility

```python
from hybrid_progress import (
    create_spinner_progress,
    create_dots_progress, 
    create_pulse_progress,
    create_bar_progress,
    ProgressType
)
```

### 2. Update Your Execution Functions

#### For Quick Queries

```python
def execute_gemini_smart_with_progress(
    prompt: str, 
    task_type: str = "quick_query",
    show_progress: bool = True
) -> Dict[str, Any]:
    """Enhanced version with hybrid progress"""
    
    if not show_progress:
        return execute_gemini_smart(prompt, task_type, show_progress=False)
    
    # Create appropriate progress indicator
    if task_type == "quick_query":
        progress = create_spinner_progress("🤖 Gemini")
    elif task_type == "analyze_code":
        progress = create_pulse_progress("📊 Analysis")
    else:
        progress = create_bar_progress("📈 Deep Scan")
    
    try:
        progress.start("Processing request")
        
        # Execute the actual operation
        result = execute_gemini_smart(prompt, task_type, show_progress=False)
        
        if result["success"]:
            # Stream the response in chunks
            output_text = result["output"]
            chunks = _split_into_chunks(output_text)
            
            for chunk in chunks:
                progress.stream_chunk(chunk, end="")
                time.sleep(0.1)  # Simulate streaming delay
            
            progress.stream_chunk("\n")
            progress.complete("Processing completed")
        else:
            progress.stop(f"Error: {result['error']}")
        
        return result
        
    except Exception as e:
        progress.stop(f"Unexpected error: {str(e)}")
        return {"success": False, "error": str(e)}

def _split_into_chunks(text: str, chunk_size: int = 60) -> list:
    """Split text into chunks for streaming effect"""
    words = text.split()
    chunks = []
    current_chunk = []
    
    for word in words:
        current_chunk.append(word)
        if len(" ".join(current_chunk)) >= chunk_size:
            chunks.append(" ".join(current_chunk) + " ")
            current_chunk = []
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks
```

#### For CLI Streaming

```python
def execute_gemini_cli_with_hybrid_progress(
    prompt: str, 
    model_name: Optional[str] = None, 
    show_progress: bool = True
) -> Dict[str, Any]:
    """Enhanced CLI execution with hybrid progress"""
    
    if not show_progress:
        return execute_gemini_cli(prompt, model_name, show_progress=False)
    
    progress = create_spinner_progress("🔍 CLI")
    
    try:
        progress.start("Executing Gemini CLI")
        
        # Start the subprocess (simplified version)
        # ... your existing subprocess logic ...
        
        # Instead of printing directly to stdout, use progress.stream_chunk()
        output_lines = []
        for line in process_output:  # Your existing streaming logic
            output_lines.append(line)
            progress.stream_chunk(line.rstrip())
        
        progress.complete("CLI execution completed")
        
        return {"success": True, "output": "".join(output_lines)}
        
    except Exception as e:
        progress.stop(f"CLI error: {str(e)}")
        return {"success": False, "error": str(e)}
```

### 3. Update MCP Tool Handlers

In your `gemini_mcp_server.py`, update the tool handlers:

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Enhanced tool handler with hybrid progress"""
    
    if name == "gemini_quick_query":
        query = arguments.get("query", "")
        context = arguments.get("context", "")
        
        # Use the enhanced version with progress
        result = execute_gemini_smart_with_progress(
            f"Context: {context}\n\nQuery: {query}" if context else query,
            task_type="quick_query",
            show_progress=True
        )
        
        if result["success"]:
            return [TextContent(type="text", text=result["output"])]
        else:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
    
    # ... other tool handlers ...
```

## Configuration Options

### Progress Types

```python
# Different progress indicators
dots_progress = create_dots_progress("Task", colors=True)
spinner_progress = create_spinner_progress("Task", colors=True) 
pulse_progress = create_pulse_progress("Task", colors=True)
bar_progress = create_bar_progress("Task", width=30, colors=True)
```

### Custom Configuration

```python
from hybrid_progress import ProgressConfig, ProgressType, HybridStreamingProgress

config = ProgressConfig(
    progress_type=ProgressType.SPINNER,
    interval=0.1,           # Update every 100ms
    prefix="🚀 ",           # Text before indicator
    suffix=" please wait",  # Text after indicator
    colors=True,            # Enable ANSI colors
    stream=sys.stderr,      # Output stream for progress
    spinner_chars=['⠋', '⠙', '⠹', '⠸'],  # Custom spinner
    max_dots=5,             # Max dots for dots progress
    width=25,               # Progress bar width
    show_elapsed=True       # Show elapsed time
)

progress = HybridStreamingProgress(config)
```

## Advanced Usage

### Async Support

```python
import asyncio

async def async_operation_with_progress():
    progress = create_pulse_progress("Async Task")
    
    try:
        progress.start("Starting async operation")
        
        # Your async operation
        result = await some_async_function()
        
        # Stream results
        for chunk in result_chunks:
            progress.stream_chunk(chunk)
            await asyncio.sleep(0.1)
        
        progress.complete("Async operation completed")
        
    except Exception as e:
        progress.stop(f"Async error: {str(e)}")
```

### Error Handling Patterns

```python
def robust_operation_with_progress():
    progress = create_spinner_progress("Operation")
    
    try:
        progress.start("Starting operation")
        
        # Your operation that might fail
        result = risky_operation()
        
        if result.success:
            progress.stream_chunk(result.data)
            progress.complete("Success")
        else:
            progress.stop(f"Operation failed: {result.error}")
    
    except KeyboardInterrupt:
        progress.stop("Operation cancelled by user")
        raise
    except Exception as e:
        progress.stop(f"Unexpected error: {str(e)}")
        raise
```

### Multiple Progress Contexts

```python
async def multi_stage_operation():
    # Stage 1: Data preparation
    with create_dots_progress("Preparing").progress_context() as prep:
        prep.stream_chunk("Data prepared successfully")
    
    await asyncio.sleep(0.5)
    
    # Stage 2: Processing  
    with create_spinner_progress("Processing").progress_context() as proc:
        proc.stream_chunk("Processing completed")
    
    await asyncio.sleep(0.5)
    
    # Stage 3: Results
    with create_bar_progress("Finalizing").progress_context() as final:
        final.stream_chunk("All stages completed!")
```

## Best Practices

1. **Use appropriate progress types**:
   - `dots` for simple operations (1-3 seconds)
   - `spinner` for medium operations (3-10 seconds)  
   - `pulse` for analysis tasks
   - `bar` for long operations with time tracking

2. **Handle interruptions gracefully**:
   ```python
   try:
       with progress_context() as progress:
           # Your operation
           pass
   except KeyboardInterrupt:
       print("\nOperation cancelled")
   ```

3. **Stream content appropriately**:
   - Use reasonable chunk sizes (30-80 characters)
   - Add small delays between chunks for better UX
   - End with newlines for proper formatting

4. **Provide meaningful messages**:
   ```python
   progress.start("Analyzing security vulnerabilities")  # Good
   progress.start("Processing")                          # Less helpful
   ```

## Integration Examples

See `hybrid_progress_integration_example.py` for complete examples showing:
- Integration with existing `gemini_helper.py` functions
- Async operations with progress feedback
- Different progress types for different operation types
- Error handling and cleanup patterns

## Thread Safety

The utility is thread-safe and properly handles:
- Progress thread lifecycle management
- Clean shutdown on interruption
- Proper resource cleanup
- Race condition prevention

## Performance Impact

- Minimal CPU overhead (separate progress thread)
- No impact on main operation performance
- Clean memory usage with automatic cleanup
- Optimized ANSI escape sequence usage

---

## Testing

Run the built-in demos to test the utility:

```bash
python hybrid_progress.py
```

Or test the integration example:

```bash  
python hybrid_progress_integration_example.py
```

## Compatibility

- Python 3.7+
- Compatible with existing MCP server architecture
- Works in terminals supporting ANSI escape sequences
- Graceful fallback when colors are disabled
