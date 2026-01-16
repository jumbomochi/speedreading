#!/usr/bin/env python3
"""
Speed Reading Video Generator

Creates RSVP (Rapid Serial Visual Presentation) videos with Spritz-style
ORP (Optimal Recognition Point) highlighting.

Supports input from: plain text, PDF, EPUB files
"""

import argparse
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, concatenate_videoclips


# ============================================================================
# Text Extraction
# ============================================================================

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF is required for PDF support. Install with: pip install PyMuPDF")

    doc = fitz.open(pdf_path)
    text_parts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            text_parts.append(text)

    doc.close()
    return "\n".join(text_parts)


def extract_text_from_epub(epub_path: str) -> str:
    """Extract text from an EPUB file using ebooklib."""
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError(
            "ebooklib and beautifulsoup4 are required for EPUB support. "
            "Install with: pip install EbookLib beautifulsoup4"
        )

    book = epub.read_epub(epub_path)
    text_parts = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator=' ')

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            if text.strip():
                text_parts.append(text)

    return "\n".join(text_parts)


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from a file based on its extension.
    Supports: .txt, .pdf, .epub
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == '.pdf':
        print(f"Extracting text from PDF: {file_path}")
        return extract_text_from_pdf(file_path)
    elif suffix == '.epub':
        print(f"Extracting text from EPUB: {file_path}")
        return extract_text_from_epub(file_path)
    else:
        # Assume plain text
        print(f"Reading text file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


def clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)

    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


# ============================================================================
# ORP Calculation
# ============================================================================

@dataclass
class WordFrame:
    """Represents a word with its ORP position."""
    word: str
    orp_index: int  # Index of the ORP letter (0-based)
    duration: float  # Duration in seconds


def calculate_orp(word: str) -> int:
    """
    Calculate the Optimal Recognition Point (ORP) for a word.

    The ORP is typically located slightly left of center, around
    the 1/3 to 1/2 position of the word. This is where the eye
    naturally fixates for fastest word recognition.

    Rules based on Spritz-style ORP:
    - 1 letter: position 0
    - 2-5 letters: position 1
    - 6-9 letters: position 2
    - 10-13 letters: position 3
    - 14+ letters: position 4
    """
    length = len(word)

    if length <= 1:
        return 0
    elif length <= 5:
        return 1
    elif length <= 9:
        return 2
    elif length <= 13:
        return 3
    else:
        return 4


def tokenize_text(text: str) -> list[str]:
    """
    Split text into words, preserving punctuation attached to words.
    """
    words = text.split()
    return [w for w in words if w.strip()]


# ============================================================================
# WPM Scheduling
# ============================================================================

