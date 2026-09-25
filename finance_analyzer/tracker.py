import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List


class FinanceAnalyzer:
    def __init__(self, data: Dict[str, List[Dict[str, Any]]]):
        """
        Initialize with a dictionary containing 'incomes' and 'expenses'.
        
        Example structure:
        {
            "incomes": [
                {"date": "2026-01-05", "category": "Salary", "amount": 4000},
                {"date": "2026-01-15", "category": "Freelance", "amount": 800}
            ],
            "expenses": [
                {"date": "2026-01-02", "category": "Rent", "amount": 1200},
                {"date": "2026-01-10", "category": "Groceries", "amount": 250}
            ]
        }
        """
        self.incomes_df = pd.DataFrame(data.get("incomes", []))
        self.expenses_df = pd.DataFrame(data.get("expenses", []))

        # Ensure date columns are proper datetime types
        for df in [self.incomes_df, self.expenses_df]:
            if not df.empty and "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])

    # -------------------------------------------------------------------------
    # Helper & Data Summaries
    # -------------------------------------------------------------------------

    def get_summary(self) -> pd.DataFrame:
        """Returns total income, total expenses, and net savings."""
        total_income = self.incomes_df["amount"].sum() if not self.incomes_df.empty else 0.0
        total_expense = self.expenses_df["amount"].sum() if not self.expenses_df.empty else 0.0
        net_savings = total_income - total_expense

        return pd.DataFrame([
            {"Metric": "Total Income", "Amount": total_income},
            {"Metric": "Total Expense", "Amount": total_expense},
            {"Metric": "Net Savings", "Amount": net_savings}
        ])

    # -------------------------------------------------------------------------
    # Visualization Functions
    # -------------------------------------------------------------------------

    def plot_expense_breakdown(self, chart_type: str = "pie") -> go.Figure:
        """
        Plots a breakdown of expenses by category.
        
        :param chart_type: 'pie' or 'bar'
        """
        if self.expenses_df.empty:
            raise ValueError("No expense data available.")

        df_cat = self.expenses_df.groupby("category")["amount"].sum().reset_index()

        if chart_type == "pie":
            fig = px.pie(
                df_cat,
                values="amount",
                names="category",
                title="Expense Breakdown by Category",
                hole=0.4
            )
        elif chart_type == "bar":
            fig = px.bar(
                df_cat,
                x="category",
                y="amount",
                color="category",
                title="Expense Breakdown by Category",
                text_auto=".2f"
            )
        else:
            raise ValueError("chart_type must be either 'pie' or 'bar'.")

        return fig

    def plot_income_breakdown(self) -> go.Figure:
        """Plots a donut chart of income by category."""
        if self.incomes_df.empty:
            raise ValueError("No income data available.")

        df_cat = self.incomes_df.groupby("category")["amount"].sum().reset_index()
        fig = px.pie(
            df_cat,
            values="amount",
            names="category",
            title="Income Sources",
            hole=0.4
        )
        return fig

    def plot_monthly_trend(self) -> go.Figure:
        """Plots a multi-line chart comparing Income vs Expense over time."""
        inc_monthly = (
            self.incomes_df.set_index("date")
            .resample("ME")["amount"]
            .sum()
            .reset_index()
            if not self.incomes_df.empty
            else pd.DataFrame(columns=["date", "amount"])
        )
        exp_monthly = (
            self.expenses_df.set_index("date")
            .resample("ME")["amount"]
            .sum()
            .reset_index()
            if not self.expenses_df.empty
            else pd.DataFrame(columns=["date", "amount"])
        )

        fig = go.Figure()

        if not inc_monthly.empty:
            fig.add_trace(go.Scatter(
                x=inc_monthly["date"],
                y=inc_monthly["amount"],
                mode="lines+markers",
                name="Income",
                line=dict(color="#2ca02c", width=3)
            ))

        if not exp_monthly.empty:
            fig.add_trace(go.Scatter(
                x=exp_monthly["date"],
                y=exp_monthly["amount"],
                mode="lines+markers",
                name="Expense",
                line=dict(color="#d62728", width=3)
            ))

        fig.update_layout(
            title="Monthly Income vs Expenses Trend",
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            hovermode="x unified"
        )
        return fig

    def plot_cashflow_waterfall(self) -> go.Figure:
        """Generates a waterfall chart showing total income minus categorized expenses."""
        income_sum = self.incomes_df["amount"].sum() if not self.incomes_df.empty else 0.0
        exp_by_cat = (
            self.expenses_df.groupby("category")["amount"].sum().to_dict()
            if not self.expenses_df.empty
            else {}
        )

        x_vals = ["Total Income"] + list(exp_by_cat.keys()) + ["Net Savings"]
        y_vals = [income_sum] + [-val for val in exp_by_cat.values()] + [0]
        measures = ["relative"] * (len(x_vals) - 1) + ["total"]

        fig = go.Figure(go.Waterfall(
            name="Cashflow",
            orientation="v",
            measure=measures,
            x=x_vals,
            y=y_vals,
            connector=dict(line=dict(color="rgb(63, 63, 63)")),
            decreasing=dict(marker=dict(color="#e74c3c")),
            increasing=dict(marker=dict(color="#2ecc71")),
            totals=dict(marker=dict(color="#3498db"))
        ))

        fig.update_layout(
            title="Cashflow Breakdown (Waterfall)",
            yaxis_title="Amount ($)"
        )
        return fig

    def plot_stacked_expense_trend(self) -> go.Figure:
        """Stacked bar chart showing category-level spending month by month."""
        if self.expenses_df.empty:
            raise ValueError("No expense data available.")
            
        df = self.expenses_df.copy()
        df["month"] = df["date"].dt.to_period("M").astype(str)
        df_grouped = df.groupby(["month", "category"])["amount"].sum().reset_index()

        fig = px.bar(
            df_grouped,
            x="month",
            y="amount",
            color="category",
            title="Monthly Expense Breakdown by Category",
            barmode="stack"
        )
        return fig

    def plot_cumulative_savings(self) -> go.Figure:
        """Area chart showing cumulative net savings over time."""
        inc = self.incomes_df.copy()
        exp = self.expenses_df.copy()
        
        inc["type"] = "income"
        exp["type"] = "expense"
        exp["amount"] = -exp["amount"]  # Subtract expenses
        
        combined = pd.concat([inc, exp]).sort_values("date")
        combined["net_cumsum"] = combined["amount"].cumsum()

        fig = px.area(
            combined,
            x="date",
            y="net_cumsum",
            title="Cumulative Savings Over Time",
            labels={"net_cumsum": "Savings ($)", "date": "Date"}
        )
        return fig
