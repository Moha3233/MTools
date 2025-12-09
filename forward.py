# forward_toolkit_app.py
import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import io
from datetime import datetime
from auth import init_user_db, add_user, validate_user

# Initialize DB (creates users.db in working dir)
init_user_db()

st.set_page_config(page_title="Forward Toolkit", layout="wide")

# ---- helpers ----
def save_df_to_excel(dfs: dict):
    """Return BytesIO of an in-memory Excel file with multiple sheets."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet, df in dfs.items():
            try:
                df.to_excel(writer, sheet_name=sheet[:31], index=False)
            except Exception:
                # fallback: convert to dataframe
                pd.DataFrame([str(df)]).to_excel(writer, sheet_name=sheet[:31], index=False)
        writer.save()
    output.seek(0)
    return output

def draw_issue_tree(issue_tree):
    G = nx.DiGraph()
    # Build edges
    for parent, children in issue_tree.items():
        if not children:
            G.add_node(parent)
        for c in children:
            G.add_edge(parent, c)
    pos = nx.spring_layout(G, seed=1)
    fig, ax = plt.subplots(figsize=(6,4))
    nx.draw(G, pos, with_labels=True, node_color="#a6cee3", node_size=1300, font_size=9, arrowsize=12, ax=ax)
    st.pyplot(fig)

# ---- AUTHENTICATION ----
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "username" not in st.session_state:
    st.session_state["username"] = None

def login_page():
    st.title("Login to Forward Toolkit")
    tab1, tab2 = st.tabs(["🔑 Login", "🆕 Create Account"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if validate_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        new_user = st.text_input("New Username", key="new_user")
        new_pass = st.text_input("New Password", type="password", key="new_pass")
        if st.button("Create Account"):
            ok = add_user(new_user, new_pass)
            if ok:
                st.success("Account created! You can now log in.")
            else:
                st.error("Username already exists or invalid input.")

if not st.session_state["logged_in"]:
    login_page()
    st.stop()

# ---- sidebar ----
st.sidebar.title("Forward Toolkit — Modules")
modules = {
    "Problem Solving": st.sidebar.checkbox("Problem Solving", True),
    "Work Plan": st.sidebar.checkbox("Work Plan", True),
    "Communicate": st.sidebar.checkbox("Communicate", True),
    "Adaptability": st.sidebar.checkbox("Adaptability", True),
    "Well-being": st.sidebar.checkbox("Well-being", True),
    "Digital Toolkit (Data)": st.sidebar.checkbox("Digital Toolkit (Data)", True),
}

st.sidebar.markdown("---")
st.sidebar.write(f"Logged in as: **{st.session_state['username']}**")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.experimental_rerun()

st.sidebar.markdown("---")
st.sidebar.write("Export / Save")
if st.sidebar.button("Export all as Excel"):
    sheets = {}
    for k,v in st.session_state.items():
        # export DataFrames
        if isinstance(v, pd.DataFrame):
            sheets[k] = v
    if sheets:
        bio = save_df_to_excel(sheets)
        st.sidebar.download_button("Download workbook.xlsx", bio, file_name="forward_toolkit_export.xlsx")
    else:
        st.sidebar.info("No table data found to export.")

# ---- main ----
st.title("Forward: Interactive Toolkit (workbook → webapp)")
st.caption("Prototype mapping workbook exercises into interactive tools. Use the left menu to enable modules.")

# ---------- PROBLEM SOLVING ----------
if modules["Problem Solving"]:
    st.header("Problem Solving")
    st.subheader("SMART Problem Statement")
    col1, col2 = st.columns(2)
    with col1:
        specific = st.text_area("Specific — What is the specific question?", key="ps_specific", height=80)
        measurable = st.text_input("Measurable — Metric to measure success", key="ps_measurable")
    with col2:
        actionable = st.text_input("Actionable — What action(s) does it point to?", key="ps_actionable")
        relevant = st.text_input("Relevant — Who cares / stakeholders?", key="ps_relevant")
        timebound = st.text_input("Time-bound — Deadline (YYYY-MM-DD)", key="ps_timebound")
    if st.button("Compose SMART statement"):
        stmt = f"How can we {specific.strip()} — Success metric: {measurable}. Actions: {actionable}. Stakeholders: {relevant}. Deadline: {timebound}"
        st.success("SMART statement composed:")
        st.write(stmt)
        st.session_state["SMART_statement"] = pd.DataFrame([{"SMART_statement":stmt, "created": datetime.now()}])

    st.markdown("---")
    st.subheader("Issue Tree (Level 0 → Level 2)")
    st.write("Enter parent (Level0), then Level1 items (comma separated), then Level2 as lists per Level1.")
    root = st.text_input("Level 0 (Key problem statement)", key="it_root", value=st.session_state.get("it_root",""))
    l1_raw = st.text_input("Level 1 items (comma-separated, e.g. A,B,C)", key="it_l1", value=st.session_state.get("it_l1",""))
    issue_tree = {}
    if root and l1_raw:
        l1s = [x.strip() for x in l1_raw.split(",") if x.strip()]
        for l1 in l1s:
            key = f"{l1}"
            default = st.session_state.get(f"it_{key}_l2","")
            l2 = st.text_input(f"Level 2 items for {l1} (comma-separated)", key=f"it_{key}_l2", value=default)
            children = [x.strip() for x in l2.split(",") if x.strip()]
            issue_tree[l1] = children
        if st.button("Render issue tree"):
            st.write("Level 0:", root)
            draw_issue_tree({root: l1s, **{l1: issue_tree[l1] for l1 in l1s}})

    st.markdown("---")
    st.subheader("Prioritization Matrix (Impact vs Feasibility)")
    st.write("Add items (issue) with estimated Impact (1-5) and Feasibility (1-5).")
    p_issue = st.text_input("Issue name", key="p_issue")
    p_imp = st.slider("Impact (1 low - 5 high)", 1,5,3, key="p_imp")
    p_feas = st.slider("Feasibility (1 low - 5 high)", 1,5,3, key="p_feas")
    if st.button("Add prioritization item"):
        df = st.session_state.get("prioritization_df", pd.DataFrame(columns=["issue","impact","feasibility"]))
        df = pd.concat([df, pd.DataFrame([{"issue":p_issue,"impact":p_imp,"feasibility":p_feas}])], ignore_index=True)
        st.session_state["prioritization_df"] = df
    if "prioritization_df" in st.session_state:
        st.table(st.session_state["prioritization_df"])

# ---------- WORK PLAN ----------
if modules["Work Plan"]:
    st.header("Work Plan / Milestones")
    st.write("Make a short workplan entry for an issue.")
    wp_issue = st.text_input("Issue", key="wp_issue")
    wp_hypothesis = st.text_input("Hypothesis / rationale", key="wp_hyp")
    wp_endprod = st.text_input("End product", key="wp_end")
    wp_analyses = st.text_input("Analyses needed", key="wp_analyses")
    wp_sources = st.text_input("Sources", key="wp_sources")
    wp_timing = st.text_input("Timing / Responsibility", key="wp_timing")
    if st.button("Add workplan row"):
        df = st.session_state.get("workplan_df", pd.DataFrame(columns=["issue","hypothesis","end_product","analyses","sources","timing"]))
        df = pd.concat([df, pd.DataFrame([{"issue":wp_issue,"hypothesis":wp_hypothesis,"end_product":wp_endprod,"analyses":wp_analyses,"sources":wp_sources,"timing":wp_timing}])], ignore_index=True)
        st.session_state["workplan_df"] = df
    if "workplan_df" in st.session_state:
        st.dataframe(st.session_state["workplan_df"])

# ---------- COMMUNICATE ----------
if modules["Communicate"]:
    st.header("Communicating for Impact")
    st.subheader("EPIC (Empathy / Purpose / Insight / Conversation)")
    emp = st.text_area("Empathy — what's the audience feeling / thinking?", key="epic_emp")
    purpose = st.text_area("Purpose — what we want them to do/feel?", key="epic_purpose")
    insight = st.text_area("Insight — the core message / evidence?", key="epic_insight")
    convo = st.text_area("Conversation — open/narrow/close plan", key="epic_convo")
    if st.button("Compose EPIC summary"):
        epic = f"EPIC Summary:\\nEmpathy: {emp}\\nPurpose: {purpose}\\nInsight: {insight}\\nConversation plan: {convo}"
        st.success("EPIC composed")
        st.write(epic)
        st.session_state["EPIC"] = pd.DataFrame([{"EPIC":epic, "created": datetime.now()}])

    st.markdown("---")
    st.subheader("Pyramid Principle builder")
    governing = st.text_input("Governing thought (1 line)", key="py_gov")
    k1 = st.text_area("Key line 1", key="py_k1")
    k2 = st.text_area("Key line 2 (optional)", key="py_k2")
    k3 = st.text_area("Key line 3 (optional)", key="py_k3")
    if st.button("Create Pyramid"):
        pyramid = {"governing": governing, "keylines": [k for k in (k1,k2,k3) if k.strip()]}
        st.write("Governing thought:", governing)
        st.write("Key lines:", pyramid["keylines"])
        st.session_state["pyramid"] = pd.DataFrame([{"governing":governing, "keylines":" | ".join(pyramid["keylines"]), "created":datetime.now()}])

# ---------- ADAPTABILITY ----------
if modules["Adaptability"]:
    st.header("Adaptability & Resilience")
    st.subheader("APR helper (Pause → Awareness → Reframe)")
    note = st.text_area("Describe a current challenging situation:", key="apr_note")
    if st.button("Get APR prompts"):
        st.write("**Pause**: take 2 deep breaths, step back for 2 minutes.")
        st.write("**Awareness**: What am I thinking/feeling? What assumptions am I making?")
        st.write("**Reframe**: What opportunity exists if I shift my mindset? (3 ideas):")
        st.write("- Idea 1: ...\\n- Idea 2: ...\\n- Idea 3: ...")
        st.session_state.setdefault("apr_history", []).append({"situation":note, "time":datetime.now().isoformat()})
    st.markdown("---")
    st.subheader("Habit loop (Cue → Routine → Reward)")
    cue = st.text_input("Cue (trigger)", key="hcue")
    routine = st.text_input("Routine (what you'll do)", key="hroutine")
    reward = st.text_input("Reward (what makes it stick)", key="hreward")
    if st.button("Add habit"):
        df = st.session_state.get("habits_df", pd.DataFrame(columns=["cue","routine","reward"]))
        df = pd.concat([df, pd.DataFrame([{"cue":cue,"routine":routine,"reward":reward}])], ignore_index=True)
        st.session_state["habits_df"] = df
    if "habits_df" in st.session_state:
        st.table(st.session_state["habits_df"])

# ---------- WELL-BEING ----------
if modules["Well-being"]:
    st.header("Relationships & Well-Being")
    battery = st.slider("Your battery level this week (0 empty → 10 full)", 0, 10, 6, key="battery")
    st.write("Battery level:", battery)
    recovery = st.text_area("Plan to recover (short list)", key="recovery_plan")
    if st.button("Save recovery plan"):
        st.session_state.setdefault("recovery_history", []).append({"battery":battery, "plan":recovery, "time":datetime.now().isoformat()})
        st.success("Saved")

# ---------- DIGITAL TOOLKIT (DATA) ----------
if modules["Digital Toolkit (Data)"]:
    st.header("My Digital Toolkit — Data")
    st.write("Upload a CSV to explore (cleaning / viz / plan).")
    uploaded = st.file_uploader("Upload CSV", type=["csv","xlsx"])
    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"Failed to read file: {e}")
            df = None
        if df is not None:
            st.session_state["last_uploaded_df"] = df
            st.subheader("Preview")
            st.dataframe(df.head())
            st.subheader("Quick chart (choose numeric column)")
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            col = st.selectbox("Numeric column", ["--select--"] + numeric_cols)
            if col != "--select--":
                st.line_chart(df[col])
            if st.button("Save dataset to workspace"):
                st.session_state.setdefault("saved_datasets", {})[uploaded.name] = df
                st.success("Saved dataset to workspace")

# ---- footer / help ----
st.markdown("---")
st.write("Prototype created from the Forward workbook. Use the Export button in the sidebar to gather tables into an Excel workbook.")
