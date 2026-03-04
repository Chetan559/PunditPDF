import subprocess
import fitz
import cv2
import numpy as np
from loguru import logger


# ── Type detection ────────────────────────────────────────────────────────────

def detect_pdf_type(file_path: str) -> str:
    """Returns: 'digital' | 'scanned' | 'handwritten'"""
    doc = fitz.open(file_path)
    total_text = "".join(page.get_text().strip() for page in doc)
    doc.close()

    if len(total_text) > 100:
        return "digital"

    doc = fitz.open(file_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    doc.close()

    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

    return _classify_image(img)


def _classify_image(image: np.ndarray) -> str:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    areas = [cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 10]

    if not areas or len(areas) < 20:
        return "scanned"

    mean = np.mean(areas)
    if mean == 0:
        return "scanned"

    return "handwritten" if (np.var(areas) / mean) > 500 else "scanned"


# ── OCR ───────────────────────────────────────────────────────────────────────

def run_ocr(file_path: str) -> str:
    """Run ocrmypdf. Returns path to OCR'd file, falls back to original on failure."""
    output_path = file_path.replace(".pdf", "_ocr.pdf")
    try:
        result = subprocess.run(
            ["ocrmypdf", "--deskew", "--optimize", "1", "--output-type", "pdfa", "--skip-text", file_path, output_path],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            logger.info(f"OCR complete: {output_path}")
            return output_path
        logger.warning(f"ocrmypdf exited {result.returncode}: {result.stderr[:200]}")
        return file_path
    except subprocess.TimeoutExpired:
        logger.error("OCR timed out after 300s")
        return file_path
    except FileNotFoundError:
        logger.error("ocrmypdf not installed")
        return file_path


# ── Text extraction ───────────────────────────────────────────────────────────

def extract_chunks(file_path: str) -> list[dict]:
    """Extract text blocks with page number and bbox."""
    doc = fitz.open(file_path)
    chunks = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        for block in page.get_text("blocks"):
            x0, y0, x1, y1, text, _, block_type = block
            text = text.strip()
            if text and block_type == 0 and len(text) > 20:
                chunks.append({
                    "text": text,
                    "page_number": page_num + 1,
                    "bbox": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
                })
    doc.close()
    return chunks


def get_page_count(file_path: str) -> int:
    doc = fitz.open(file_path)
    count = doc.page_count
    doc.close()
    return count