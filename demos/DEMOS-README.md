# Demos

This directory contains demonstration scripts for the hybrid progress utility functionality.

## Files

### `hybrid_progress_mcp_demo.py`
Interactive demonstration of hybrid progress utility integrated with MCP server functionality. Shows how the progress indicators work with:

- **Gemini Quick Query**: Spinner progress with streaming response
- **Code Analysis**: Pulse progress with analysis phases  
- **Codebase Analysis**: Progress bar with comprehensive reporting
- **Error Handling**: Demonstrates graceful failure scenarios

**Usage:**
```bash
python demos/hybrid_progress_mcp_demo.py
```

This demo simulates actual MCP server operations and showcases:
- Progress indicators transitioning to streaming output
- Different progress types for different operations
- Real-time feedback during processing
- Error handling with proper progress cleanup

### `streaming_demo.py`
Basic demonstration of the streaming progress features.

**Usage:**
```bash  
python demos/streaming_demo.py
```

## Running the Demos

From the project root directory:

```bash
# Run MCP integration demo
python demos/hybrid_progress_mcp_demo.py

# Run basic streaming demo  
python demos/streaming_demo.py
```

These demos help visualize how the hybrid progress utility enhances user experience by providing smooth transitions from animated progress indicators to actual streaming content, similar to modern AI interfaces.
