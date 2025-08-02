#!/usr/bin/env python3
"""
Hybrid Streaming Progress Feedback Utility

Provides incremental dots/spinners while waiting, then switches to full output
when response chunks arrive. Designed for MCP servers and CLI tools.
"""

import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, TextIO


# Enum for progress types
class ProgressType(Enum):
    """Types of progress indicators"""

    DOTS = "dots"
    SPINNER = "spinner"
    BAR = "bar"
    PULSE = "pulse"


# Enum for progress states
class ProgressState(Enum):
    """Progress states"""

    IDLE = "idle"
    PROGRESS = "progress"
    STREAMING = "streaming"
    COMPLETE = "complete"
    STOPPED = "stopped"


# Dataclass for progress configuration
@dataclass
class ProgressConfig:
    """Configuration for progress indicator"""

    progress_type: ProgressType = ProgressType.DOTS
    interval: float = 0.5  # Update interval in seconds
    prefix: str = ""  # Text prefix
    suffix: str = ""  # Text suffix
    colors: bool = True  # Enable colors
    stream: TextIO = sys.stderr  # Output stream
    spinner_chars: List[str] = None  # Custom spinner characters
    max_dots: int = 4  # Maximum dots to show
    width: int = 30  # Progress bar width
    show_elapsed: bool = False  # Show elapsed time


