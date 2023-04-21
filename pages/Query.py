import streamlit as st
import pandas as pd

st.set_page_config(page_title="欣美园区健康监测管理系统", page_icon="📝")
st.title("欣美园区健康监测管理系统")
st.header("单人查询")

if "single_auth" not in st.session_state:
    st.session_state["single_auth"] = False

if not st.session_state["single_auth"]:
    with st.form("登录"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        if st.form_submit_button("登录"):
            if (
                username in st.secrets["viewer"]
                and password == st.secrets["viewer"][username]
                or username in st.secrets["su"]
                and password == st.secrets["su"][username]
                or username in st.secrets["visitor"]
                and password == st.secrets["visitor"][username]
            ):
                st.session_state["single_auth"] = True
                st.experimental_rerun()
            else:
                st.error("用户名或密码错误")
    st.stop()


@st.cache
def load_summary():
    return pd.read_csv("./data/summary.csv")


def get_tracking():
    df = pd.read_csv("./data/tracking.csv")
    return df


summary_info = load_summary()
tracking = get_tracking()
idx = st.selectbox(
    "查询姓名 + 尾号",
    range(len(summary_info["姓名"])),
    index=0,
    help="选择待查询健康状态的人员姓名 + 手机尾号",
    key="index",
    format_func=lambda x: summary_info["姓名"][x]
    + " "
    + str(summary_info["联系电话"][x])[-4:],
)
st.metric("当前状态", value=summary_info.iloc[idx, -1])
st.subheader("填报记录")
st.dataframe(tracking[tracking["联系电话"] == summary_info["联系电话"][idx]])
