import streamlit as st
import os
import dotenv
from pymongo import MongoClient
import pandas as pd
import time
from datetime import datetime

def connect_db(user,password,host):
    client = MongoClient(f"mongodb://{user}:{password}@{host}:27017/")
    return client

def get_data_db(database,collection):
    client = connect_db(os.environ["MG_USERNAME"],os.environ["MG_PASSWORD"],os.environ["MG_HOST"])
    db = client[database]
    collection = db[collection]
    data = list(collection.find())
    df = pd.DataFrame(data)
    return df

def insert_data_queue(database,collection,df,div):
    client = connect_db(os.environ["MG_USERNAME"],os.environ["MG_PASSWORD"],os.environ["MG_HOST"])
    db = client[database]
    collection = db[collection]
    df['div'] = div
    df['created_at'] = datetime.now()
    data = df.to_dict(orient='records')
    collection.insert_many(data)

def insert_data_employee(database,collection,df):
    client = connect_db(os.environ["MG_USERNAME"],os.environ["MG_PASSWORD"],os.environ["MG_HOST"])
    db = client[database]
    collection = db[collection]
    df['created_at'] = datetime.now()
    data = df.to_dict(orient='records')
    collection.insert_many(data)
        
def calculate_score(select_major_list,gpa_list,select_gender_list,weight_score,select_no):
    df_source_employee = get_data_db(os.environ["MG_DATABASE"],"source_employee")
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

    df_source_employee = df_source_employee[df_source_employee['total_score']>0]

    df_preview_employee = df_source_employee.head(select_no)
    df_preview_employee = df_preview_employee[['title','name','lastname','education_on_level','major','gpa','university','attach_file']]
    
    df_preview_employee['select']=False

    cols = ["select"] + [col for col in df_preview_employee.columns if col != "select"]
    df_preview_employee = df_preview_employee[cols]
    return df_preview_employee

def assign_queue(df):
    df = df.copy()
    div = st.session_state.div
    insert_data_queue(os.environ["MG_DATABASE"],"queue_interview",df,div)
    
def select_employee():
    st.subheader("SEARCH EMPLOYEE")

    
    df_source_employee = get_data_db(os.environ["MG_DATABASE"],"source_employee")
    if not df_source_employee.empty:
        st.subheader("1. Select education major", divider="gray")
        df_major = df_source_employee.drop_duplicates(subset=['major'])

        # create major list

        major_list = ["-- Select education major --"] + df_major['major'].tolist()

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
            select_gender_list=[]
        

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
    # show table   
    df_source_employee = get_data_db(os.environ["MG_DATABASE"],"source_employee")
    df =df_source_employee.copy()
    if not df.empty:
        df = df[['apply_position','title','name','lastname','work_experience','education_on_level','major','gpa','university','tel_no','email','attach_file','created_at']]
        df = df.sort_values(by=['created_at'],ascending=[True])
        st.data_editor(df, use_container_width=True, num_rows="fixed",hide_index=True,column_config={
                                                    "attach_file": st.column_config.LinkColumn(
                                                        label="Website",      
                                                        display_text=None 
                                                    )
                                                })
    else:
        st.write("no employee data")

def schedule():
    st.subheader("SCHEDULE")
    df_queue_interview = get_data_db(os.environ["MG_DATABASE"],"queue_interview")
    df =df_queue_interview.copy()
    if not df.empty:
        df = df[['div','title','name','lastname','education_on_level','major','gpa','university','attach_file','created_at']]
        df = df.sort_values(by=['created_at','div'],ascending=[True,False])
        st.data_editor(df, use_container_width=True, num_rows="fixed",hide_index=True,column_config={
                                                    "attach_file": st.column_config.LinkColumn(
                                                        label="Website",      
                                                        display_text=None 
                                                    )
                                                })
    else:st.write("no employee data")

def admin():
    st.subheader("ADMIN")
    # upload file
    st.subheader("Upload source employee by CSV", divider="gray")
    col1, col2, col3 = st.columns(3)
    with col1:
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        upload_button = st.button("UPLOAD TO DATABASE",key='upload_button',use_container_width=False)

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Preview of CSV:")
        st.dataframe(df)

    if upload_button:
        insert_data_employee(os.environ["MG_DATABASE"],"source_employee",df)
        st.success('SUCCESS UPLOADED', icon="✅")
        time.sleep(1)
        st.rerun()

    # config weight score
    st.subheader("CONFIG WEIGHT SCORE", divider="gray")
    col1, col2, col3 = st.columns(3)
    with col1:
        major_weight = st.slider("Major weight score", 0, 100, 50)
        gpa_weight = st.slider("Major weight score", 0, 100, 40)
        gender_weight = st.slider("Major weight score", 0, 100, 10)
        total_weight  = major_weight+gpa_weight+gender_weight

        weight_button = st.button("UPDATE WEIGHT SCORE",key='weight_button',use_container_width=False)
        if weight_button:
            if total_weight==100:
                total_weight_env = f"{major_weight},{gpa_weight},{gender_weight}"
                os.environ["WEIGHT_SCORE"] = str(total_weight_env)
                dotenv.set_key(dotenv_file,"WEIGHT_SCORE",os.environ["WEIGHT_SCORE"])
                st.success('SUCCESS UPDATED', icon="✅")
                time.sleep(1)
                st.rerun()
            else:
                st.error('TOTAL WEIGHT SCORE NOT EQUAL 100%', icon="❌")
                time.sleep(1)

    # config max select employee
    st.subheader("CONFIG MAX SELECT EMPLOYEE", divider="gray")
    col1, col2, col3 = st.columns(3)
    with col1:
        max_select_employee = st.slider("Maximum employee can select ", 1, 20, 10)
        max_select_employee_button = st.button("UPDATE MAX SELECT EMPLOYEE",key='max_select_employee_button',use_container_width=False)
        if max_select_employee_button:
            os.environ["MAX_SELECT_NO"] = str(max_select_employee)
            dotenv.set_key(dotenv_file,"MAX_SELECT_NO",os.environ["MAX_SELECT_NO"])
            st.success('SUCCESS UPDATED', icon="✅")
            time.sleep(1)
            st.rerun()

    # config max preview employee
    st.subheader("CONFIG MAX PREVIEW EMPLOYEE", divider="gray")
    col1, col2, col3 = st.columns(3)
    with col1:
        max_preview_employee = st.slider("Maximum employee can preview ", 1, 30, 10)
        max_preview_employee_button = st.button("UPDATE MAX PREVIEW EMPLOYEE",key='max_preview_employee_button',use_container_width=False)
        if max_preview_employee_button:
            os.environ["PREVIEW_NO"] = str(max_preview_employee)
            dotenv.set_key(dotenv_file,"PREVIEW_NO",os.environ["PREVIEW_NO"])
            st.success('SUCCESS UPDATED', icon="✅")
            time.sleep(1)
            st.rerun()

def check_password(password):
    df_div = get_data_db(os.environ["MG_DATABASE"],"div_user")
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
                database() 
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

