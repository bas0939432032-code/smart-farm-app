import os
import subprocess
import sys

print("🚀 เริ่มต้นกระบวนการสร้างและติดตั้ง Smart Farm System...")

# 1. สร้างไฟล์ requirements.txt
requirements_content = """streamlit
pandas
plotly
"""
with open("requirements.txt", "w", encoding="utf-8") as f:
    f.write(requirements_content)
print("✅ 1/4 สร้างไฟล์ requirements.txt เรียบร้อย")

# 2. สร้างไฟล์ database.py
database_content = """import sqlite3

def init_db():
    conn = sqlite3.connect('smart_farm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS farms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, location TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS plots 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, farm_id INTEGER, name TEXT, area_sqm REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS crops 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, plot_id INTEGER, name TEXT, plant_date TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sensors 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, plot_id INTEGER, type TEXT, value REAL, timestamp DATETIME DEFAULT (datetime('now','localtime')))''')
    c.execute('''CREATE TABLE IF NOT EXISTS irrigation 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, plot_id INTEGER, mode TEXT, status TEXT, update_time DATETIME DEFAULT (datetime('now','localtime')))''')
    c.execute('''CREATE TABLE IF NOT EXISTS harvest 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, crop_id INTEGER, harvest_date TEXT, yield_kg REAL, revenue REAL)''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
"""
with open("database.py", "w", encoding="utf-8") as f:
    f.write(database_content)
print("✅ 2/4 สร้างไฟล์ database.py เรียบร้อย")

