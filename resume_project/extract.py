import pymupdf
import re
import hashlib
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("resumes")
OUTPUT_DIR = Path("extracted")

TEXT_OUTPUT_DIR = OUTPUT_DIR
IMAGE_OUTPUT_DIR = OUTPUT_DIR / "images"


# ------------------------------------------------------------
# Meaningful image filters
# ------------------------------------------------------------
#
# Small logos/icons/signatures are ignored.
# A real profile photo should normally be larger than this.
#

MIN_IMAGE_WIDTH = 30
MIN_IMAGE_HEIGHT = 30
MIN_IMAGE_AREA = 900


# ============================================================
# FILENAME CLEANING
# ============================================================

def safe_filename(name):

    name = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        name
    )

    name = re.sub(
        r"\s+",
        " ",
        name
    )

    return name.strip()


# ============================================================
# IMAGE CHECK
# ============================================================

def is_meaningful_image(width, height):

    if width < MIN_IMAGE_WIDTH:
        return False

    if height < MIN_IMAGE_HEIGHT:
        return False

    if width * height < MIN_IMAGE_AREA:
        return False

    return True


# ============================================================
# EXTRACT IMAGE FROM BLOCK
# ============================================================

def save_image_block(
    block,
    image_folder,
    image_number
):

    width = block.get(
        "width",
        0
    )

    height = block.get(
        "height",
        0
    )

    # Ignore tiny images
    if not is_meaningful_image(
        width,
        height
    ):
        return None

    image_bytes = block.get(
        "image"
    )

    if not image_bytes:
        return None

    extension = block.get(
        "ext",
        "png"
    )

    extension = extension.lower()

    if extension not in {
        "png",
        "jpg",
        "jpeg",
        "bmp",
        "gif",
        "tiff",
        "webp"
    }:

        extension = "png"

    # --------------------------------------------------------
    # Avoid empty image folders / files
    # --------------------------------------------------------

    image_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        f"image_{image_number}."
        f"{extension}"
    )

    output_file = (
        image_folder /
        filename
    )

    with open(
        output_file,
        "wb"
    ) as f:

        f.write(
            image_bytes
        )

    return output_file


# ============================================================
# TEXT FROM TEXT BLOCK
# ============================================================

def extract_text_from_block(block):

    lines = []

    for line in block.get(
        "lines",
        []
    ):

        spans = []

        for span in line.get(
            "spans",
            []
        ):

            text = span.get(
                "text",
                ""
            )

            if text:
                spans.append(text)

        if spans:

            lines.append(
                "".join(spans)
            )

    return "\n".join(lines)


# ============================================================
# BLOCK SORTING
# ============================================================

def block_position(block):

    bbox = block.get(
        "bbox",
        (0, 0, 0, 0)
    )

    x0 = bbox[0]
    y0 = bbox[1]

    return (
        round(y0, 2),
        round(x0, 2)
    )


# ============================================================
# EXTRACT ONE PDF
# ============================================================

