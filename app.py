import streamlit as st
import os
import dotenv

def select_employee():
    st.header("SELECT EMPLOYEE")

    st.subheader("1. Select education major", divider="gray")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        major_select_1 = st.selectbox('major-1',('every period time','every period time with accumulate data','sidelap','combine with external data'),key='major-1')
    with col2:
        major_select_2 = st.selectbox('major-2',('every period time','every period time with accumulate data','sidelap','combine with external data'),key='major-2')
    with col3:
        major_select_3 = st.selectbox('major-3',('every period time','every period time with accumulate data','sidelap','combine with external data'),key='major-3')


    st.subheader("2. Select GPA", divider="gray")
    col1, col2, col3 = st.columns(3)
    with col1:
        gpa = st.slider("Select GPA", 2.0, 4.0, (2.2, 3.5),key='gpa')
        # print(values)

    st.subheader("3. Select gender", divider="gray")
    gender_man = st.toggle("Man",key='gender_man')
    gender_lady = st.toggle("Lady",key='gender_lady')
    gender_both = st.toggle("Both",key='gender_both')

def database():
    st.header("DATABASE")
    st.write("database")

def schedule():
    st.header("SCHEDULE")
    st.write("schedule")

def admin():
    st.header("ADMIN")
    st.write("admin")

def main_layout():
    st.set_page_config(
        page_title="Recruitment System 1.0.0",
        page_icon="💻",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    st.markdown("""<h1 style='text-align: center;'>Recruitment System</h1>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    if not st.session_state.logged_in:
        with col2:
            user_name = st.text_input("Input username", type="default")
            password = st.text_input("Input password", type="password")

        if user_name == str(os.environ["USER_NAME"]) and password == str(os.environ["PASSWORD"]):
            st.session_state.logged_in = True
            st.rerun()
        elif user_name or password:
            st.toast('USER OR PASSWORD NOT CORRECT!', icon='❌')

    else:
        # เมื่อเข้าสู่ระบบแล้ว
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 SELECT EMPLOYEE", "📂 DATABASE", "🕞 SCHEDULE", "📝 ADMIN"])
        with tab1:
            select_employee() #major gpa gender
        with tab2:
            database() #apply_position,work_experience,title,name,lastname,education_on_level,univesity,major,gpa,tel_no,email,attach_file
        with tab3:
            schedule()
        with tab4:
            admin()



if __name__ == "__main__":
    dotenv_file = dotenv.find_dotenv()
    dotenv.load_dotenv(dotenv_file, override=True)
    main_layout()