# 3. สร้างไฟล์ app.py
app_content = '''import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from database import init_db

init_db()

st.set_page_config(page_title="ระบบจัดการฟาร์มอัจฉริยะ", layout="wide", page_icon="🌱")
st.title("🌱 ระบบจัดการฟาร์มอัจฉริยะ (Smart Farm Management System)")

def get_connection():
    return sqlite3.connect('smart_farm.db')

conn = get_connection()

st.sidebar.header("📌 เมนูหลัก")
menu = ["📊 ภาพรวม (Dashboard)", 
        "🏡 จัดการฟาร์ม & แปลง (Farm & Plot)", 
        "🌾 พืชผล (Crop)", 
        "📡 ข้อมูลเซนเซอร์ (Sensor)", 
        "💦 ระบบรดน้ำ (Irrigation)", 
        "🛒 การเก็บเกี่ยว (Harvest)"]
choice = st.sidebar.radio("เลือกเมนูการทำงาน:", menu)

def get_farms(): return pd.read_sql("SELECT * FROM farms", conn)
def get_plots(): return pd.read_sql("SELECT * FROM plots", conn)
def get_crops(): return pd.read_sql("SELECT * FROM crops", conn)

if choice == "📊 ภาพรวม (Dashboard)":
    st.subheader("📊 สรุปข้อมูลภาพรวมฟาร์ม")
    col1, col2, col3, col4 = st.columns(4)
    
    farms_cnt = pd.read_sql("SELECT COUNT(*) as cnt FROM farms", conn).iloc[0]['cnt']
    plots_cnt = pd.read_sql("SELECT COUNT(*) as cnt FROM plots", conn).iloc[0]['cnt']
    crops_cnt = pd.read_sql("SELECT COUNT(*) as cnt FROM crops WHERE status='กำลังปลูก'", conn).iloc[0]['cnt']
    total_yield = pd.read_sql("SELECT SUM(yield_kg) as total FROM harvest", conn).iloc[0]['total'] or 0

    col1.metric("จำนวนฟาร์มทั้งหมด", f"{farms_cnt} แห่ง")
    col2.metric("จำนวนแปลงปลูก", f"{plots_cnt} แปลง")
    col3.metric("พืชที่กำลังปลูก", f"{crops_cnt} รายการ")
    col4.metric("ผลผลิตรวมสะสม", f"{total_yield:,.2f} กก.")

    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📈 แนวโน้มข้อมูลเซนเซอร์ล่าสุด")
        sensor_df = pd.read_sql("SELECT * FROM sensors ORDER BY timestamp DESC LIMIT 50", conn)
        if not sensor_df.empty:
            fig = px.line(sensor_df, x='timestamp', y='value', color='type', markers=True, title="แนวโน้มเซนเซอร์ (ความชื้น/อุณหภูมิ)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ยังไม่มีข้อมูลเซนเซอร์ในระบบ")

    with col_chart2:
        st.subheader("💰 สรุปรายได้จากการเก็บเกี่ยว")
        harvest_df = pd.read_sql("SELECT * FROM harvest", conn)
        if not harvest_df.empty:
            fig2 = px.bar(harvest_df, x='harvest_date', y='revenue', title="รายได้ตามวันเก็บเกี่ยว (บาท)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("ยังไม่มีข้อมูลการเก็บเกี่ยว")

elif choice == "🏡 จัดการฟาร์ม & แปลง (Farm & Plot)":
    st.subheader("🏡 จัดการข้อมูลฟาร์มและแปลงปลูก")
    tab1, tab2 = st.tabs(["📌 เพิ่มฟาร์มใหม่", "🔲 เพิ่มแปลงปลูก"])
    
    with tab1:
        with st.form("add_farm"):
            f_name = st.text_input("ชื่อฟาร์ม")
            f_loc = st.text_input("สถานที่ตั้ง / จังหวัด")
            if st.form_submit_button("บันทึกข้อมูลฟาร์ม"):
                if f_name:
                    conn.execute("INSERT INTO farms (name, location) VALUES (?, ?)", (f_name, f_loc))
                    conn.commit()
                    st.success(f"เพิ่มฟาร์ม '{f_name}' สำเร็จ!")
                    st.rerun()
                else:
                    st.error("กรุณากรอกชื่อฟาร์ม")
        
        st.write("รายชื่อฟาร์มที่มีในระบบ:")
        st.dataframe(get_farms(), use_container_width=True)

    with tab2:
        farms_df = get_farms()
        if not farms_df.empty:
            with st.form("add_plot"):
                farm_id = st.selectbox("เลือกฟาร์ม", farms_df['id'].tolist(), format_func=lambda x: farms_df[farms_df['id']==x]['name'].values[0])
                p_name = st.text_input("ชื่อแปลงปลูก (เช่น แปลง A1)")
                p_area = st.number_input("ขนาดพื้นที่ (ตารางเมตร)", min_value=1.0)
                if st.form_submit_button("บันทึกแปลงปลูก"):
                    if p_name:
                        conn.execute("INSERT INTO plots (farm_id, name, area_sqm) VALUES (?, ?, ?)", (farm_id, p_name, p_area))
                        conn.commit()
                        st.success(f"เพิ่มแปลง '{p_name}' สำเร็จ!")
                        st.rerun()
                    else:
                        st.error("กรุณากรอกชื่อแปลงปลูก")
            
            st.write("รายชื่อแปลงปลูกที่มีในระบบ:")
            plots_df = pd.read_sql("SELECT plots.id, farms.name as farm_name, plots.name as plot_name, plots.area_sqm FROM plots JOIN farms ON plots.farm_id = farms.id", conn)
            st.dataframe(plots_df, use_container_width=True)
        else:
            st.warning("กรุณาเพิ่มฟาร์มในแท็บ 'เพิ่มฟาร์มใหม่' ก่อนสร้างแปลงปลูก")

elif choice == "🌾 พืชผล (Crop)":
    st.subheader("🌾 จัดการพืชผลที่ปลูก")
    plots_df = get_plots()
    
    if not plots_df.empty:
        with st.form("add_crop"):
            plot_id = st.selectbox("เลือกแปลงปลูก", plots_df['id'].tolist(), format_func=lambda x: plots_df[plots_df['id']==x]['name'].values[0])
            c_name = st.text_input("ชื่อพืช (เช่น เมล่อน, ผักสลัด, มะเขือเทศ)")
            p_date = st.date_input("วันที่เริ่มปลูก")
            status = st.selectbox("สถานะการปลูก", ["กำลังปลูก", "เก็บเกี่ยวแล้ว", "ยกเลิก/เสียหาย"])
            
            if st.form_submit_button("บันทึกข้อมูลพืชผล"):
                if c_name:
                    conn.execute("INSERT INTO crops (plot_id, name, plant_date, status) VALUES (?, ?, ?, ?)", (plot_id, c_name, str(p_date), status))
                    conn.commit()
                    st.success(f"เพิ่มพืช '{c_name}' ลงในแปลงเรียบร้อยแล้ว!")
                    st.rerun()
                else:
                    st.error("กรุณากรอกชื่อพืช")
        
        st.write("รายการพืชผลในฟาร์ม:")
        crops_display = pd.read_sql("SELECT crops.id, plots.name as plot_name, crops.name as crop_name, crops.plant_date, crops.status FROM crops JOIN plots ON crops.plot_id = plots.id", conn)
        st.dataframe(crops_display, use_container_width=True)
    else:
        st.warning("กรุณาเพิ่มแปลงปลูกก่อนเพิ่มพืชผล")

elif choice == "📡 ข้อมูลเซนเซอร์ (Sensor)":
    st.subheader("📡 รับค่าข้อมูลเซนเซอร์ (บันทึกข้อมูล)")
    plots_df = get_plots()
    
    if not plots_df.empty:
        with st.form("add_sensor"):
            plot_id = st.selectbox("เลือกแปลงปลูก", plots_df['id'].tolist(), format_func=lambda x: plots_df[plots_df['id']==x]['name'].values[0])
            s_type = st.selectbox("ประเภทเซนเซอร์", ["ความชื้นในดิน (%)", "อุณหภูมิอากาศ (°C)", "ความชื้นอากาศ (%)", "ความเข้มแสง (Lux)"])
            s_value = st.number_input("ค่าที่อ่านได้", value=0.0)
            
            if st.form_submit_button("บันทึกค่าเซนเซอร์"):
                conn.execute("INSERT INTO sensors (plot_id, type, value) VALUES (?, ?, ?)", (plot_id, s_type, s_value))
                conn.commit()
                st.success("บันทึกค่าเซนเซอร์สำเร็จ!")
                st.rerun()
                
        st.write("ประวัติข้อมูลเซนเซอร์:")
        st.dataframe(pd.read_sql("SELECT * FROM sensors ORDER BY timestamp DESC", conn), use_container_width=True)
    else:
        st.warning("กรุณาเพิ่มแปลงปลูกก่อนบันทึกค่าเซนเซอร์")

elif choice == "💦 ระบบรดน้ำ (Irrigation)":
    st.subheader("💦 ควบคุมการเปิด-ปิด ระบบรดน้ำ")
    plots_df = get_plots()
    
    if not plots_df.empty:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            with st.form("irrigation_control"):
                plot_id = st.selectbox("เลือกแปลงปลูก", plots_df['id'].tolist(), format_func=lambda x: plots_df[plots_df['id']==x]['name'].values[0])
                mode = st.radio("โหมดการทำงาน", ["กำหนดเอง (Manual)", "อัตโนมัติ (Auto)"])
                status = st.selectbox("สถานะวาล์วน้ำ", ["🔴 ปิด (OFF)", "🟢 เปิด (ON)"])
                
                if st.form_submit_button("อัปเดตระบบรดน้ำ"):
                    conn.execute("INSERT INTO irrigation (plot_id, mode, status) VALUES (?, ?, ?)", (plot_id, mode, status))
                    conn.commit()
                    st.success("อัปเดตสถานะการรดน้ำเรียบร้อย!")
                    st.rerun()
        
        with col2:
            st.write("ประวัติการทำงานของระบบรดน้ำ:")
            irr_df = pd.read_sql("SELECT irrigation.update_time, plots.name as plot_name, irrigation.mode, irrigation.status FROM irrigation JOIN plots ON irrigation.plot_id = plots.id ORDER BY irrigation.update_time DESC LIMIT 10", conn)
            st.dataframe(irr_df, use_container_width=True)
    else:
        st.warning("กรุณาเพิ่มแปลงปลูกก่อนใช้งานระบบรดน้ำ")

elif choice == "🛒 การเก็บเกี่ยว (Harvest)":
    st.subheader("🛒 บันทึกผลผลิตและการเก็บเกี่ยว")
    crops_df = get_crops()
    
    if not crops_df.empty:
        active_crops = crops_df[crops_df['status'] != 'ยกเลิก/เสียหาย']
        
        if not active_crops.empty:
            with st.form("add_harvest"):
                crop_id = st.selectbox("เลือกพืชผลที่เก็บเกี่ยว", active_crops['id'].tolist(), format_func=lambda x: active_crops[active_crops['id']==x]['name'].values[0])
                h_date = st.date_input("วันที่เก็บเกี่ยว")
                yield_kg = st.number_input("ปริมาณผลผลิตที่ได้ (กิโลกรัม)", min_value=0.0, step=0.1)
                revenue = st.number_input("รายได้จากการขาย (บาท)", min_value=0.0, step=10.0)
                
                if st.form_submit_button("บันทึกการเก็บเกี่ยว"):
                    conn.execute("INSERT INTO harvest (crop_id, harvest_date, yield_kg, revenue) VALUES (?, ?, ?, ?)", (crop_id, str(h_date), yield_kg, revenue))
                    conn.execute("UPDATE crops SET status='เก็บเกี่ยวแล้ว' WHERE id=?", (crop_id,))
                    conn.commit()
                    st.success("บันทึกข้อมูลการเก็บเกี่ยวเรียบร้อยแล้ว!")
                    st.rerun()
            
            st.write("ประวัติการเก็บเกี่ยวและรายได้:")
            harvest_display = pd.read_sql("SELECT harvest.harvest_date, crops.name as crop_name, harvest.yield_kg, harvest.revenue FROM harvest JOIN crops ON harvest.crop_id = crops.id ORDER BY harvest.harvest_date DESC", conn)
            st.dataframe(harvest_display, use_container_width=True)
        else:
            st.info("ไม่มีพืชผลที่สามารถเก็บเกี่ยวได้ในขณะนี้")
    else:
        st.warning("กรุณาเพิ่มพืชผลก่อนบันทึกการเก็บเกี่ยว")

conn.close()
'''
with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_content)
print("✅ 3/4 สร้างไฟล์ app.py เรียบร้อย")

# 4. สร้างไฟล์ run.bat สำหรับดับเบิลคลิกเปิดในครั้งต่อไป
bat_content = """@echo off
cd /d "%~dp0"
call ".venv\Scripts\activate"
streamlit run app.py
pause
"""
with open("run.bat", "w", encoding="utf-8") as f:
    f.write(bat_content)
print("✅ 4/4 สร้างปุ่มดับเบิลคลิก run.bat เรียบร้อย")

# 5. ติดตั้ง Packages และรันระบบอัตโนมัติ
print("📦 กำลังติดตั้ง Dependencies (Streamlit, Pandas, Plotly)...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

print("\n🎉 สร้างทุกอย่างเสร็จสมบูรณ์! กำลังเปิดหน้าเว็บระบบ Smart Farm Management...")
subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
