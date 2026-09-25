import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

from database import create_tables, get_connection


# Create database tables
create_tables()


# Page configuration
st.set_page_config(
    page_title="Cable Bill Management",
    page_icon="📺",
    layout="wide"
)


# -------------------------------
# TITLE
# -------------------------------

st.title("📺 Cable Bill Payment Management System")
st.write("Manage monthly cable bills and track pending payments.")


# -------------------------------
# SIDEBAR
# -------------------------------

st.sidebar.title("Menu")

menu = st.sidebar.radio(
    "Select Option",
    [
        "Dashboard",
        "Add Customer",
        "Generate Monthly Bills",
        "View Pending Bills",
        "View All Bills",
        "Customers"
    ]
)


# -------------------------------
# DASHBOARD
# -------------------------------

if menu == "Dashboard":

    st.header("📊 Dashboard")

    conn = get_connection()

    customers = pd.read_sql_query(
        "SELECT * FROM customers",
        conn
    )

    bills = pd.read_sql_query(
        "SELECT * FROM bills",
        conn
    )

    conn.close()

    total_customers = len(customers)

    total_bills = len(bills)

    pending_bills = len(
        bills[bills["status"] == "Pending"]
    ) if not bills.empty else 0

    paid_bills = len(
        bills[bills["status"] == "Paid"]
    ) if not bills.empty else 0

    pending_amount = (
        bills.loc[
            bills["status"] == "Pending",
            "amount"
        ].sum()
        if not bills.empty
        else 0
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Customers",
        total_customers
    )

    col2.metric(
        "Total Bills",
        total_bills
    )

    col3.metric(
        "Paid Bills",
        paid_bills
    )

    col4.metric(
        "Pending Bills",
        pending_bills
    )

    col5.metric(
        "Pending Amount",
        f"₹{pending_amount:,.2f}"
    )

    st.divider()

    if not bills.empty:

        st.subheader("Monthly Bill Summary")

        summary = bills.groupby(
            ["year", "month", "status"]
        ).agg(
            Bills=("bill_id", "count"),
            Amount=("amount", "sum")
        ).reset_index()

        st.dataframe(
            summary,
            use_container_width=True
        )


# -------------------------------
# ADD CUSTOMER
# -------------------------------

elif menu == "Add Customer":

    st.header("➕ Add New Customer")

    with st.form("customer_form"):

        name = st.text_input(
            "Customer Name"
        )

        phone = st.text_input(
            "Phone Number"
        )

        address = st.text_area(
            "Address"
        )

        monthly_bill = st.number_input(
            "Monthly Bill Amount",
            min_value=0.0,
            value=300.0,
            step=10.0
        )

        submitted = st.form_submit_button(
            "Add Customer"
        )

        if submitted:

            if name.strip() == "":

                st.error(
                    "Please enter customer name."
                )

            else:

                conn = get_connection()

                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO customers
                    (name, phone, address, monthly_bill)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        name,
                        phone,
                        address,
                        monthly_bill
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    f"Customer {name} added successfully!"
                )


# -------------------------------
# GENERATE MONTHLY BILLS
# -------------------------------

