
# 📄 Converting Report to PDF

## Option 1: Using Pandoc (Recommended)

1. **Install Pandoc:**
   ```bash
   # macOS
   brew install pandoc
   
   # Or download from: https://pandoc.org/installing.html
   ```

2. **Convert to PDF:**
   ```bash
   pandoc output/mukbang_viral_analysis_report.md -o output/mukbang_viral_analysis_report.pdf --pdf-engine=xelatex -V geometry:margin=1in
   ```

## Option 2: Using Online Converters

1. **Copy the markdown content** from `output/mukbang_viral_analysis_report.md`
2. **Visit:** https://md-to-pdf.fly.dev/ or https://www.markdowntopdf.com/
3. **Paste the content** and download the PDF

## Option 3: Using VS Code

1. **Install the "Markdown PDF" extension**
2. **Open** `output/mukbang_viral_analysis_report.md`
3. **Press Ctrl+Shift+P** (Cmd+Shift+P on Mac)
4. **Type "Markdown PDF: Export (pdf)"** and press Enter

## Option 4: Using Python (if you have weasyprint)

```bash
pip install weasyprint markdown
python -c "
import markdown
from weasyprint import HTML
with open('output/mukbang_viral_analysis_report.md', 'r') as f:
    md_content = f.read()
html_content = markdown.markdown(md_content)
HTML(string=html_content).write_pdf('output/mukbang_viral_analysis_report.pdf')
"
```
