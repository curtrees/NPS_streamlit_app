import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

logo_path = os.path.join(os.path.dirname(__file__), "logo.png")


# Show the logo image (supports PNG, JPG, etc.)
st.image(logo_path, width=200)
# ...existing code...

st.title("NPS Score Calculator")

uploaded_file = st.file_uploader("Upload a CSV file with 'month' and 'score' columns. Use 1 for January, 2 for February, etc.", type="csv")

def calculate_nps(scores):
    promoters = sum(1 for s in scores if s >= 9)
    passives = sum(1 for s in scores if 7 <= s <= 8)
    detractors = sum(1 for s in scores if s <= 6)
    total = len(scores)
    if total == 0:
        return 0, promoters, passives, detractors
    nps = ((promoters - detractors) / total) * 100
    return round(nps, 2), promoters, passives, detractors


if uploaded_file is not None:
    # Expecting columns: month, score
    df = pd.read_csv(uploaded_file, header=None, names=["month", "score"])
    df = df.dropna()
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df = df[df["score"].between(0, 10)]

    # Define the correct month order
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Convert 'month' column to categorical with the correct order
    df["month"] = pd.Categorical(df["month"], categories=month_order, ordered=True)
    df["month"] = df["month"].astype(str)  # Convert to string for display
    
    if not df.empty:
        # Calculate NPS per month
        nps_by_month = []
        for month, group in df.groupby("month", sort=False):  # sort=False keeps the categorical order
            if group.empty:
                continue
            scores = group["score"].tolist()
            nps, promoters, passives, detractors = calculate_nps(scores)
            nps_by_month.append({
                "Month": month,
                "NPS": nps,
                "Promoters": promoters,
                "Passives": passives,
                "Detractors": detractors
            })
        nps_df = pd.DataFrame(nps_by_month)
        nps_df["Month"] = pd.Categorical(nps_df["Month"], categories=month_order, ordered=True)
        nps_df = nps_df.sort_values("Month")

        st.subheader("NPS by Month")
        st.table(nps_df[["Month", "NPS", "Promoters", "Passives", "Detractors"]])

                # Line chart of NPS over time with UCL and LCL
                # Line chart of NPS over time with UCL, LCL, and Mean of monthly NPS
        mean_monthly_nps = nps_df["NPS"].mean()
        std_nps = nps_df["NPS"].std()
        ucl = mean_monthly_nps + 3 * std_nps
        lcl = mean_monthly_nps - 3 * std_nps

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=nps_df["Month"], y=nps_df["NPS"], mode="lines+markers", name="NPS"
        ))
        fig_line.add_trace(go.Scatter(
            x=nps_df["Month"], y=[ucl]*len(nps_df), mode="lines", name="UCL (mean + 3σ)",
            line=dict(dash='dash', color='green')
        ))
        fig_line.add_trace(go.Scatter(
            x=nps_df["Month"], y=[lcl]*len(nps_df), mode="lines", name="LCL (mean - 3σ)",
            line=dict(dash='dash', color='red')
        ))
        fig_line.add_trace(go.Scatter(
            x=nps_df["Month"], y=[mean_monthly_nps]*len(nps_df), mode="lines", name="Mean Monthly NPS",
            line=dict(dash='dot', color='blue')
        ))

        # Add annotation for the mean value
        fig_line.add_annotation(
            x=nps_df["Month"].iloc[-1],  # Last month on x-axis
            y=mean_monthly_nps,
            text=f"Mean: {mean_monthly_nps:.2f}",
            showarrow=True,
            arrowhead=1,
            ax=40,
            ay=0,
            font=dict(color="blue", size=12, family="Arial"),
            bgcolor="white",
            bordercolor="blue"
        )
        fig_line.update_layout(
            title="NPS Over Time with UCL/LCL/Mean",
            xaxis_title="Month",
            yaxis_title="NPS Score"
        )
        st.plotly_chart(fig_line)

        # Donut chart for all data combined
        total_promoters = nps_df["Promoters"].sum()
        total_passives = nps_df["Passives"].sum()
        total_detractors = nps_df["Detractors"].sum()
        fig_donut = go.Figure(data=[go.Pie(
            labels=["Promoters", "Passives", "Detractors"],
            values=[total_promoters, total_passives, total_detractors],
            hole=.5
        )])
        fig_donut.update_traces(marker=dict(colors=["#2ECC71", "#f1c40f", "#E74C3C"]),)
        fig_donut.update_layout(title_text="Overall NPS Category Distribution")
        st.plotly_chart(fig_donut)
    else:
        st.error("No valid NPS scores found in the file.")