elif menu == "Generate Monthly Bills":

    st.header("🧾 Generate Monthly Bills")

    conn = get_connection()

    customers = pd.read_sql_query(
        "SELECT * FROM customers",
        conn
    )

    conn.close()

    if customers.empty:

        st.warning(
            "No customers found. Add customers first."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:

            selected_month = st.selectbox(
                "Select Month",
                [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December"
                ]
            )

        with col2:

            selected_year = st.number_input(
                "Select Year",
                min_value=2020,
                max_value=2100,
                value=date.today().year
            )

        if st.button(
            "Generate Bills"
        ):

            conn = get_connection()

            cursor = conn.cursor()

            generated = 0
            skipped = 0

            for _, customer in customers.iterrows():

                cursor.execute(
                    """
                    SELECT bill_id
                    FROM bills
                    WHERE customer_id = ?
                    AND month = ?
                    AND year = ?
                    """,
                    (
                        customer["customer_id"],
                        selected_month,
                        selected_year
                    )
                )

                existing = cursor.fetchone()

                if existing:

                    skipped += 1

                else:

                    cursor.execute(
                        """
                        INSERT INTO bills
                        (
                            customer_id,
                            month,
                            year,
                            amount,
                            status
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            customer["customer_id"],
                            selected_month,
                            selected_year,
                            customer["monthly_bill"],
                            "Pending"
                        )
                    )

                    generated += 1

            conn.commit()
            conn.close()

            st.success(
                f"{generated} bills generated successfully!"
            )

            if skipped > 0:

                st.info(
                    f"{skipped} bills already existed."
                )


# -------------------------------
# VIEW PENDING BILLS
# -------------------------------

elif menu == "View Pending Bills":

    st.header("⏳ Pending Cable Bills")

    col1, col2 = st.columns(2)

    months = [
        "All",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ]

    with col1:

        selected_month = st.selectbox(
            "Month",
            months
        )

    with col2:

        selected_year = st.number_input(
            "Year",
            min_value=2020,
            max_value=2100,
            value=date.today().year
        )

    conn = get_connection()

    query = """
        SELECT
            bills.bill_id,
            customers.customer_id,
            customers.name,
            customers.phone,
            customers.address,
            bills.month,
            bills.year,
            bills.amount,
            bills.status,
            bills.payment_date
        FROM bills
        JOIN customers
        ON bills.customer_id = customers.customer_id
        WHERE bills.status = 'Pending'
        AND bills.year = ?
    """

    params = [selected_year]

    if selected_month != "All":

        query += " AND bills.month = ?"

        params.append(selected_month)

    pending = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    if pending.empty:

        st.success(
            "🎉 No pending bills found!"
        )

    else:

        st.dataframe(
            pending,
            use_container_width=True
        )

        total_pending = pending["amount"].sum()

        st.subheader(
            f"Total Pending Amount: ₹{total_pending:,.2f}"
        )

        st.divider()

        st.subheader("Mark Bill as Paid")

        bill_id = st.number_input(
            "Enter Bill ID",
            min_value=1,
            step=1
        )

        if st.button(
            "Mark as Paid"
        ):

            conn = get_connection()

            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE bills
                SET status = 'Paid',
                    payment_date = ?
                WHERE bill_id = ?
                """,
                (
                    str(date.today()),
                    bill_id
                )
            )

            conn.commit()

            affected = cursor.rowcount

            conn.close()

            if affected:

                st.success(
                    "Bill marked as paid!"
                )

                st.rerun()

            else:

                st.error(
                    "Bill ID not found."
                )

        csv = pending.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Download Pending List",
            csv,
            "pending_cable_bills.csv",
            "text/csv"
        )


# -------------------------------
# VIEW ALL BILLS
# -------------------------------

elif menu == "View All Bills":

    st.header("📋 All Cable Bills")

    conn = get_connection()

    bills = pd.read_sql_query(
        """
        SELECT
            bills.bill_id,
            customers.customer_id,
            customers.name,
            customers.phone,
            bills.month,
            bills.year,
            bills.amount,
            bills.status,
            bills.payment_date
        FROM bills
        JOIN customers
        ON bills.customer_id = customers.customer_id
        ORDER BY bills.year DESC
        """,
        conn
    )

    conn.close()

    if bills.empty:

        st.info(
            "No bills available."
        )

    else:

        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Paid", "Pending"]
        )

        if status_filter != "All":

            bills = bills[
                bills["status"] == status_filter
            ]

        st.dataframe(
            bills,
            use_container_width=True
        )


# -------------------------------
# CUSTOMERS
# -------------------------------

elif menu == "Customers":

    st.header("👥 Customer List")

    conn = get_connection()

    customers = pd.read_sql_query(
        "SELECT * FROM customers",
        conn
    )

    conn.close()

    if customers.empty:

        st.info(
            "No customers added yet."
        )

    else:

        st.dataframe(
            customers,
            use_container_width=True
        )