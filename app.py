import streamlit as st
import pandas as pd
import random

st.title("シフト自動作成アプリ（完成版・安定）")

# ---------------------------
# スタッフ人数
# ---------------------------
num_staff = st.number_input("スタッフ人数", 1, 10, 6)
staff_names = [f"スタッフ{i+1}" for i in range(num_staff)]
hours = list(range(24))

# ---------------------------
# 勤務時間上限
# ---------------------------
max_hours = st.number_input("1人あたりの最大勤務時間", 1, 24, 8)

# ---------------------------
# 必要人数
# ---------------------------
st.subheader("必要人数")
required = {}
for h in hours:
    required[h] = st.number_input(f"{h}時", 0, num_staff, 3, key=f"req_{h}")

# ---------------------------
# 勤務希望・休憩希望
# ---------------------------
work_df = pd.DataFrame(0, index=staff_names, columns=hours)
break_df = pd.DataFrame(0, index=staff_names, columns=hours)

st.subheader("勤務希望／休憩希望")

for staff in staff_names:
    st.write(f"--- {staff} ---")

    st.write("勤務希望")
    for h in hours:
        work_df.loc[staff, h] = 1 if st.checkbox(f"{h}時", key=f"w_{staff}_{h}") else 0

    st.write("休憩希望")
    for h in hours:
        break_df.loc[staff, h] = 1 if st.checkbox(f"{h}時", key=f"b_{staff}_{h}") else 0

# ---------------------------
# 実行
# ---------------------------
if st.button("実行"):

    schedule = work_df.copy()

    # ① 休憩反映
    for s in staff_names:
        for h in hours:
            if break_df.loc[s, h] == 1:
                schedule.loc[s, h] = 0

    # ② 初期人数合わせ
    for h in hours:
        while schedule[h].sum() < required[h]:
            candidates = [
                s for s in staff_names
                if schedule.loc[s, h] == 0
                and break_df.loc[s, h] == 0
                and schedule.loc[s].sum() < max_hours
            ]
            if not candidates:
                break
            s = random.choice(candidates)
            schedule.loc[s, h] = 1

    # ③ 単発削除（1回目）
    for s in staff_names:
        h = 0
        while h < 24:
            if schedule.loc[s, h] == 1:
                start = h
                while h < 24 and schedule.loc[s, h] == 1:
                    h += 1
                if h - start == 1:
                    schedule.loc[s, start] = 0
            else:
                h += 1

    # ④ 指定時間帯に休憩
    target_ranges = [[11,12,13],[17,18,19,20]]
    for s in staff_names:
        for tr in target_ranges:
            if all(schedule.loc[s, h] == 1 for h in tr):
                schedule.loc[s, random.choice(tr)] = 0

    # ⑤ 最終人数合わせ（連続優先版）
    for h in hours:
        while schedule[h].sum() < required[h]:

            candidates = sorted(
                staff_names,
                key=lambda s: schedule.loc[s].sum()
            )

            added = False

            for s in candidates:
                if (
                    schedule.loc[s, h] == 0
                    and break_df.loc[s, h] == 0
                    and schedule.loc[s].sum() < max_hours
                ):

                    # 前とつながる
                    if h > 0 and schedule.loc[s, h-1] == 1:
                        schedule.loc[s, h] = 1
                        added = True

                    # 後ろとつながる
                    elif h < 23 and schedule.loc[s, h+1] == 1:
                        schedule.loc[s, h] = 1
                        added = True

                    # 2時間セットで入れる
                    elif h < 23:
                        schedule.loc[s, h] = 1
                        schedule.loc[s, h+1] = 1
                        added = True

                    if added:
                        break

            if not added:
                break

    # ⑥ 単発削除（最終）
    for s in staff_names:
        h = 0
        while h < 24:
            if schedule.loc[s, h] == 1:
                start = h
                while h < 24 and schedule.loc[s, h] == 1:
                    h += 1
                if h - start == 1:
                    schedule.loc[s, start] = 0
            else:
                h += 1

    # ---------------------------
    # 表示
    # ---------------------------

    # 勤務時間
    st.subheader("勤務時間")
    st.dataframe(schedule.sum(axis=1).rename("勤務時間"))

    # チェック
    st.subheader("チェック結果")
    for h in hours:
        assigned = schedule[h].sum()
        need = required[h]

        if assigned < need:
            st.error(f"{h}時：人数不足（{assigned}/{need}）")
        elif assigned > need:
            st.warning(f"{h}時：人数超過（{assigned}/{need}）")

    # ---------------------------
    # ビジュアルシフト表
    # ---------------------------
    st.subheader("シフト表（ビジュアル）")

    display_df = schedule.copy()
    display_df.columns = [f"{h:02d}" for h in hours]

    def color_map(val):
        return "background-color: #F6A068" if val == 1 else "background-color: #FFEEDB"

    styled = display_df.style.map(color_map)
    styled = styled.format(lambda x: "")
    styled = styled.set_properties(**{
        "border": "2px solid #999",
        "text-align": "center"
    })

    st.dataframe(styled, use_container_width=True)