# Hybrid streaming progress utility class
# Hybrid streaming progress utility class
class HybridStreamingProgress:
    """
    Hybrid streaming progress utility that shows progress indicators while waiting,
    then switches to displaying actual response chunks when they arrive.
    """

    # Initialize progress indicator
    def __init__(self, config: Optional[ProgressConfig] = None):
        self.config = config or ProgressConfig()
        self.state = ProgressState.IDLE
        self._progress_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._start_time: Optional[float] = None
        self._last_message = ""
        self._progress_counter = 0

        # Default spinner characters
        if self.config.spinner_chars is None:
            self.config.spinner_chars = ["|", "/", "-", "\\"]

    # Get ANSI color code
    def _get_color_code(self, color: str) -> str:
        """Get ANSI color code"""
        colors = {
            "reset": "\033[0m",
            "blue": "\033[94m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "bold": "\033[1m",
            "dim": "\033[2m",
        }
        return colors.get(color, "") if self.config.colors else ""

    # Clear the current line
    def _clear_line(self):
        """Clear the current line"""
        self.config.stream.write("\r\033[K")
        self.config.stream.flush()

    # Write progress text and return to start of line
    def _write_progress(self, text: str):
        """Write progress text and return to start of line"""
        self._clear_line()
        self.config.stream.write(f"\r{text}")
        self.config.stream.flush()

    # Generate dots progress indicator
    def _generate_dots_indicator(self) -> str:
        """Generate dots progress indicator"""
        dots_count = self._progress_counter % (self.config.max_dots + 1)
        if dots_count == 0:
            dots_count = 1
        dots = "." * dots_count
        return f"{self.config.prefix}⏳ Processing{dots}{self.config.suffix}"

    # Generate spinner progress indicator
    def _generate_spinner_indicator(self) -> str:
        """Generate spinner progress indicator"""
        char_idx = self._progress_counter % len(self.config.spinner_chars)
        spinner_char = self.config.spinner_chars[char_idx]
        color = self._get_color_code("cyan")
        reset = self._get_color_code("reset")
        return f"{self.config.prefix}{color}{spinner_char}{reset} Processing...{self.config.suffix}"

    # Generate pulse progress indicator
    def _generate_pulse_indicator(self) -> str:
        """Generate pulse progress indicator"""
        pulse_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        char_idx = self._progress_counter % len(pulse_chars)
        pulse_char = pulse_chars[char_idx]
        color = self._get_color_code("blue")
        reset = self._get_color_code("reset")
        return f"{self.config.prefix}{color}{pulse_char}{reset} Processing...{self.config.suffix}"

    # Generate progress bar indicator (indeterminate)
    def _generate_bar_indicator(self) -> str:
        """Generate progress bar indicator (indeterminate)"""
        # Create a moving progress bar effect
        pos = self._progress_counter % (self.config.width + 5)
        bar = [" "] * self.config.width

        # Add moving indicator
        for i in range(3):  # 3-char wide indicator
            idx = (pos + i) % self.config.width
            if 0 <= idx < self.config.width:
                bar[idx] = "█"

        bar_str = "".join(bar)
        color = self._get_color_code("green")
        reset = self._get_color_code("reset")

        elapsed_str = ""
        if self.config.show_elapsed and self._start_time:
            elapsed = time.time() - self._start_time
            elapsed_str = f" ({elapsed:.1f}s)"

        return f"{self.config.prefix}[{color}{bar_str}{reset}]{elapsed_str}{self.config.suffix}"

    # Main progress loop running in separate thread
    def _progress_loop(self):
        """Main progress loop running in separate thread"""
        while not self._stop_event.is_set() and self.state == ProgressState.PROGRESS:
            # Generate progress indicator based on type
            if self.config.progress_type == ProgressType.DOTS:
                indicator = self._generate_dots_indicator()
            elif self.config.progress_type == ProgressType.SPINNER:
                indicator = self._generate_spinner_indicator()
            elif self.config.progress_type == ProgressType.PULSE:
                indicator = self._generate_pulse_indicator()
            elif self.config.progress_type == ProgressType.BAR:
                indicator = self._generate_bar_indicator()
            else:
                indicator = self._generate_dots_indicator()

            self._write_progress(indicator)
            self._progress_counter += 1

            # Wait for next update or stop signal
            if self._stop_event.wait(self.config.interval):
                break

    # Start showing progress indicator
    def start(self, message: Optional[str] = None) -> None:
        """Start showing progress indicator"""
        if self.state != ProgressState.IDLE:
            return

        self.state = ProgressState.PROGRESS
        self._start_time = time.time()
        self._progress_counter = 0
        self._stop_event.clear()

        if message:
            self.config.prefix = f"{message} "

        # Start progress thread
        self._progress_thread = threading.Thread(
            target=self._progress_loop, daemon=True
        )
        self._progress_thread.start()

    # Switch to streaming mode and output chunk
    def stream_chunk(self, chunk: str, end: str = "\n") -> None:
        """Switch to streaming mode and output chunk"""
        if self.state == ProgressState.PROGRESS:
            # First chunk - switch to streaming mode
            self._stop_progress()
            self.state = ProgressState.STREAMING
            self._clear_line()

            # Show transition message
            color = self._get_color_code("green")
            reset = self._get_color_code("reset")
            self.config.stream.write(
                f"{color}✓{reset} Response received, streaming output...\n"
            )
            self.config.stream.flush()

        if self.state == ProgressState.STREAMING:
            # Output the chunk to stdout (actual content goes to stdout)
            sys.stdout.write(chunk)
            if end:
                sys.stdout.write(end)
            sys.stdout.flush()

    # Complete and clean up
    def complete(self, final_message: Optional[str] = None) -> None:
        """Complete and clean up"""
        if self.state == ProgressState.IDLE:
            return

        self._stop_progress()
        self.state = ProgressState.COMPLETE

        if final_message:
            self._clear_line()
            color = self._get_color_code("green")
            reset = self._get_color_code("reset")

            elapsed_str = ""
            if self._start_time:
                elapsed = time.time() - self._start_time
                elapsed_str = f" ({elapsed:.1f}s)"

            self.config.stream.write(f"{color}✅ {final_message}{elapsed_str}{reset}\n")
            self.config.stream.flush()
        else:
            self._clear_line()

    # Stop/abort progress
    def stop(self, error_message: Optional[str] = None) -> None:
        """Stop/abort progress"""
        self._stop_progress()
        self.state = ProgressState.STOPPED

        if error_message:
            self._clear_line()
            color = self._get_color_code("red")
            reset = self._get_color_code("reset")
            self.config.stream.write(f"{color}❌ {error_message}{reset}\n")
            self.config.stream.flush()
        else:
            self._clear_line()

    # Internal method to stop progress threading
    def _stop_progress(self) -> None:
        """Internal method to stop progress thread"""
        if self._progress_thread and self._progress_thread.is_alive():
            self._stop_event.set()
            self._progress_thread.join(timeout=1.0)
        self._progress_thread = None

    # Context manager for automatic progress handling
    @contextmanager
    def progress_context(self, message: Optional[str] = None):
        """Context manager for automatic progress handling"""
        try:
            self.start(message)
            yield self
        finally:
            if self.state in [ProgressState.PROGRESS, ProgressState.STREAMING]:
                self.complete()


# Convenience functions for common use cases
def create_dots_progress(
    prefix: str = "", colors: bool = True
) -> HybridStreamingProgress:
    """Create a dots progress indicator"""
    config = ProgressConfig(
        progress_type=ProgressType.DOTS, prefix=prefix, colors=colors, interval=0.5
    )
    return HybridStreamingProgress(config)


# Create a spinner progress indicator
def create_spinner_progress(
    prefix: str = "", colors: bool = True
) -> HybridStreamingProgress:
    """Create a spinner progress indicator"""
    config = ProgressConfig(
        progress_type=ProgressType.SPINNER, prefix=prefix, colors=colors, interval=0.1
    )
    return HybridStreamingProgress(config)


# Create a pulse progress indicator
def create_pulse_progress(
    prefix: str = "", colors: bool = True
) -> HybridStreamingProgress:
    """Create a pulse progress indicator"""
    config = ProgressConfig(
        progress_type=ProgressType.PULSE, prefix=prefix, colors=colors, interval=0.1
    )
    return HybridStreamingProgress(config)


# Create a progress bar indicator
def create_bar_progress(
    prefix: str = "", width: int = 30, colors: bool = True
) -> HybridStreamingProgress:
    """Create a progress bar indicator"""
    config = ProgressConfig(
        progress_type=ProgressType.BAR,
        prefix=prefix,
        colors=colors,
        width=width,
        interval=0.1,
        show_elapsed=True,
    )
    return HybridStreamingProgress(config)
