import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from plotly import graph_objects as go

st.set_page_config(page_title="欣美园区健康监测管理系统", page_icon="📝")
st.title("欣美园区健康监测管理系统")
st.header("后台管理")

if "auth" not in st.session_state:
    st.session_state["auth"] = False
if "edit" not in st.session_state:
    st.session_state["edit"] = False

if not st.session_state["auth"]:
    with st.form("登录"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        if st.form_submit_button("登录"):
            if username in st.secrets["su"] and password == st.secrets["su"][username]:
                st.session_state["auth"] = True
                st.session_state["edit"] = True
                st.experimental_rerun()
            elif (
                username in st.secrets["visitor"]
                and password == st.secrets["visitor"][username]
            ):
                st.session_state["auth"] = True
                st.session_state["edit"] = False
                st.experimental_rerun()
            else:
                st.error("用户名或密码错误")
    st.stop()


def update_people(name: str, depart: str, tel: int, employ: str):
    if not name:
        return
    old_df = get_people()
    new_elem = pd.DataFrame(
        {"姓名": [name], "部门": [depart], "联系电话": [tel], "用工形式": [employ], "备注": [""]}
    )
    new_df = old_df.append(new_elem, ignore_index=True)

    # drop dup base on tel
    new_df.drop_duplicates(subset="联系电话", keep="last", inplace=True)
    new_df.to_csv("./data/people.csv", index=False)


def get_people():
    df = pd.read_csv("./data/people.csv").fillna("")
    return df


@st.cache
def get_depart():
    df = get_people()
    return sorted(list(df["部门"].unique()))


def get_tracking():
    df = pd.read_csv("./data/tracking.csv")
    return df


def update_stat(date: str, name: str, depart: str, tel: int):
    stat = st.session_state[f"{date}-{depart}-{name}-{tel}"]
    df = get_tracking()
    df.loc[(df["日期"] == date) & (df["姓名"] == name) & (df["联系电话"] == tel), "目前状态"] = stat
    df.to_csv("./data/tracking.csv", index=False)


def update_comment(name: str, depart: str, tel: int):
    comment = st.session_state[f"{depart}-{name}-{tel}-comment"]
    df = get_people().copy()
    df.loc[(df["姓名"] == name) & (df["联系电话"] == tel), "备注"] = comment
    df.to_csv("./data/people.csv", index=False)


@st.cache(ttl=600)
def get_summary():
    people_info = get_people().copy()
    people_info.sort_values(by=["部门", "姓名", "联系电话"], inplace=True)
    submission = people_info.copy()
    tracking_info = get_tracking()
    days = tracking_info["日期"].unique()
    days.sort()
    for idx, day in enumerate(days):
        today = tracking_info[tracking_info["日期"] == day]
        submission[day] = "未提交"
        submission.loc[submission["联系电话"].isin(today["联系电话"]), day] = "已提交"
        if idx == 0:
            people_info[day] = "未知"
        else:
            people_info[day] = people_info[days[idx - 1]]
        for i in range(len(today)):
            name = today.iloc[i]["姓名"]
            tel = today.iloc[i]["联系电话"]
            stat = today.iloc[i]["健康状态"]
            if stat == "健康" and (
                "确诊"
                in people_info.loc[
                    (people_info["姓名"] == name) & (people_info["联系电话"] == tel)
                ].values
            ):
                people_info.loc[
                    (people_info["姓名"] == name) & (people_info["联系电话"] == tel), day
                ] = "康复"
            else:
                people_info.loc[
                    (people_info["姓名"] == name) & (people_info["联系电话"] == tel), day
                ] = stat
    people_info.to_csv("./data/summary.csv", index=False)
    return (
        pd.read_csv("./data/summary.csv"),
        submission,
        days,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


add_people, query_record, assign_stat, summary = st.tabs(
    ["新增人员", "查询记录", "指派状态", "一览表"]
)


with add_people:
    if st.session_state["edit"]:
        with st.form("新增人员"):
            name: str = st.text_input("姓名", help="待新增人员姓名")
            depart: str = st.selectbox(
                "部门",
                get_depart(),
            )
            employ: str = st.selectbox(
                "用工形式",
                get_people()["用工形式"].unique(),
            )
            tel: int = st.number_input(
                "联系电话", 10000000000, 19999999999, help="待新增人员联系电话，将作为登录账号"
            )
            if st.form_submit_button("确认信息无误，提交"):
                update_people(name, depart, tel, employ)
    else:
        st.info("请使用具有编辑权限的管理员账号登录，以使用此功能")

with query_record:
    df = get_tracking()
    st.subheader("筛选条件")
    start, end = st.slider(
        "日期",
        min_value=date(*tuple(map(int, df["日期"].min().split("-")))) - timedelta(days=1),
        max_value=date(*tuple(map(int, df["日期"].max().split("-")))),
        value=(
            date(*tuple(map(int, df["日期"].max().split("-")))),
            date(*tuple(map(int, df["日期"].max().split("-")))),
        ),
        # format="YYYY-MM-DD",
    )
    depart = st.multiselect(
        "部门",
        df["部门"].unique(),
        default=df["部门"].unique(),
    )
    employ = st.multiselect(
        "用工形式",
        df["用工形式"].unique(),
        default=df["用工形式"].unique(),
    )
    acid = st.multiselect(
        "核酸状态",
        df["核酸"].unique(),
        default=df["核酸"].unique(),
    )
    anti = st.multiselect(
        "抗原状态",
        df["抗原"].unique(),
        default=df["抗原"].unique(),
    )
    qrcd = st.multiselect(
        "健康码状态",
        df["健康码"].unique(),
        default=df["健康码"].unique(),
    )
    vacc = st.multiselect(
        "疫苗状态",
        df["疫苗"].unique(),
        default=df["疫苗"].unique(),
    )
    temp = st.multiselect(
        "体温异常",
        df["体温异常"].unique(),
        default=df["体温异常"].unique(),
    )
    health = st.multiselect(
        "健康状态",
        df["健康状态"].unique(),
        default=df["健康状态"].unique(),
    )
    filtered = df[
        (df["部门"].isin(depart))
        & (df["日期"] >= start.strftime("%Y-%m-%d"))
        & (df["日期"] <= end.strftime("%Y-%m-%d"))
        & (df["用工形式"].isin(employ))
        & (df["核酸"].isin(acid))
        & (df["抗原"].isin(anti))
        & (df["健康码"].isin(qrcd))
        & (df["疫苗"].isin(vacc))
        & (df["体温异常"].isin(temp))
        & (df["健康状态"].isin(health))
    ]
    st.dataframe(filtered)
    st.download_button(
        "下载表格",
        filtered.to_csv(index=False, encoding="utf_8_sig"),
        file_name=f"查询记录_{datetime.now().strftime('%Y-%M-%D_%H-%M-%S')}.csv",
    )

with assign_stat:
    if st.session_state["edit"]:
        depart = st.selectbox("部门", get_depart())
        people_info = get_people()
        depart_people = people_info[people_info["部门"] == depart]
        total_record = get_tracking()
        today_date = date.today().strftime("%Y-%m-%d")
        today_record = total_record[total_record["日期"] == today_date]
        st.download_button(
            "下载该部门当日未提交名单",
            depart_people[~depart_people["联系电话"].isin(today_record["联系电话"])].to_csv(
                index=False, encoding="utf_8_sig"
            ),
            file_name=f"{depart}未提交名单_{datetime.now().strftime('%Y-%M-%D_%H-%M-%S')}.csv",
            help="下载单个部门人员中当日未提交名单，如需下载多个部门，请至“一览表”功能中下载",
        )
        for name, tel in zip(depart_people["姓名"], depart_people["联系电话"]):
            with st.expander(
                name + " " + str(tel), expanded=name in today_record["姓名"].values
            ):
                if name in today_record["姓名"].values:
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric(
                            "核酸",
                            today_record[today_record["姓名"] == name]["核酸"].values[0],
                        )
                    with cols[1]:
                        st.metric(
                            "抗原",
                            today_record[today_record["姓名"] == name]["抗原"].values[0],
                        )
                    with cols[2]:
                        st.metric(
                            "体温",
                            today_record[today_record["姓名"] == name]["体温"].values[0],
                            delta="+ 异常"
                            if today_record[today_record["姓名"] == name]["体温异常"].values[
                                0
                            ]
                            == "是"
                            else "- 正常",
                            delta_color="inverse",
                        )
                    st.selectbox(
                        "指派状态",
                        options=["工作状态", "居家", "集中隔离"],
                        index=(["工作状态", "居家", "集中隔离"]).index(
                            today_record[today_record["姓名"] == name]["目前状态"].values[0]
                        ),
                        key=f"{today_date}-{depart}-{name}-{tel}",
                        on_change=update_stat,
                        args=(today_date, name, depart, tel),
                    )
                else:
                    last_record = total_record[
                        (total_record["姓名"] == name) & (total_record["联系电话"] == tel)
                    ]
                    if len(last_record) > 0:
                        st.warning(
                            f"今日未完成，以下为 {last_record.iloc[-1, :]['日期']} 记录，联系电话: {tel}"
                        )
                        cols = st.columns(3)
                        with cols[0]:
                            st.metric(
                                "核酸",
                                last_record.iloc[-1, :]["核酸"],
                            )
                        with cols[1]:
                            st.metric(
                                "抗原",
                                last_record.iloc[-1, :]["抗原"],
                            )
                        with cols[2]:
                            st.metric(
                                "体温",
                                last_record.iloc[-1, :]["体温"],
                                delta="+ 异常"
                                if last_record.iloc[-1, :]["体温异常"] == "是"
                                else "- 正常",
                                delta_color="inverse",
                            )
                    else:
                        st.error(f"今日未完成，未找到历史记录，联系电话: {tel}")
                st.text_area(
                    "备注信息",
                    value=people_info[
                        (people_info["姓名"] == name) & (people_info["联系电话"] == tel)
                    ]["备注"].values[0],
                    max_chars=200,
                    key=f"{depart}-{name}-{tel}-comment",
                    on_change=update_comment,
                    args=(name, depart, tel),
                    help="所有备注信息将会与对应人员相关联，如需删除请清空备注信息",
                )
    else:
        st.info("请使用具有编辑权限的管理员账号登录，以使用此功能")

with summary:
    summary, submission, days, update_time = get_summary()
    st.info(f"数据更新时间: {update_time}")
    depart = st.multiselect(
        "筛选部门",
        df["部门"].unique(),
        default=df["部门"].unique(),
    )
    st.download_button(
        "下载提交情况汇总表",
        submission[submission["部门"].isin(depart)].to_csv(
            index=False, encoding="utf_8_sig"
        ),
        file_name=f'提交情况汇总表_{datetime.now().strftime("%Y-%M-%D_%H-%M-%S")}.csv',
        help="此表仅包含人员基本信息与每日提交情况",
    )
    filtered = summary[summary["部门"].isin(depart)]
    st.dataframe(filtered, use_container_width=True)
    st.download_button(
        "下载健康状况汇总表",
        filtered.to_csv(index=False, encoding="utf_8_sig"),
        file_name=f"汇总_{update_time.replace(':', '-').replace(' ', '_')}.csv",
        help="此表包含人员基本信息、每日健康状况。健康状况根据每日提交情况以自动更新。",
    )

    days_summarys = {day: filtered[day].value_counts().to_dict() for day in days}
    day_start, day_end = st.slider(
        "选择日期范围",
        min_value=datetime.strptime(days[0], "%Y-%m-%d"),
        max_value=datetime.strptime(days[-1], "%Y-%m-%d"),
        value=(
            datetime.strptime(days[0], "%Y-%m-%d"),
            datetime.strptime(days[-1], "%Y-%m-%d"),
        ),
        format="YYYY-MM-DD",
    )
    day_start = day_start.strftime("%Y-%m-%d")
    day_end = day_end.strftime("%Y-%m-%d")
    plot_days = [day for day in days if day >= day_start and day <= day_end]

    plot = go.Figure(
        data=[
            go.Bar(
                name="异常",
                x=plot_days,
                y=[days_summarys[day].get("异常", 0) for day in plot_days],
            ),
            go.Bar(
                name="确诊",
                x=plot_days,
                y=[days_summarys[day].get("确诊", 0) for day in plot_days],
            ),
            go.Bar(
                name="健康",
                x=plot_days,
                y=[days_summarys[day].get("健康", 0) for day in plot_days],
            ),
            go.Bar(
                name="康复",
                x=plot_days,
                y=[days_summarys[day].get("康复", 0) for day in plot_days],
            ),
            go.Bar(
                name="未知",
                x=plot_days,
                y=[days_summarys[day].get("未知", 0) for day in plot_days],
            ),
        ]
    )
    hovertemp = "<b>日期: </b> %{x} <br>"
    hovertemp += "<b>人数: </b> %{y}"
    plot.update_traces(hovertemplate=hovertemp)
    plot.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=plot_days,
            ticktext=plot_days,
        )
    )
    # plot.update_layout(barmode="stack")
    st.plotly_chart(plot)
