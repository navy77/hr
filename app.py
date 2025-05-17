import streamlit as st
import os
import dotenv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
import time

def connect_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate('./serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    return db

def get_data_firebase(collection):
    db = connect_firebase()
    docs = db.collection(collection).stream()
    data = [doc.to_dict() for doc in docs]
    df = pd.DataFrame(data)
    return df

def insert_data_firebase(collection,df,div):
    db = connect_firebase()
    for _, row in df.iterrows():
        data = row.to_dict()
        data["div"] = div
        data["created_at"] = firestore.SERVER_TIMESTAMP
        db.collection(collection).add(data)

def calculate_score(select_major_list,gpa_list,select_gender_list,weight_score,select_no):
    df_source_employee = get_data_firebase("source_employee")
    weight_score = [int(x) for x in weight_score.split(",")] # convert to list
    
    # clean select_major_list
    new_select_major_list = [0 if item == '-- Select education major --' else item for item in select_major_list]
    # calculate score
    df_source_employee['major_score'] = df_source_employee['major'].apply(lambda x: 1 if x in new_select_major_list else 0)
    df_source_employee['gpa_score'] = df_source_employee['gpa'].apply(lambda x: 1 if x >= gpa_list[0] and x <= gpa_list[1]  else  0)
    df_source_employee['gender_score'] = df_source_employee['title'].apply(lambda x: 1 if x in select_gender_list  else  0)

    df_source_employee['total_score'] = df_source_employee['major_score']*weight_score[0] + df_source_employee['gpa_score'] * weight_score[1] + df_source_employee['gender_score'] * weight_score[2]
    # sort by total_score gpa_score
    df_source_employee = df_source_employee.sort_values(by=['total_score','gpa_score'],ascending=[False,False])
    df_preview_employee = df_source_employee.head(select_no)
    df_preview_employee = df_preview_employee[['title','name','lastname','education_on_level','major','gpa','univesity','attach_file']]
    df_preview_employee['select']=False

    cols = ["select"] + [col for col in df_preview_employee.columns if col != "select"]
    df_preview_employee = df_preview_employee[cols]
    return df_preview_employee

def assign_queue(df):
    df = df.copy()
    div = st.session_state.div
    insert_data_firebase("queue_interview",df,div)
    
def select_employee():
    st.subheader("SEARCH EMPLOYEE")

    st.subheader("1. Select education major", divider="gray")
    df_source_employee = get_data_firebase("source_employee")
    # create major list

    major_list = ["-- Select education major --"] + df_source_employee['major'].tolist()

    col1, col2, col3 = st.columns(3)
    
    with col1:
        major_select_1 = st.selectbox('major-1',major_list,key='major-1',placeholder='-')
    with col2:
        major_select_2 = st.selectbox('major-2',major_list,key='major-2')
    with col3:
        major_select_3 = st.selectbox('major-3',major_list,key='major-3')

    st.subheader("2. Select GPA", divider="gray")
    col1, col2, col3 = st.columns(3)
    with col1:
        gpa_list = st.slider("Select GPA", 2.0, 4.0, (2.2, 3.5),key='gpa')

    st.subheader("3. Select gender", divider="gray")
    gender_man = st.toggle("Man",key='gender_man')
    gender_lady = st.toggle("Lady",key='gender_lady')
    gender_both = st.toggle("Both",key='gender_both')

    if gender_both==True:
        select_gender_list=['ms','mr']
    elif gender_man==True and gender_lady==False:
        select_gender_list=['mr']
    elif gender_man==False and gender_lady==True:
        select_gender_list=['ms']
    else:
        select_gender_list=['ms','mr']
    

    col1, col2, col3 = st.columns(3)
    with col2:
        search_button = st.button(" 🔍 SEARCH ",key='search_button',use_container_width=True)

    if "show_table" not in st.session_state:
        st.session_state.show_table = False

    if "df_preview_employee" not in st.session_state:
        st.session_state.df_preview_employee = None

    if search_button:
        st.session_state.show_table = True
        select_major_list = [major_select_1,major_select_2,major_select_3]

        st.session_state.df_preview_employee = calculate_score(select_major_list,gpa_list,select_gender_list,os.environ["WEIGHT_SCORE"],int(os.environ["PREVIEW_NO"]))

    if st.session_state.show_table and st.session_state.df_preview_employee is not None:
        st.write("You can select maximum 10 persons")
        df_preview_employee = st.data_editor(st.session_state.df_preview_employee, use_container_width=True, num_rows="fixed", key="editor",hide_index=True,
                                             column_config={
                                                "attach_file": st.column_config.LinkColumn(
                                                    label="Website",      
                                                    display_text=None 
                                                )
                                            })
        
        col1, col2, col3 = st.columns(3)
        with col2:
            submit_button = st.button(" ✅ SUBMIT ",key='submit_button',use_container_width=True)
            cancel_button = st.button(" ❌ CANCEL ",key='cancel_button',use_container_width=True)
            if submit_button:
                df_selected_employee = df_preview_employee[df_preview_employee["select"] == True].reset_index(drop=True)
                if len(df_selected_employee) <= int(os.environ["MAX_SELECT_NO"]):
                    # print(df_selected_employee)
                    assign_queue(df_selected_employee)
                    st.success('SUCCESS SELECTED', icon="✅")
                    if st.session_state.role == "user":
                        time.sleep(2)
                        st.session_state.logged_in = False
                        st.session_state.div = None
                        st.session_state.df_preview_employee =False
                        st.session_state.show_table = False
                        st.rerun()
                else:
                    st.error('SELECTED OVER LIMIT', icon="❌")
                    time.sleep(2)
                    st.rerun()
            if cancel_button:
                st.error('NOT SELECT EMPLOYEE', icon="❌")
                if st.session_state.role == "user":
                    time.sleep(2)
                    st.session_state.logged_in = False
                    st.session_state.div = None
                    st.session_state.df_preview_employee =False
                    st.session_state.show_table = False
                    st.rerun()

def database():
    st.subheader("DATABASE")
    st.write("database")

def schedule():
    st.subheader("SCHEDULE")
    df_queue_interview = get_data_firebase("queue_interview")
    df =df_queue_interview.copy()

    df = df[['div','title','name','lastname','education_on_level','major','gpa','univesity','attach_file','created_at']]
    sorted
    st.data_editor(df, use_container_width=True, num_rows="fixed",hide_index=True,column_config={
                                                "attach_file": st.column_config.LinkColumn(
                                                    label="Website",      
                                                    display_text=None 
                                                )
                                            })

def admin():
    st.subheader("ADMIN")
    
def check_password(password):
    df_div = get_data_firebase("div_user")
    df_div['div_pass'] = df_div['div_name']+df_div['password']

    result_check = df_div[df_div["div_pass"] == password]
    if len(result_check) > 0 :
        return True
    else:
        return False

def main_layout():
    st.set_page_config(
        page_title="Recruitment System 1.0.0",
        page_icon="💻",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "div" not in st.session_state:
        st.session_state.div = None

    if "role" not in st.session_state:
        st.session_state.role = None

    st.markdown("""<h1 style='text-align: center;'>Recruitment System</h1>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    if not st.session_state.logged_in:
        with col2:
            div_input = st.text_input("Input division", type="default")
            password = st.text_input("Input password", type="password")
            signin_button = st.button("SIGN IN ",key='signin_button',use_container_width=True)

            if signin_button:
                div_password = div_input+password
                result_login = check_password(div_password)
                
                if result_login == True:
                    st.session_state.logged_in = True
                    st.session_state.div = div_input
                    st.session_state.role = "user"
                    st.rerun()
                elif div_input  == str(os.environ["DIV"]) and password == str(os.environ["PASSWORD"]):
                    st.session_state.logged_in = True
                    st.session_state.div = div_input
                    st.session_state.role = "admin"
                    st.rerun()
                else:st.toast('DIV OR PASSWORD INCORRECT!', icon='❌')

    else:
        if st.session_state.role == "admin":
            tab1, tab2, tab3, tab4 = st.tabs(["🔍 SEARCH EMPLOYEE", "📂 DATABASE", "🕞 SCHEDULE", "📝 ADMIN"])
            with tab1:
                select_employee() #major gpa gender
            with tab2:
                database() #apply_position,work_experience,title,name,lastname,education_on_level,univesity,major,gpa,tel_no,email,attach_file
            with tab3:
                schedule()
            with tab4:
                admin()
        elif st.session_state.role == "user":
            tab1 = st.tabs(["🔍 SEARCH EMPLOYEE"])[0]
            with tab1:
                select_employee() #major gpa gender

if __name__ == "__main__":
    dotenv_file = dotenv.find_dotenv()
    dotenv.load_dotenv(dotenv_file, override=True)
    main_layout()

