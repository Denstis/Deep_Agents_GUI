#!/usr/bin/env python3
"""
Message Bubble Module - Improved chat message display component.

This module provides an optimized message bubble widget for the DeepAgents GUI
with proper width/height calculation, dynamic content sizing, and efficient rendering.

Key improvements:
- Messages use full available width
- Height is calculated dynamically based on font metrics and line count
- No hardcoded pixel heights - all sizing is relative to font size
- Efficient text wrapping and layout
- Separate handling for user and assistant messages
"""

import logging
import tkinter as tk
from datetime import datetime
from typing import Optional, Callable
import customtkinter as ctk

logger = logging.getLogger(__name__)


class MessageBubble(ctk.CTkFrame):
    """
    An optimized message bubble widget for chat display.
    
    Features:
    - Full-width messages with proper alignment
    - Dynamic height calculation based on content
    - Font-metric-based sizing (no hardcoded pixels)
    - Collapsible content for long messages
    - Copy to clipboard functionality
    - Streaming update support
    """
    
    # Configuration constants
    USER_BG_COLOR = "#3a3a3a"
    ASSISTANT_BG_COLOR = "#2b2b2b"
    CORNER_RADIUS = 12
    PADDING_X = 15
    PADDING_Y = 12
    COLLAPSED_LINES = 20
    
    def __init__(
        self,
        master,
        message: str,
        role: str = "user",
        timestamp: Optional[str] = None,
        on_copy: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize a message bubble.
        
        Args:
            master: Parent widget
            message: Message text content
            role: "user" or "assistant"
            timestamp: Optional timestamp string (defaults to current time)
            on_copy: Optional callback when message is copied
            **kwargs: Additional arguments passed to CTkFrame
        """
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        
        self.role = role
        self.is_expanded = False
        self.full_message = message
        self.on_copy_callback = on_copy
        
        # Configure grid for full-width layout
        self.grid_columnconfigure(0, weight=1)
        
        logger.debug(f"MessageBubble created: role={role}, message_len={len(message)}")
        
        # Timestamp
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Header frame (role + timestamp)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="w", padx=self.PADDING_X, pady=(5, 0))
        
        # Role label
        role_color = "#3498db" if role == "user" else "#2ecc71"
        role_text = "You" if role == "user" else "Assistant"
        
        self.role_label = ctk.CTkLabel(
            self.header_frame,
            text=f"{role_text} • {timestamp}",
            text_color=role_color,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.role_label.pack(side="left")
        
        # Message container - full width
        self.message_container = ctk.CTkFrame(
            self,
            corner_radius=self.CORNER_RADIUS,
            fg_color=self.ASSISTANT_BG_COLOR if role == "assistant" else self.USER_BG_COLOR
        )
        self.message_container.grid(row=1, column=0, sticky="ew", padx=0, pady=5)
        self.message_container.grid_columnconfigure(0, weight=1)
        
        # Calculate optimal height based on font metrics
        font_size = 13
        char_width_approx = font_size * 0.6  # Approximate character width in pixels
        container_width = self._get_container_width()
        chars_per_line = max(20, int(container_width / char_width_approx))
        
        # Count lines needed for the message
        estimated_lines = self._estimate_line_count(message, chars_per_line)
        
        # Determine display height
        if role == "assistant" and len(message) > 500 and estimated_lines > self.COLLAPSED_LINES:
            display_lines = self.COLLAPSED_LINES
            self._needs_expand_button = True
        else:
            display_lines = estimated_lines
            self._needs_expand_button = False
        
        # Text widget for message content
        self.message_text = ctk.CTkTextbox(
            self.message_container,
            wrap="word",
            font=ctk.CTkFont(size=font_size, family="Segoe UI"),
            height=display_lines,
            activate_scrollbars=False,
            border_width=0,
            fg_color="transparent"
        )
        self.message_text.grid(row=0, column=0, sticky="ew", padx=self.PADDING_X, pady=self.PADDING_Y)
        self.message_text.insert("0.0", message)
        self.message_text.configure(state="disabled")
        
        # Store actual line count for expansion
        self._actual_line_count = estimated_lines
        self._display_line_count = display_lines
        
        # Button frame (only show if needed)
        if self._needs_expand_button or True:  # Always show copy button
            self.btn_frame = ctk.CTkFrame(self.message_container, fg_color="transparent")
            self.btn_frame.grid(row=1, column=0, sticky="e", padx=self.PADDING_X, pady=(0, self.PADDING_Y))
            
            # Expand/Collapse button for assistant messages
            if self._needs_expand_button:
                self.toggle_btn = ctk.CTkButton(
                    self.btn_frame,
                    text="📋 Показать полностью",
                    command=self._toggle_expand,
                    width=140,
                    height=28,
                    font=ctk.CTkFont(size=11),
                    fg_color="transparent",
                    hover_color="#4a4a4a"
                )
                self.toggle_btn.pack(side="left", padx=(0, 10))
            
            # Copy button
            self.copy_btn = ctk.CTkButton(
                self.btn_frame,
                text="📋 Копировать",
                command=self._copy_to_clipboard,
                width=110,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                hover_color="#4a4a4a"
            )
            self.copy_btn.pack(side="right")
        
        # Schedule final layout adjustment
        self.after(50, self._adjust_layout)
    
    def _get_container_width(self) -> int:
        """Estimate available container width in pixels."""
        try:
            # Try to get parent width, fallback to reasonable default
            parent = self.master
            if hasattr(parent, 'winfo_width'):
                width = parent.winfo_width()
                if width > 1 and width < 10000:  # Valid width
                    return max(300, width - 60)  # Account for padding
            return 500  # Default estimate
        except Exception:
            return 500
    
    def _estimate_line_count(self, text: str, chars_per_line: int) -> int:
        """
        Estimate the number of lines needed for the given text.
        
        Args:
            text: The message text
            chars_per_line: Approximate characters that fit per line
            
        Returns:
            Estimated number of lines
        """
        if not text:
            return 1
        
        # Split by newlines first
        lines = text.split('\n')
        total_lines = 0
        
        for line in lines:
            # Account for word wrapping within each line
            if len(line) <= chars_per_line:
                total_lines += 1
            else:
                # Estimate wrapped lines
                words = line.split(' ')
                current_line_len = 0
                line_count = 1
                
                for word in words:
                    word_len = len(word) + 1  # +1 for space
                    if current_line_len + word_len > chars_per_line:
                        line_count += 1
                        current_line_len = word_len
                    else:
                        current_line_len += word_len
                
                total_lines += line_count
        
        return max(1, total_lines)
    
    def _adjust_layout(self):
        """Final layout adjustment after widget is fully rendered."""
        try:
            # Recalculate based on actual container width
            actual_width = self.message_container.winfo_width()
            if actual_width > 10:
                font_size = 13
                char_width_approx = font_size * 0.6
                chars_per_line = max(20, int(actual_width / char_width_approx))
                
                # Recalculate line count
                new_line_count = self._estimate_line_count(self.full_message, chars_per_line)
                self._actual_line_count = new_line_count
                
                # Update display if collapsed
                if not self.is_expanded and self._needs_expand_button:
                    display_lines = min(new_line_count, self.COLLAPSED_LINES)
                    if display_lines != self._display_line_count:
                        self._display_line_count = display_lines
                        self.message_text.configure(height=display_lines)
            
            logger.debug(f"Layout adjusted: width={actual_width}, lines={self._actual_line_count}")
        except Exception as e:
            logger.error(f"Layout adjustment failed: {e}")
    
    def _copy_to_clipboard(self):
        """Copy message content to clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.full_message)
            
            # Show temporary feedback
            if hasattr(self, 'copy_btn'):
                original_text = self.copy_btn.cget("text")
                self.copy_btn.configure(text="✓ Скопировано!")
                self.after(1500, lambda: self.copy_btn.configure(text=original_text))
            
            # Call callback if provided
            if self.on_copy_callback:
                self.on_copy_callback(self.full_message)
                
            logger.debug("Message copied to clipboard")
        except Exception as e:
            logger.error(f"Copy to clipboard failed: {e}")
    
    def _toggle_expand(self):
        """Toggle between expanded and collapsed state."""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            # Show full content
            self.message_text.configure(height=self._actual_line_count + 1)
            if hasattr(self, 'toggle_btn'):
                self.toggle_btn.configure(text="📄 Свернуть")
            logger.debug("Message expanded")
        else:
            # Return to collapsed state
            self.message_text.configure(height=min(self._actual_line_count, self.COLLAPSED_LINES))
            if hasattr(self, 'toggle_btn'):
                self.toggle_btn.configure(text="📋 Показать полностью")
            logger.debug("Message collapsed")
    
    def update_message(self, new_content: str):
        """
        Update the message content (for streaming responses).
        
        Args:
            new_content: New message text to display
        """
        try:
            self.full_message = new_content
            
            # Enable editing
            self.message_text.configure(state="normal")
            self.message_text.delete("0.0", "end")
            self.message_text.insert("0.0", new_content)
            self.message_text.configure(state="disabled")
            
            # Recalculate line count
            font_size = 13
            container_width = self.message_container.winfo_width()
            chars_per_line = max(20, int(container_width / (font_size * 0.6)))
            new_line_count = self._estimate_line_count(new_content, chars_per_line)
            self._actual_line_count = new_line_count
            
            # Update display height
            if self.is_expanded:
                self.message_text.configure(height=new_line_count + 1)
            elif self._needs_expand_button:
                display_lines = min(new_line_count, self.COLLAPSED_LINES)
                self._display_line_count = display_lines
                self.message_text.configure(height=display_lines)
            else:
                self.message_text.configure(height=new_line_count)
            
            logger.debug(f"Message updated: {len(new_content)} chars, {new_line_count} lines")
        except Exception as e:
            logger.error(f"Message update failed: {e}")
    
    def set_expanded(self, expanded: bool):
        """Programmatically set expanded state."""
        if expanded != self.is_expanded:
            self._toggle_expand()


def calculate_text_height(text: str, font_size: int = 13, width_pixels: int = 500) -> int:
    """
    Calculate the pixel height needed for a given text.
    
    This is a utility function for pre-calculating message heights.
    
    Args:
        text: The text to measure
        font_size: Font size in points
        width_pixels: Available width in pixels
        
    Returns:
        Required height in pixels
    """
    if not text:
        return font_size * 1.5
    
    # Approximate line height (1.2x font size is typical)
    line_height = font_size * 1.2
    
    # Estimate characters per line
    char_width = font_size * 0.6
    chars_per_line = max(10, int(width_pixels / char_width))
    
    # Count lines
    line_count = 0
    for line in text.split('\n'):
        if len(line) <= chars_per_line:
            line_count += 1
        else:
            # Account for word wrapping
            words = line.split(' ')
            current_len = 0
            line_count += 1
            for word in words:
                word_len = len(word) + 1
                if current_len + word_len > chars_per_line:
                    line_count += 1
                    current_len = word_len
                else:
                    current_len += word_len
    
    return int(line_count * line_height)
