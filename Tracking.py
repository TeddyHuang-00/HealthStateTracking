import streamlit as st
from datetime import datetime
import pandas as pd
from hashlib import sha256

st.set_page_config(page_title="欣美园区健康监测管理系统", page_icon="📝")
st.title("欣美园区健康监测管理系统")
st.header("健康状态跟踪")


FEVER_THRESH = 37.5
DEFAULT_PASSWD = "123456"


@st.cache(ttl=60)
def get_people():
    df = pd.read_csv("./data/people.csv").fillna("")
    return df


def update_data(
    name: str,
    depart: str,
    employ: str,
    tel: int,
    acid: str,
    temp: float,
    anti: str,
    qrcd: str,
    vacc: int,
    stat: str,
):
    # Write to data files
    update_time = datetime.now()
    date = update_time.strftime("%Y-%m-%d")
    time = update_time.strftime("%H:%M:%S")
    fever = temp >= FEVER_THRESH
    old_df: pd.DataFrame = pd.read_csv("./data/tracking.csv")
    new_rec = pd.DataFrame(
        {
            "日期": [date],
            "填报时间": [time],
            "部门": [depart],
            "姓名": [name],
            "用工形式": [employ],
            "联系电话": [tel],
            "核酸": [acid],
            "抗原": [anti],
            "健康码": [qrcd],
            "疫苗": [str(vacc)],
            "体温": [f"{temp:.1f}"],
            "体温异常": ["是" if fever else "否"],
            "目前状态": [stat],
            "健康状态": [
                "确诊"
                if acid == "阳性" or anti == "阳性" or qrcd == "红码"
                else "异常"
                if temp >= FEVER_THRESH or qrcd == "黄码"
                else "健康"
            ],
        }
    )
    new_df = old_df.append(new_rec, ignore_index=True)
    new_df.drop_duplicates(subset=["日期", "姓名", "联系电话"], keep="last", inplace=True)
    new_df.to_csv("./data/tracking.csv", index=False)


def get_user():
    return pd.read_csv("./data/users.csv")


def salt(passwd: str):
    for salt in st.secrets["salt"].values():
        passwd = sha256((passwd + salt).encode()).hexdigest()
    return passwd


people_info = get_people().copy()
users = get_user()

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    with st.form("登录"):
        username = st.number_input(
            "手机号",
            10000000000,
            19999999999,
            help="请输入您的手机号，如果您不在本系统中，请联系管理员添加",
        )
        password = st.text_input(
            "密码", type="password", help=f"初次登陆密码为 {DEFAULT_PASSWD}"
        )
        if st.form_submit_button("登录"):
            if (
                username in users["name"].values
                and salt(password) in users["pass"].values
                or username in people_info["联系电话"].values
                and salt(password) == salt(DEFAULT_PASSWD)
            ):
                st.session_state["login"] = True
                st.session_state["tel"] = username
                st.experimental_rerun()
            else:
                st.error("用户名或密码错误")
    st.stop()

if st.session_state["tel"] not in users["name"].values:
    st.warning("初次登陆，请修改密码")
    with st.form("修改密码"):
        new_password = st.text_input("新密码", type="password")
        new_password_confirm = st.text_input("确认新密码", type="password")
        if st.form_submit_button("修改密码"):
            if not new_password:
                st.error("密码不能为空")
            elif new_password != new_password_confirm:
                st.error("密码不一致")
            else:
                users = users.append(
                    pd.DataFrame(
                        {
                            "name": [st.session_state["tel"]],
                            "pass": [salt(new_password)],
                        }
                    )
                )
                users.to_csv("./data/users.csv", index=False)
                st.session_state["login"] = False
                st.experimental_rerun()
    st.stop()

idx = people_info["联系电话"].tolist().index(st.session_state["tel"])
depart, name, employ, tel, *_ = people_info.iloc[idx, :]

if not name:
    st.error("请先选择姓名后继续")

st.subheader("基本信息")
L, R = st.columns(2)
with L:
    st.metric("姓名", name)
with R:
    st.metric("部门", depart)

st.subheader("今日填报")
with st.form(name):
    acid: str = st.radio(
        "**核酸状态**", ["阳性", "阴性", "未出"], horizontal=True, help="如您当日未检测，请填报上次检测结果"
    )
    anti: str = st.radio(
        "**抗原状态**", ["阳性", "阴性"], horizontal=True, help="如您当日未检测，请填报上次检测结果"
    )
    qrcd: str = st.radio("**健康码状态**", ["绿码", "黄码", "红码"], horizontal=True)
    vacc: int = st.slider("**疫苗接种情况**", min_value=0, max_value=4, format="%d针", value=0)
    stat: str = st.radio("**目前状态**", ["工作状态", "居家", "集中隔离"], horizontal=True)
    temp: float = st.number_input("**今日体温**", 35.0, 45.0, 37.0, step=0.1)
    if st.form_submit_button("提交"):
        update_data(name, depart, employ, tel, acid, temp, anti, qrcd, vacc, stat)
        if acid == "阳性" or anti == "阳性":
            st.error("您的新冠检测结果为阳性，建议您居家，保重健康")
        elif qrcd == "红码":
            st.error("您的健康码为红码，建议您居家，保重健康")
        elif temp >= FEVER_THRESH:
            st.warning("您的体温偏高，请注意休息，及时上报发烧等症状")
        else:
            st.success("您的健康状况良好，请注意近期身体健康")
