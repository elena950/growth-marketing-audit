#!/usr/bin/env python3
import os
import json
import argparse
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import textwrap
import re
from dotenv import load_dotenv

# ==========================
# LOAD ENV VARIABLES
# ==========================
load_dotenv()  # loads variables from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Set your OPENAI_API_KEY in environment variables or .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

# ==========================
# HELPERS
# ==========================
def scrape_website(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    texts = soup.stripped_strings
    return " ".join(texts)

def build_prompt(text, rubric):
    # Force GPT to only return JSON
    return (
        f"Analyze the following website text for Brand, Content, Website, and Marketing:\n\n{text}\n\n"
        f"Use this rubric: {json.dumps(rubric)}\n"
        "Return STRICT JSON ONLY with keys: Brand, Content, Website, Marketing.\n"
        "Each key must contain: grade (A+ to F), reasoning (string), quick_wins (list of strings)."
        "Provide a thoroughly detailed paragraph and actionable recommendations in the quick wins section and examples for each section"
    )

def analyze(text, rubric, model="gpt-4o-mini"):
    prompt = build_prompt(text, rubric)
    resp = client.responses.create(
        model=model,
        input=prompt,
        temperature=0.4
    )
    raw = resp.output_text

    # Extract JSON object from raw text
    try:
        json_match = re.search(r"(\{.*\})", raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        else:
            return {"error": "Could not parse JSON", "raw": raw}
    except Exception:
        return {"error": "Could not parse JSON", "raw": raw}

def safe_text(text):
    return str(text).replace("–", "-").replace("“", '"').replace("”", '"')

def wrap_text(text, width=90):
    return "\n".join(textwrap.wrap(text, width=width))

# ==========================
# BRANDED PDF GENERATION
# ==========================
import re
import textwrap
from fpdf import FPDF
import os

def sanitize_filename(name: str) -> str:
    """Sanitize website name to use as a valid filename."""
    return re.sub(r'[^\w\-_. ]', '_', name)

def build_pdf(audit, website_url, header_image="Growth_Marketing_Audit_Header.png",
              heading_font="Montserrat-ExtraBold.ttf", body_font="Montserrat-Medium.ttf",
              icon_paths=None):
    """
    Build a branded PDF audit report.
    audit: dict returned from generate_audit_report
    website_url: used to name the output file
    header_image: path to top header image
    heading_font: path to heading font TTF
    body_font: path to body font TTF
    icon_paths: dict mapping section name to icon filename
    """
    if icon_paths is None:
        icon_paths = {
            "Brand": "brand-icon.png",
            "Content": "content-icon.png",
            "Website": "build-icon.png",
            "Marketing": "grow-icon.png"
        }

    # Updated color map for grades
    grade_colors = {
        "A+": (68, 206, 27),
        "A": (68, 206, 27),
        "A-": (187, 219, 68),
        "B+": (187, 219, 68),
        "B": (187, 219, 68),
        "B-": (247, 227, 121),
        "C+": (247, 227, 121),
        "C": (247, 227, 121),
        "C-": (242, 161, 52),
        "D+": (242, 161, 52),
        "D": (242, 161, 52),
        "F": (229, 31, 31)
    }

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Background color
    pdf.set_fill_color(249, 249, 250)
    pdf.rect(0, 0, 210, 297, 'F')  # full page

    # Register fonts
    if heading_font and os.path.exists(heading_font):
        pdf.add_font("HeadingFont", "", heading_font, uni=True)
    if body_font and os.path.exists(body_font):
        pdf.add_font("BodyFont", "", body_font, uni=True)

    # Add header image
    if header_image and os.path.exists(header_image):
        pdf.image(header_image, x=0, y=0, w=210)  # full width

    pdf.ln(40)  # space after header image

    # Sections
    section_x = 20
    text_width = 170  # page width minus margins

    for section, details in audit.items():
        if isinstance(details, dict):
            grade = details.get("grade", "N/A")
            reasoning = details.get("reasoning", "")
            quick_wins = details.get("quick_wins", [])
        else:
            grade = "N/A"
            reasoning = str(details)
            quick_wins = []

        # Section icon
        icon_file = icon_paths.get(section)
        icon_width = 8
        icon_gap = 4
        y_start = pdf.get_y()
        if icon_file and os.path.exists(icon_file):
            pdf.image(icon_file, x=section_x, y=y_start, w=icon_width)
        title_x = section_x + (icon_width + icon_gap if icon_file else 0)

        # Section title
        if heading_font and os.path.exists(heading_font):
            pdf.set_font("HeadingFont", "", 16)
        else:
            pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(28, 28, 28)
        pdf.set_xy(title_x, y_start)
        pdf.cell(0, 8, f"{section} - ", ln=False)

        # Letter grade (colored) aligned to right margin
        pdf.set_text_color(*grade_colors.get(grade, (28, 28, 28)))
        pdf.set_xy(section_x + text_width - 15, y_start)  # right-align grade
        pdf.cell(15, 8, grade, ln=True, align="R")

        pdf.ln(6)  # extra space between title and reasoning

        # Reasoning - make cohesive by removing existing line breaks
        if body_font and os.path.exists(body_font):
            pdf.set_font("BodyFont", "", 11)
        else:
            pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(28, 28, 28)
        reasoning_clean = " ".join(reasoning.splitlines())
        pdf.set_x(section_x)
        pdf.multi_cell(text_width, 6, reasoning_clean)
        pdf.ln(3)

        # Quick wins
        if quick_wins:
            if heading_font and os.path.exists(heading_font):
                pdf.set_font("HeadingFont", "", 13)
            else:
                pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(28, 28, 28)
            pdf.set_x(section_x)
            pdf.cell(0, 6, "Quick Wins:", ln=True)
            pdf.set_font("BodyFont" if body_font and os.path.exists(body_font) else "Helvetica", "", 10)
            pdf.set_text_color(28, 28, 28)
            for q in quick_wins:
                q_wrapped = textwrap.fill(f"- {q}", width=110)
                pdf.set_x(section_x)  # reset x for each bullet line
                pdf.multi_cell(text_width, 6, q_wrapped)
            pdf.ln(6)

    # Output file name based on website
    sanitized_name = sanitize_filename(website_url)
    out_file = f"audit_{sanitized_name}.pdf"
    pdf.output(out_file)
    return out_file


# ==========================
# STREAMLIT ENTRYPOINT
# ==========================
def generate_audit_report(website_url: str, model="gpt-4o-mini"):
    """You are a senior digital marketing strategist conducting a critical growth marketing audit. 
    Do not sugarcoat or give generic advice — be direct, constructive, and specific. 
    Highlight what is NOT working, what is missing, and where {business_name} is likely losing opportunities."""
    text = scrape_website(website_url)
    rubric = {
        "Brand": "Is the brand positioning clear and differentiated? If not, what’s confusing or weak? Where does the messaging fail to connect with the intended audience? Critique tone, clarity, and trust signals. Provide sharper alternatives.",
        "Content": "Point out missing or poorly optimized elements: meta tags, keyword targeting, content depth. Identify weaknesses compared to industry best practices (e.g., lack of authority content, weak internal linking). Suggest exactly what types of content should be created or improved",
        "Website": "Critically evaluate navigation, mobile performance, and calls-to-action. Identify friction points that would cause a visitor to bounce or fail to convert. Be blunt about design flaws, clutter, or poor layout choices. Recommend fixes.",
        "Marketing": "- Call out channels the business is underutilizing (paid ads, email nurture, partnerships, retargeting). Highlight quick wins that could drive immediate ROI. Provide bold, high-impact recommendations for scaling growth — even if they require major changes.  "
    }
    audit = analyze(text, rubric, model=model)
    return audit

# ==========================
# CLI ENTRYPOINT
# ==========================
def main():
    parser = argparse.ArgumentParser(description="Growth Marketing Audit")
    parser.add_argument("--url", required=True, help="Website URL to audit")
    parser.add_argument("--out", default="audit.pdf", help="Output PDF file")
    parser.add_argument("--logo", help="Path to logo image")
    parser.add_argument("--heading-font", help="Path to Soleil Extra Bold .ttf")
    parser.add_argument("--body-font", help="Path to Montserrat Medium .ttf")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model")
    args = parser.parse_args()

    audit = generate_audit_report(args.url, model=args.model)
    print("Generating PDF...")
    build_pdf(
        audit,
        args.out,
        logo_path=args.logo,
        heading_font=args.heading_font,
        body_font=args.body_font
    )

if __name__ == "__main__":
    main()
