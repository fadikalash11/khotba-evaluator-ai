import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from weasyprint import HTML  # استخدمنا المكتبة الحديثة بدل pdfkit

st.set_page_config(page_title="مقياس الخطبة الذكي", layout="centered")

st.title("💍 مقياس الخطبة الذكي - الإصدار الاحترافي")
st.write("نظام خبير يدمج الفلاتر الشرعية، حواجز الحماية، وتوليد تقارير PDF.")
st.markdown("---")

eval_name = st.text_input("📝 أدخل اسماً أو رمزاً لهذا التقييم (ليظهر في التقرير):", "تقييم خطبة رقم 1")

st.header("1. الشروط الأساسية (لا مساومة عليها)")
col1, col2 = st.columns(2)
with col1:
    islam_input = st.radio("الإسلام (الدين):", ["متوفر", "غير متوفر"], index=1)
    c_islam = 1 if islam_input == "متوفر" else 0
with col2:
    salah_input = st.radio("الصلاح والأخلاق:", ["متوفر", "غير متوفر"], index=1)
    c_salah = 1 if salah_input == "متوفر" else 0

st.markdown("---")

st.header("2. الصفات التراكمية والأولويات")
traits = ["الوعي", "الحياء", "الطاعة", "الجمال", "الحسب", "النظافة", "القرابة"]
weight_options = {"عادي": 1, "مهم": 3, "مهم جداً": 5}
scores = {}
weights = {}

for trait in traits:
    c1, c2 = st.columns([2, 1])
    with c1:
        scores[trait] = st.slider(f"تقييم ({trait}):", 1, 10, 5, key=f"s_{trait}")
    with c2:
        user_choice = st.selectbox(f"أهمية ({trait}):", options=list(weight_options.keys()), index=1, key=f"w_{trait}")
        weights[trait] = weight_options[user_choice]

st.markdown("---")
st.header("3. حواجز الحماية (Guardrails)")
minimum_threshold = st.slider("الحد الأدنى المقبول لأي صفة لتجنب التعويض الأعمى:", 1, 10, 4)
st.markdown("---")

if st.button("🧮 احسب النتيجة واستخرج التقرير", use_container_width=True):
    weighted_sum = sum(scores[t] * weights[t] for t in traits)
    max_possible_sum = sum(10 * weights[t] for t in traits)
    final_score = c_islam * c_salah * weighted_sum
    final_percentage = (final_score / max_possible_sum) * 100
    
    # تحديد حالة القبول
    failed_traits = [t for t, s in scores.items() if s < minimum_threshold]
    
    if final_percentage == 0:
        status_msg = "مرفوضة قاطعاً (غياب شرط الدين أو الصلاح)"
        color = "#d32f2f" # أحمر
    elif failed_traits:
        status_msg = f"مرفوضة لوجود ضعف كارثي في: {', '.join(failed_traits)}"
        color = "#d32f2f" # أحمر
    elif final_percentage >= 70:
        status_msg = "مقبولة، توكل على الله!"
        color = "#388e3c" # أخضر
    else:
        status_msg = "غير مقبولة (التقييم الإجمالي ضعيف)"
        color = "#f57c00" # برتقالي

    st.header(f"النتيجة النهائية: {final_percentage:.1f}%")
    st.markdown(f"**القرار الآلي:** <span style='color:{color}; font-size:18px;'>{status_msg}</span>", unsafe_allow_html=True)
    
    # --- رسم المخطط الراداري ---
    categories = list(scores.keys())
    values = list(scores.values())
    categories.append(categories[0])
    values.append(values[0])
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values, theta=categories, fill='toself',
        marker=dict(color='indigo', size=8), line=dict(color='indigo', width=2)
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False, margin=dict(l=40, r=40, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # --- توليد تقرير PDF فخم (عبر HTML & CSS) ---
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # تجهيز صفوف الجدول
    table_rows = ""
    for t in traits:
        importance = list(weight_options.keys())[list(weight_options.values()).index(weights[t])]
        table_rows += f"<tr><td>{t}</td><td>{scores[t]} / 10</td><td>{importance}</td></tr>"

    # تصميم قالب HTML معدل لمنع تداخل الحروف ويتوافق مع WeasyPrint
    html_template = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
            
            /* إعدادات صفحة الطباعة لـ WeasyPrint */
            @page {{
                size: A4;
                margin: 15mm;
            }}
            
            body {{ font-family: 'Cairo', sans-serif; padding: 10px; color: #333; }}
            
            /* تنسيق الترويسة */
            .header {{ text-align: center; border-bottom: 2px solid {color}; padding-bottom: 10px; margin-bottom: 20px; }}
            .header h1 {{ color: {color}; margin: 0; margin-bottom: 15px; }}
            
            /* جدول مخفي للمعلومات لمنع تداخل النصوص */
            .info-table {{ width: 100%; border: none; margin-bottom: 10px; font-size: 14px; }}
            .info-table td {{ border: none; padding: 5px; background: transparent; }}
            
            .summary {{ background-color: #f9f9f9; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #ddd; margin-bottom: 30px; }}
            .summary h2 {{ margin: 0 0 10px 0; color: #333; }}
            
            /* جدول التقييم */
            .data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 16px; }}
            .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
            .data-table th {{ background-color: #f1f1f1; color: #333; }}
            
            .footer {{ text-align: center; margin-top: 40px; font-size: 12px; color: #777; border-top: 1px solid #eee; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>💍 تقرير مقياس الخطبة الذكي</h1>
            <!-- استخدمنا جدول هنا لعزل الرمز عن التاريخ برمجياً -->
            <table class="info-table">
                <tr>
                    <td style="text-align: right; width: 50%;"><strong>رمز التقييم:</strong> {eval_name}</td>
                    <td style="text-align: left; width: 50%;"><strong>تاريخ التقييم:</strong> {current_date}</td>
                </tr>
            </table>
        </div>
        
        <div class="summary">
            <h2>النسبة النهائية: {final_percentage:.1f}%</h2>
            <h3 style="color: {color}; margin: 0;">القرار الآلي: {status_msg}</h3>
        </div>
        
        <h3 style="color: #444;">تفاصيل التقييم والأوزان:</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>الصفة</th>
                    <th>التقييم (من 10)</th>
                    <th>درجة الأهمية (الوزن)</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p>تم توليد هذا التقرير آلياً بواسطة النظام الخبير | AI Expert System</p>
        </div>
    </body>
    </html>
    """

    # تحويل الـ HTML إلى PDF باستخدام WeasyPrint
    try:
        pdf_bytes = HTML(string=html_template).write_pdf()
        
        st.download_button(
            label="📄 تحميل التقرير كملف PDF مرتب",
            data=pdf_bytes,
            file_name=f"Report_{eval_name}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"حدث خطأ أثناء توليد الـ PDF: {e}")
