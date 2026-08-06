import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from weasyprint import HTML

st.set_page_config(page_title="مقياس الخطبة الذكي", layout="centered")

st.title("💍 مقياس الخطبة الذكي - نظام المطابقة الخبير")
st.write("الإصدار الأحدث: يدمج حساب التوافق (Gap Analysis) مع حواجز الحماية وتوليد تقارير PDF.")
st.markdown("---")

eval_name = st.text_input("📝 أدخل اسماً أو رمزاً لهذا التقييم (ليظهر في التقرير):", "تقييم خطبة رقم 1")

# --- القواميس (Scenarios) ---
religion_levels = {
    "مسلم بالاسم (غير ملتزم بالفرائض)": 1,
    "مسلم عادي (يؤدي الفرائض الأساسية)": 2,
    "مسلم ملتزم (صلاة دائمة، التزام بالسنن)": 3,
    "شديد الالتزام (طالب علم، تدين عالي)": 4
}

awareness_levels = {
    "سطحي (الاهتمام بالمظاهر فقط)": 1,
    "وعي متوسط (إدارة حياة طبيعية)": 2,
    "مثقف وواعي جداً (عمق فكري)": 3
}

st.header("1. من أنت؟ (تحديد نقطة الأساس)")
st.info("💡 النظام يحتاج لمعرفة مستواك ليحسب 'الفجوة' والتوافق بينك وبين المخطوبة.")
guy_rel = st.selectbox("كيف تصنف التزامك الديني؟", list(religion_levels.keys()))
guy_awa = st.selectbox("كيف تصنف مستوى وعيك؟", list(awareness_levels.keys()))

st.markdown("---")

st.header("2. تقييم المخطوبة")
st.subheader("أ. التوافق الديني والفكري (حساب الفجوة)")
girl_rel = st.selectbox("ما هو الوصف الأدق لحالتها الدينية؟", list(religion_levels.keys()))
girl_awa = st.selectbox("ما هو الوصف الأدق لمستوى وعيها؟", list(awareness_levels.keys()))

st.subheader("ب. الصفات التراكمية الأخرى (من 1 إلى 10)")
other_traits = ["الحياء", "الطاعة", "الجمال", "النظافة", "القرابة"]
weight_options = {"عادي": 1, "مهم": 3, "مهم جداً": 5}

raw_scores = {}
weights = {}

# تحديد أوزان الدين والوعي أيضاً
st.markdown("**حدد أهمية (الدين) و(الوعي) بالنسبة لك كأوزان في المعادلة:**")
col_w1, col_w2 = st.columns(2)
with col_w1:
    weights["الدين"] = weight_options[st.selectbox("أهمية (الدين):", list(weight_options.keys()), index=2)]
with col_w2:
    weights["الوعي"] = weight_options[st.selectbox("أهمية (الوعي):", list(weight_options.keys()), index=1)]

st.markdown("**قيم باقي الصفات وحدد أهميتها:**")
for trait in other_traits:
    c1, c2 = st.columns([2, 1])
    with c1:
        raw_scores[trait] = st.slider(f"تقييم ({trait}):", 1, 10, 5)
    with c2:
        user_choice = st.selectbox(f"أهمية ({trait}):", list(weight_options.keys()), index=1, key=f"w_{trait}")
        weights[trait] = weight_options[user_choice]

st.markdown("---")
st.header("3. حواجز الحماية (Guardrails)")
minimum_threshold = st.slider("الحد الأدنى المقبول لأي صفة لتجنب التعويض الأعمى:", 1, 10, 4)
st.markdown("---")