def create_wpm_schedule(
    start_wpm: float,
    peak_wpm: float,
    total_words: int,
    ramp_words: int | None = None,
    ramp_style: str = "smooth"
) -> list[float]:
    """
    Create a WPM schedule that ramps up from start_wpm to peak_wpm,
    then stays at peak_wpm for the remainder.

    Args:
        start_wpm: Starting words per minute
        peak_wpm: Peak/target words per minute
        total_words: Total number of words
        ramp_words: Number of words over which to ramp up (default: 10% of total, min 20)
        ramp_style: "smooth" (ease-in-out), "linear", or "stepped"

    Returns:
        List of WPM values, one per word
    """
    if total_words <= 1:
        return [start_wpm]

    # Default ramp_words to 10% of total, minimum 20 words
    if ramp_words is None:
        ramp_words = max(20, int(total_words * 0.1))

    # Ensure ramp_words doesn't exceed total
    ramp_words = min(ramp_words, total_words)

    schedule = []

    if ramp_style == "smooth":
        # Smooth ease-in-out curve using cosine interpolation
        for i in range(total_words):
            if i < ramp_words:
                # Cosine ease-in-out for smooth acceleration
                progress = i / ramp_words
                # Cosine interpolation: starts slow, speeds up, then slows down at the end
                smooth_progress = (1 - math.cos(progress * math.pi)) / 2
                wpm = start_wpm + (peak_wpm - start_wpm) * smooth_progress
            else:
                wpm = peak_wpm
            schedule.append(wpm)

    elif ramp_style == "linear":
        # Linear ramp up, then plateau
        for i in range(total_words):
            if i < ramp_words:
                progress = i / ramp_words
                wpm = start_wpm + (peak_wpm - start_wpm) * progress
            else:
                wpm = peak_wpm
            schedule.append(wpm)

    elif ramp_style == "stepped":
        # Step increases during ramp phase
        num_steps = 6
        words_per_step = max(1, ramp_words // num_steps)
        wpm_step = (peak_wpm - start_wpm) / num_steps

        for i in range(total_words):
            if i < ramp_words:
                step = min(i // words_per_step, num_steps)
                wpm = start_wpm + wpm_step * step
            else:
                wpm = peak_wpm
            schedule.append(wpm)

    else:
        raise ValueError(f"Unknown ramp_style: {ramp_style}")

    return schedule


# ============================================================================
# Frame Rendering
# ============================================================================

def render_word_frame(
    word_frame: WordFrame,
    width: int = 1920,
    height: int = 1080,
    font_size: int = 120,
    bg_color: str = "#1a1a2e",
    text_color: str = "#ffffff",
    orp_color: str = "#ff0000",
    font_path: str | None = None,
) -> np.ndarray:
    """
    Render a single word frame as a numpy array.

    The word is positioned so that the ORP letter aligns with the center
    of the frame, with a small vertical line indicator.
    """
    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Load font
    if font_path and os.path.exists(font_path):
        font = ImageFont.truetype(font_path, font_size)
    else:
        # Try to load a good monospace or sans-serif font
        font_options = [
            "/System/Library/Fonts/SFNSMono.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        font = None
        for fp in font_options:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, font_size)
                    break
                except:
                    continue
        if font is None:
            font = ImageFont.load_default()

    word = word_frame.word
    orp_idx = min(word_frame.orp_index, len(word) - 1)

    # Calculate character widths to position ORP at center
    char_widths = []
    for c in word:
        bbox = draw.textbbox((0, 0), c, font=font)
        char_widths.append(bbox[2] - bbox[0])

    # Calculate the x position where ORP letter should be centered
    center_x = width // 2

    # Calculate starting x position so ORP letter center aligns with frame center
    orp_char_width = char_widths[orp_idx] if char_widths else 0
    chars_before_orp_width = sum(char_widths[:orp_idx])
    start_x = center_x - chars_before_orp_width - (orp_char_width // 2)

    # Y position - use consistent baseline based on font metrics
    # Use a reference string with ascenders and descenders for consistent height
    reference_bbox = draw.textbbox((0, 0), "Aygjpq", font=font)
    reference_height = reference_bbox[3] - reference_bbox[1]
    reference_top = reference_bbox[1]  # Top offset of the reference

    # Center the reference height in the frame
    y_base = (height - reference_height) // 2 - reference_top

    # Draw the vertical alignment line (subtle) - fixed position
    line_color = "#444444"
    line_top = (height - reference_height) // 2 - 20
    line_bottom = (height + reference_height) // 2 + 20
    draw.line([(center_x, line_top), (center_x, line_top + 15)], fill=line_color, width=2)
    draw.line([(center_x, line_bottom - 15), (center_x, line_bottom)], fill=line_color, width=2)

    # Draw each character at consistent baseline
    current_x = start_x
    for i, char in enumerate(word):
        color = orp_color if i == orp_idx else text_color
        draw.text((current_x, y_base), char, font=font, fill=color)
        current_x += char_widths[i]

    return np.array(img)


# ============================================================================
# Video Generation
# ============================================================================

def generate_speed_reading_video(
    text: str,
    output_path: str,
    start_wpm: float = 200,
    peak_wpm: float = 600,
    ramp_words: int | None = None,
    ramp_style: str = "smooth",
    width: int = 1920,
    height: int = 1080,
    font_size: int = 120,
    bg_color: str = "#1a1a2e",
    text_color: str = "#ffffff",
    orp_color: str = "#ff0000",
    font_path: str | None = None,
    fps: int = 30,
    show_wpm: bool = True,
) -> str:
    """
    Generate a speed reading video from text.

    Args:
        text: The text to convert to video
        output_path: Path to save the video
        start_wpm: Starting words per minute (during ramp)
        peak_wpm: Peak words per minute (after ramp completes)
        ramp_words: Number of words over which to ramp up (default: auto)
        ramp_style: How to ramp speed - "smooth", "linear", or "stepped"
        width: Video width in pixels
        height: Video height in pixels
        font_size: Font size for words
        bg_color: Background color (hex)
        text_color: Text color (hex)
        orp_color: ORP highlight color (hex)
        font_path: Path to custom font file
        fps: Frames per second
        show_wpm: Whether to show current WPM on screen

    Returns:
        Path to the generated video
    """
    # Clean and tokenize text
    text = clean_text(text)
    words = tokenize_text(text)
    if not words:
        raise ValueError("No words found in text")

    print(f"Processing {len(words)} words...")
    print(f"WPM: {start_wpm} -> {peak_wpm} (ramp: {ramp_style})")

    # Create WPM schedule
    wpm_schedule = create_wpm_schedule(
        start_wpm=start_wpm,
        peak_wpm=peak_wpm,
        total_words=len(words),
        ramp_words=ramp_words,
        ramp_style=ramp_style
    )

    actual_ramp_words = ramp_words if ramp_words else max(20, int(len(words) * 0.1))
    print(f"Ramping over first {min(actual_ramp_words, len(words))} words")

    # Generate clips for each word
    clips = []

    for i, (word, wpm) in enumerate(zip(words, wpm_schedule)):
        # Calculate ORP for alphanumeric portion
        clean_word = ''.join(c for c in word if c.isalnum())
        orp = calculate_orp(clean_word) if clean_word else 0

        # Adjust ORP for leading punctuation
        leading_punct = 0
        for c in word:
            if not c.isalnum():
                leading_punct += 1
            else:
                break

        # Base duration from WPM
        duration = 60.0 / wpm

        # Add pause for punctuation
        if any(c in word for c in '.!?'):
            duration *= 1.5
        elif any(c in word for c in ',;:'):
            duration *= 1.2

        # Create word frame
        word_frame = WordFrame(
            word=word,
            orp_index=orp + leading_punct,
            duration=duration
        )

        # Render frame
        frame = render_word_frame(
            word_frame,
            width=width,
            height=height,
            font_size=font_size,
            bg_color=bg_color,
            text_color=text_color,
            orp_color=orp_color,
            font_path=font_path,
        )

        # Add WPM indicator if enabled
        if show_wpm:
            img = Image.fromarray(frame)
            draw = ImageDraw.Draw(img)

            # Load smaller font for WPM display
            try:
                small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            except:
                small_font = ImageFont.load_default()

            wpm_text = f"{int(wpm)} WPM"
            draw.text((width - 200, height - 60), wpm_text, font=small_font, fill="#666666")
            frame = np.array(img)

        # Create video clip for this word
        clip = ImageClip(frame, duration=word_frame.duration)
        clips.append(clip)

        # Progress indicator
        if (i + 1) % 100 == 0 or i == len(words) - 1:
            print(f"  Processed {i + 1}/{len(words)} words...")

    print("Concatenating clips...")
    final_clip = concatenate_videoclips(clips, method="compose")

    print(f"Writing video to {output_path}...")
    final_clip.write_videofile(
        output_path,
        fps=fps,
        codec='libx264',
        audio=False,
        logger=None,  # Suppress moviepy output
    )

    # Clean up
    final_clip.close()
    for clip in clips:
        clip.close()

    total_duration = sum(c.duration for c in clips)
    print(f"Done! Video saved to {output_path}")
    print(f"Video duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")

    return output_path


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate speed reading (RSVP) videos with ORP highlighting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate video from text file (ramps to 600 WPM)
  python speedreading.py -i story.txt -o output.mp4 --peak-wpm 600

  # Generate video from PDF
  python speedreading.py -i book.pdf -o output.mp4 --peak-wpm 800

  # Generate video from EPUB
  python speedreading.py -i novel.epub -o output.mp4 --peak-wpm 500

  # Custom ramp settings (slower start, longer ramp)
  python speedreading.py -i story.txt -o output.mp4 --start-wpm 150 --peak-wpm 700 --ramp-words 50

  # Direct text input
  python speedreading.py -t "The quick brown fox jumps over the lazy dog." -o output.mp4

Supported input formats:
  - Plain text (.txt or any text file)
  - PDF documents (.pdf)
  - EPUB ebooks (.epub)
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('-i', '--input', type=str,
                             help='Path to input file (.txt, .pdf, or .epub)')
    input_group.add_argument('-t', '--text', type=str, help='Direct text input')

    # Output
    parser.add_argument('-o', '--output', type=str, required=True, help='Output video path')

    # Speed settings
    parser.add_argument('--start-wpm', type=float, default=200,
                        help='Starting WPM during ramp phase (default: 200)')
    parser.add_argument('--peak-wpm', type=float, default=600,
                        help='Peak/target WPM after ramp completes (default: 600)')
    parser.add_argument('--ramp-words', type=int, default=None,
                        help='Number of words to ramp over (default: 10%% of total, min 20)')
    parser.add_argument('--ramp', type=str, choices=['smooth', 'linear', 'stepped'],
                        default='smooth', help='Speed ramp style (default: smooth)')

    # Video settings
    parser.add_argument('--width', type=int, default=1920, help='Video width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='Video height (default: 1080)')
    parser.add_argument('--font-size', type=int, default=120, help='Font size (default: 120)')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second (default: 30)')

    # Color settings
    parser.add_argument('--bg-color', type=str, default='#1a1a2e',
                        help='Background color (default: #1a1a2e)')
    parser.add_argument('--text-color', type=str, default='#ffffff',
                        help='Text color (default: #ffffff)')
    parser.add_argument('--orp-color', type=str, default='#ff0000',
                        help='ORP highlight color (default: #ff0000)')

    # Other options
    parser.add_argument('--font', type=str, help='Path to custom font file')
    parser.add_argument('--no-wpm-display', action='store_true', help='Hide WPM indicator')

    args = parser.parse_args()

    # Get input text
    if args.input:
        text = extract_text_from_file(args.input)
    else:
        text = args.text

    # Generate video
    generate_speed_reading_video(
        text=text,
        output_path=args.output,
        start_wpm=args.start_wpm,
        peak_wpm=args.peak_wpm,
        ramp_words=args.ramp_words,
        ramp_style=args.ramp,
        width=args.width,
        height=args.height,
        font_size=args.font_size,
        bg_color=args.bg_color,
        text_color=args.text_color,
        orp_color=args.orp_color,
        font_path=args.font,
        fps=args.fps,
        show_wpm=not args.no_wpm_display,
    )


if __name__ == '__main__':
    main()