def extract_pdf(pdf_file):

    print()
    print(
        f"Processing: {pdf_file.name}"
    )

    try:

        document = pymupdf.open(
            pdf_file
        )

    except Exception as e:

        print(
            f"  ERROR opening PDF: {e}"
        )

        return False

    print(
        f"  Pages: {len(document)}"
    )

    resume_name = safe_filename(
        pdf_file.stem
    )

    text_output_file = (
        TEXT_OUTPUT_DIR /
        f"{resume_name}.txt"
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Image folder is NOT created here.
    #
    # It will only be created if a meaningful image
    # is actually found.
    # --------------------------------------------------------

    image_folder = (
        IMAGE_OUTPUT_DIR /
        resume_name
    )

    all_output = []

    image_counter = 0

    saved_images = []

    # Used to avoid saving the exact same image twice
    seen_image_hashes = set()

    # ========================================================
    # PROCESS EACH PAGE
    # ========================================================

    for page_number, page in enumerate(
        document,
        start=1
    ):

        # ----------------------------------------------------
        # Get blocks
        # ----------------------------------------------------

        page_dict = page.get_text(
            "dict"
        )

        blocks = page_dict.get(
            "blocks",
            []
        )

        # ----------------------------------------------------
        # Sort blocks by their physical position
        #
        # This gives us:
        #
        # top-left image
        # ↓
        # text next to it
        # ↓
        # remaining text
        #
        # rather than simply putting all images at the end.
        # ----------------------------------------------------

        blocks = sorted(
            blocks,
            key=block_position
        )

        page_output = []

        # ====================================================
        # PROCESS BLOCKS
        # ====================================================

        for block in blocks:

            block_type = block.get(
                "type"
            )

            # ------------------------------------------------
            # TEXT BLOCK
            # ------------------------------------------------

            if block_type == 0:

                text = extract_text_from_block(
                    block
                )

                if text.strip():

                    page_output.append(
                        text.rstrip()
                    )

            # ------------------------------------------------
            # IMAGE BLOCK
            # ------------------------------------------------

            elif block_type == 1:

                width = block.get(
                    "width",
                    0
                )

                height = block.get(
                    "height",
                    0
                )

                # --------------------------------------------
                # Ignore tiny graphics/icons
                # --------------------------------------------

                if not is_meaningful_image(
                    width,
                    height
                ):

                    continue

                image_bytes = block.get(
                    "image"
                )

                if not image_bytes:

                    continue

                # --------------------------------------------
                # Prevent exact duplicate images
                # --------------------------------------------

                image_hash = hashlib.sha256(
                    image_bytes
                ).hexdigest()

                if image_hash in seen_image_hashes:

                    continue

                seen_image_hashes.add(
                    image_hash
                )

                # --------------------------------------------
                # Save image
                # --------------------------------------------

                image_counter += 1

                image_file = save_image_block(
                    block,
                    image_folder,
                    image_counter
                )

                if image_file is None:

                    continue

                saved_images.append(
                    image_file
                )

                # --------------------------------------------
                # Relative path used inside TXT
                # --------------------------------------------

                relative_path = (
                    Path("images")
                    / resume_name
                    / image_file.name
                )

                relative_path = str(
                    relative_path
                ).replace(
                    "\\",
                    "/"
                )

                image_marker = (
                    f"[IMAGE: "
                    f"{relative_path}"
                    f"]"
                )

                # --------------------------------------------
                # INSERT IMAGE MARKER EXACTLY AT THE
                # IMAGE'S POSITION IN THE BLOCK ORDER
                # --------------------------------------------

                page_output.append(
                    image_marker
                )

        # ----------------------------------------------------
        # Add page content
        #
        # No "PAGE 1", "PAGE 2", etc.
        # ----------------------------------------------------

        for item in page_output:

            if item.strip():

                all_output.append(
                    item
                )

    # ========================================================
    # FINAL TEXT
    # ========================================================

    final_text = "\n".join(
        all_output
    )

    # --------------------------------------------------------
    # Remove excessive blank lines
    #
    # We don't remove actual text.
    # --------------------------------------------------------

    final_text = re.sub(
        r"\n{3,}",
        "\n\n",
        final_text
    )

    final_text = final_text.strip()

    # ========================================================
    # SAVE TEXT
    # ========================================================

    with open(
        text_output_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            final_text
        )

        if final_text:
            f.write("\n")

    # ========================================================
    # STATISTICS
    # ========================================================

    print(
        f"  Characters extracted: "
        f"{len(final_text)}"
    )

    if saved_images:

        print(
            f"  Images found: "
            f"{len(saved_images)}"
        )

        for image_file in saved_images:

            print(
                f"     Saved: "
                f"{image_file}"
            )

    else:

        print(
            "  Images found: 0"
        )

    print(
        f"  Text saved: "
        f"{text_output_file.name}"
    )

    print(
        "  Done"
    )

    document.close()

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Create only the main extracted folder.
    #
    # images/ will be created only if a meaningful image
    # is actually found.
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    pdf_files = sorted(
        INPUT_DIR.glob("*.pdf"),
        key=lambda x: x.name.lower()
    )

    print("=" * 70)
    print("RESUME EXTRACTION")
    print("=" * 70)

    print()
    print(
        f"Input folder : "
        f"{INPUT_DIR.resolve()}"
    )

    print(
        f"Output folder: "
        f"{OUTPUT_DIR.resolve()}"
    )

    print(
        f"Found {len(pdf_files)} PDF files"
    )

    if not pdf_files:

        print()
        print(
            "ERROR: No PDF files found."
        )

        print(
            f"Put your resumes inside: "
            f"{INPUT_DIR.resolve()}"
        )

        return

    successful = 0

    # ========================================================
    # PROCESS ALL RESUMES
    # ========================================================

    for pdf_file in pdf_files:

        try:

            if extract_pdf(
                pdf_file
            ):

                successful += 1

        except Exception as e:

            print()
            print(
                f"ERROR processing "
                f"{pdf_file.name}: {e}"
            )

    # ========================================================
    # COMPLETE
    # ========================================================

    print()
    print("=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)

    print(
        f"Successfully processed: "
        f"{successful}/{len(pdf_files)}"
    )

    print(
        f"Output: "
        f"{OUTPUT_DIR.resolve()}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()