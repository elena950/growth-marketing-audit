import streamlit as st
from audit_mvp import generate_audit_report, build_pdf
import base64
import os
import re
import tempfile

st.set_page_config(page_title="Growth Marketing Audit", layout="wide")

# ==========================
# LOAD CUSTOM FONTS
# ==========================
def load_font_as_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

montserrat_medium_base64 = load_font_as_base64("Montserrat-Medium.ttf")
montserrat_extrabold_base64 = load_font_as_base64("Montserrat-ExtraBold.ttf")

st.markdown(f"""
    <style>
        @font-face {{
            font-family: 'Montserrat';
            src: url(data:font/ttf;base64,{montserrat_medium_base64}) format('truetype');
            font-weight: 500;
            font-style: normal;
        }}
        @font-face {{
            font-family: 'Montserrat';
            src: url(data:font/ttf;base64,{montserrat_extrabold_base64}) format('truetype');
            font-weight: 800;
            font-style: normal;
        }}
        body {{
            background-color: #f9f9fa;
            color: #1c1c1c;
            font-family: 'Montserrat', sans-serif;
            font-weight: 500;
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Montserrat', sans-serif;
            font-weight: 800;
            color: #1c1c1c;
        }}
    </style>
""", unsafe_allow_html=True)

# ==========================
# STREAMLIT UI
# ==========================
st.title("🚀 Growth Marketing Audit")
st.write("Enter a website URL to generate a quick audit report.")

website_url = st.text_input("Website URL")

if st.button("Generate Audit"):
    if not website_url:
        st.error("Please enter a website URL before generating the audit.")
    else:
        with st.spinner("Generating your audit report..."):
            report = generate_audit_report(website_url)

        if report and isinstance(report, dict):
            st.success("✅ Audit complete!")
            
            for section, details in report.items():
                if isinstance(details, dict):
                    st.subheader(f"{section} – Grade: {details.get('grade','N/A')}")
                    st.write(details.get("reasoning", "No reasoning available."))
                    if details.get("quick_wins"):
                        st.markdown("**Quick Wins:**")
                        for q in details["quick_wins"]:
                            st.write(f"- {q}")
                else:
                    st.subheader(section)
                    st.write(details)

            # ==========================
            # GENERATE PDF
            # ==========================
            # Clean website URL to create safe file name
            safe_site_name = re.sub(r"[^\w\-]", "_", website_url.split("//")[-1].split("/")[0])
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, f"{safe_site_name}_audit.pdf")

            # Build the PDF
            pdf_file = build_pdf(
                report,
                pdf_path,
                header_image="Growth_Marketing_Audit_Header.png",
                heading_font="Montserrat-ExtraBold.ttf",
                body_font="Montserrat-Medium.ttf"
            )

            # Provide download button
            if os.path.exists(pdf_file):
                with open(pdf_file, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label="📄 Download Audit PDF",
                    data=pdf_bytes,
                    file_name=f"{safe_site_name}_audit.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("⚠️ PDF generation failed. Please check your backend function.")

        else:
            st.error("⚠️ Audit report is invalid. Please check the backend function.")
