import markdown
from xhtml2pdf import pisa

README = "README.md"
OUTPUT = "NewsGenie_README.pdf"

CSS_STYLES = """
@page {
    size: A4;
    margin: 2cm 2.2cm 2cm 2.2cm;
}

body {
    font-family: Arial, 'Helvetica Neue', sans-serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #1f2937;
}

h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #1e40af;
    border-bottom: 2px solid #2563eb;
    padding-bottom: 4px;
    margin-top: 14pt;
    margin-bottom: 6pt;
}

h2 {
    font-size: 14pt;
    font-weight: bold;
    color: #1d4ed8;
    border-bottom: 1px solid #bfdbfe;
    padding-bottom: 2px;
    margin-top: 14pt;
    margin-bottom: 5pt;
}

h3 {
    font-size: 11.5pt;
    font-weight: bold;
    color: #1e40af;
    margin-top: 10pt;
    margin-bottom: 4pt;
}

h4 {
    font-size: 10.5pt;
    font-weight: bold;
    color: #374151;
    margin-top: 8pt;
}

p { margin: 4pt 0; }

a { color: #2563eb; }

code {
    font-family: 'Courier New', Courier, monospace;
    font-size: 9pt;
    background: #f1f5f9;
    color: #0f172a;
    padding: 1px 4px;
    border-radius: 3px;
}

pre {
    background: #1e293b;
    color: #e2e8f0;
    padding: 10px 14px;
    border-radius: 5px;
    font-size: 8.5pt;
    font-family: 'Courier New', Courier, monospace;
    line-height: 1.5;
    margin: 6pt 0;
}

pre code {
    background: transparent;
    color: #e2e8f0;
    padding: 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 8pt 0;
    font-size: 9.5pt;
}

th {
    background-color: #1d4ed8;
    color: #ffffff;
    font-weight: bold;
    padding: 6px 10px;
    text-align: left;
}

td {
    padding: 5px 10px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
}

tr.even td { background-color: #f8fafc; }

ul, ol {
    padding-left: 18pt;
    margin: 4pt 0;
}

li { margin: 2pt 0; }

blockquote {
    border-left: 4px solid #2563eb;
    background: #eff6ff;
    padding: 6px 12px;
    margin: 6pt 0;
    color: #1e40af;
    font-style: italic;
}

hr {
    border-top: 1px solid #e5e7eb;
    margin: 10pt 0;
}
"""


def build_pdf():
    with open(README, "r", encoding="utf-8") as f:
        md_text = f.read()

    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "nl2br"],
    )

    # Stripe table rows via post-processing
    import re
    row_count = [0]
    def stripe_row(m):
        row_count[0] += 1
        cls = "even" if row_count[0] % 2 == 0 else "odd"
        return f'<tr class="{cls}">'
    html_body = re.sub(r"<tr>", stripe_row, html_body)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <style>{CSS_STYLES}</style>
</head>
<body>
{html_body}
</body>
</html>"""

    with open(OUTPUT, "wb") as pdf_file:
        result = pisa.CreatePDF(full_html, dest=pdf_file)

    if result.err:
        print(f"PDF generation had errors: {result.err}")
    else:
        print(f"PDF saved: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