if st.button("🧮 احسب التوافق واستخرج التقرير", use_container_width=True):
    # 1. حساب الفجوة للدين والوعي
    rel_gap = abs(religion_levels[guy_rel] - religion_levels[girl_rel])
    awa_gap = abs(awareness_levels[guy_awa] - awareness_levels[girl_awa])
    
    # تحويل الفجوة إلى علامة من 10 لتتناسب مع المخطط الراداري
    def gap_to_score(gap):
        if gap == 0: return 10
        elif gap == 1: return 7
        elif gap == 2: return 4
        else: return 1
        
    final_scores = {}
    final_scores["الدين"] = gap_to_score(rel_gap)
    final_scores["الوعي"] = gap_to_score(awa_gap)
    
    # إضافة باقي العلامات
    for t in other_traits:
        final_scores[t] = raw_scores[t]
        
    all_traits = ["الدين", "الوعي"] + other_traits
    
    # 2. الحساب النهائي للنسبة المئوية
    weighted_sum = sum(final_scores[t] * weights[t] for t in all_traits)
    max_possible_sum = sum(10 * weights[t] for t in all_traits)
    final_percentage = (weighted_sum / max_possible_sum) * 100
    
    # 3. التحقق من الفيتو وحواجز الحماية
    failed_traits = [t for t, s in final_scores.items() if s < minimum_threshold]
    
    if rel_gap >= 2:
        status_msg = "🚫 مرفوضة (فجوة دينية كبيرة - اختلاف جذري في الالتزام قد يسبب مشاكل)"
        color = "#d32f2f"
        final_percentage = 0  # تصفير النسبة كعقوبة (فيتو)
    elif awa_gap >= 2:
        status_msg = "🚫 مرفوضة (فجوة فكرية كبيرة - صعوبة شديدة في التفاهم)"
        color = "#d32f2f"
        final_percentage = 0
    elif failed_traits:
        status_msg = f"🛑 مرفوضة لوجود ضعف كارثي (تحت الحد المسموح) في: {', '.join(failed_traits)}"
        color = "#d32f2f"
    elif final_percentage >= 70:
        status_msg = "🎉 مقبولة، توافق ممتاز، توكل على الله!"
        color = "#388e3c"
    else:
        status_msg = "⚠️ غير مقبولة (نسبة التوافق الإجمالية ضعيفة)"
        color = "#f57c00"

    st.header(f"نسبة التوافق النهائية: {final_percentage:.1f}%")
    st.markdown(f"**القرار الآلي:** <span style='color:{color}; font-size:18px;'>{status_msg}</span>", unsafe_allow_html=True)
    
    # --- رسم المخطط الراداري ---
    categories = list(final_scores.keys())
    values = list(final_scores.values())
    categories.append(categories[0])
    values.append(values[0])
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values, theta=categories, fill='toself',
        marker=dict(color='indigo', size=8), line=dict(color='indigo', width=2)
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False, margin=dict(l=40, r=40, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # --- توليد تقرير PDF فخم (عبر HTML & CSS و WeasyPrint) ---
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    table_rows = ""
    for t in all_traits:
        importance = list(weight_options.keys())[list(weight_options.values()).index(weights[t])]
        table_rows += f"<tr><td>{t}</td><td>{final_scores[t]} / 10</td><td>{importance}</td></tr>"

    html_template = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
            @page {{ size: A4; margin: 15mm; }}
            body {{ font-family: 'Cairo', sans-serif; padding: 10px; color: #333; }}
            .header {{ text-align: center; border-bottom: 2px solid {color}; padding-bottom: 10px; margin-bottom: 20px; }}
            .header h1 {{ color: {color}; margin: 0; margin-bottom: 15px; }}
            .info-table {{ width: 100%; border: none; margin-bottom: 10px; font-size: 14px; }}
            .info-table td {{ border: none; padding: 5px; background: transparent; }}
            .summary {{ background-color: #f9f9f9; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #ddd; margin-bottom: 30px; }}
            .summary h2 {{ margin: 0 0 10px 0; color: #333; }}
            .data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 16px; }}
            .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
            .data-table th {{ background-color: #f1f1f1; color: #333; }}
            .footer {{ text-align: center; margin-top: 40px; font-size: 12px; color: #777; border-top: 1px solid #eee; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>💍 تقرير مقياس التوافق للخطبة</h1>
            <table class="info-table">
                <tr>
                    <td style="text-align: right; width: 50%;"><strong>رمز التقييم:</strong> {eval_name}</td>
                    <td style="text-align: left; width: 50%;"><strong>تاريخ التقييم:</strong> {current_date}</td>
                </tr>
            </table>
        </div>
        
        <div class="summary">
            <h2>نسبة التوافق النهائية: {final_percentage:.1f}%</h2>
            <h3 style="color: {color}; margin: 0;">القرار الآلي: {status_msg}</h3>
            <p style="font-size: 14px; color: #666; margin-top: 10px;">يعتمد هذا التقييم المتقدم على خوارزمية حساب الفجوة (Gap Analysis) بين نقطة أساس الشاب وواقع المخطوبة.</p>
        </div>
        
        <h3 style="color: #444;">تفاصيل التقييم والأوزان:</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>الصفة</th>
                    <th>علامة التوافق (من 10)</th>
                    <th>درجة الأهمية (الوزن)</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p>تم توليد هذا التقرير آلياً بواسطة النظام الخبير | AI Expert Matching Engine</p>
        </div>
    </body>
    </html>
    """

    try:
        pdf_bytes = HTML(string=html_template).write_pdf()
        st.download_button(
            label="📄 تحميل التقرير كملف PDF مرتب",
            data=pdf_bytes,
            file_name=f"Report_Match_{eval_name}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"حدث خطأ أثناء توليد الـ PDF: {e}")