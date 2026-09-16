import os
import shutil

BASE_DIR = r"C:\Users\Sudeep M\Documents\Project Antigravity"
DASHBOARD_DIR = os.path.join(BASE_DIR, "projects", "rainprediction_codesis", "dashboard")
FRAMES_DIR = os.path.join(BASE_DIR, ".clario", "frames")

os.makedirs(DASHBOARD_DIR, exist_ok=True)

src_html = os.path.join(FRAMES_DIR, "rain_prediction_dashboard.html")
src_js = os.path.join(FRAMES_DIR, "rain_data.js")

dst_html = os.path.join(DASHBOARD_DIR, "index.html")
dst_js = os.path.join(DASHBOARD_DIR, "rain_data.js")

print("1. Copying rain_data.js...")
shutil.copyfile(src_js, dst_js)
print(f"Copied to: {dst_js}")

print("2. Reading dashboard HTML...")
with open(src_html, "r", encoding="utf-8") as f:
    html_content = f.read()

# Enhance HTML with EDA Insights Drawer / Banner
eda_banner_html = """
  <!-- EDA & Climatological Insights Accordion / Panel -->
  <div class="chart-panel" style="margin-bottom: 24px; border: 1px solid rgba(59, 130, 246, 0.3); background: linear-gradient(180deg, rgba(17, 24, 39, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);">
    <div class="chart-header" style="cursor: pointer;" onclick="toggleEdaPanel()">
      <div class="chart-title" style="color: #60a5fa; font-size: 16px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
        Key Exploratory Data Analysis (EDA) & Climatological Discoveries
        <span style="font-size: 11px; padding: 2px 8px; border-radius: 12px; background: rgba(59, 130, 246, 0.2); color: #93c5fd; margin-left: 8px;">115-Year Synthesis</span>
      </div>
      <span id="edaToggleBtn" style="font-size: 13px; font-weight: 600; color: #9ca3af;">▼ Click to View Insights</span>
    </div>
    
    <div id="edaContentBox" style="display: block; margin-top: 14px; border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 16px;">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px;">
        <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 14px;">
          <div style="font-size: 12px; font-weight: 700; color: #34d399; margin-bottom: 6px; text-transform: uppercase;">1. Extreme Spatial Disparity (76.4x)</div>
          <div style="font-size: 12px; color: #d1d5db; line-height: 1.5;">
            Wettest District: <b style="color: #67e8f9;">Tamenglong (Manipur, 7,229 mm)</b> &amp; Jaintia Hills (6,380 mm).<br>
            Driest District: <b style="color: #f87171;">Ladakh / Leh (94.6 mm)</b> &amp; Jaisalmer (181 mm).<br>
            Enormous 76-fold difference across India requires localized model scaling.
          </div>
        </div>

        <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 14px;">
          <div style="font-size: 12px; font-weight: 700; color: #f59e0b; margin-bottom: 6px; text-transform: uppercase;">2. Chronic Drought Belt &amp; Persistence</div>
          <div style="font-size: 12px; color: #d1d5db; line-height: 1.5;">
            West Rajasthan experiences drought in <b style="color: #fbbf24;">28.7% of years</b>; Saurashtra in 26.1%.<br>
            <b style="color: #f87171;">Multi-Year Drought Clustering:</b> If year t-1 was a drought, P(Drought in year t) jumps from 15.1% to <b>24.8% (+64% risk)</b>.
          </div>
        </div>

        <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 14px;">
          <div style="font-size: 12px; font-weight: 700; color: #60a5fa; margin-bottom: 6px; text-transform: uppercase;">3. June Onset Predictability (61.4%)</div>
          <div style="font-size: 12px; color: #d1d5db; line-height: 1.5;">
            When June rainfall suffers a severe deficit (&le; -25%), <b style="color: #93c5fd;">61.4% of historical seasons</b> ended in deficient or below-normal monsoon totals due to truncated moisture pumping.
          </div>
        </div>

        <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 14px;">
          <div style="font-size: 12px; font-weight: 700; color: #a78bfa; margin-bottom: 6px; text-transform: uppercase;">4. The Dual-Monsoon Decoupling</div>
          <div style="font-size: 12px; color: #d1d5db; line-height: 1.5;">
            Correlation between SW Monsoon (Jun-Sep) &amp; NE Monsoon (Oct-Dec) is <b style="color: #c4b5fd;">r = +0.041 (zero correlation)</b>.<br>
            Tamil Nadu &amp; Puducherry receive 50-70% of rain in Oct-Dec, decoupled from national summer droughts.
          </div>
        </div>
      </div>
    </div>
  </div>
"""

# Insert EDA banner just above the KPI Ribbon
kpi_marker = '<div class="kpi-grid">'
if kpi_marker in html_content and "toggleEdaPanel" not in html_content:
    html_content = html_content.replace(kpi_marker, eda_banner_html + "\n  " + kpi_marker)

# Add toggle script function if not present
toggle_fn = """
    function toggleEdaPanel() {
      const box = document.getElementById('edaContentBox');
      const btn = document.getElementById('edaToggleBtn');
      if (box.style.display === 'none') {
        box.style.display = 'block';
        btn.textContent = '▲ Click to Collapse';
      } else {
        box.style.display = 'none';
        btn.textContent = '▼ Click to View Insights';
      }
    }
"""

if "function toggleEdaPanel" not in html_content:
    script_close_marker = "</script>\n</body>"
    html_content = html_content.replace(script_close_marker, toggle_fn + "\n  " + script_close_marker)

print("3. Writing enhanced dashboard HTML to dashboard/index.html...")
with open(dst_html, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Saved to: {dst_html}")

# Also update the frame HTML
with open(src_html, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Updated frame: {src_html}")

print("\nDashboard setup completed successfully!")
