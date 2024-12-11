from flask import Flask, render_template, request
import pyodbc
import pandas as pd

app = Flask(__name__)

# Database connection details
server = 'server number'
login ='your login id'
password ='security key'
database = 'database name '


def get_connection():
    return pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};UID={login};PWD={password};DATABASE={database};'
    )


def fetch_filter_options():
    try:
        conn = get_connection()
        query = "stored procedure name"
        df = pd.read_sql(query, conn)
        conn.close()
        return {
            "CustomerPoNo": df['CustomerPoNo'].dropna().unique().tolist(),
            "InternalPoNo": df['InternalPoNo'].dropna().unique().tolist(),
            "Brand": df['brand'].dropna().unique().tolist(),
            "Color": df['Color'].dropna().unique().tolist(),
            "StyleNo": df['StyleNo'].dropna().unique().tolist(),
            "Category": df['Category'].dropna().unique().tolist(),
            "SubCategory": df['SubCategory'].dropna().unique().tolist(),
            "ExFactory": df['ExFactory'].dropna().unique().tolist(),
        }
    except Exception as e:
        print(f"Error fetching filter options: {str(e)}")
        return {}


def fetch_table_data(filters=None):
    try:
        conn = get_connection()
        sql = """
        EXEC pivot_table @CustomerPoNo=?, @InternalPoNo=?, @Color=?, @PoOrder=?, 
            @StyleNo=?, @Category=?, @SubCategory=?, @ExFactory=?
        """

        # Build parameters list with None for filters set to 'all'
        params = [
            filters.get("CustomerPoNo") if filters.get("CustomerPoNo") and filters.get(
                "CustomerPoNo") != 'all' else None,
            filters.get("InternalPoNo") if filters.get("InternalPoNo") and filters.get(
                "InternalPoNo") != 'all' else None,
            filters.get("Color") if filters.get("Color") and filters.get("Color") != 'all' else None,
            filters.get("PoOrder") if filters.get("PoOrder") and filters.get("PoOrder") != 'all' else None,
            filters.get("StyleNo") if filters.get("StyleNo") and filters.get("StyleNo") != 'all' else None,
            filters.get("Category") if filters.get("Category") and filters.get("Category") != 'all' else None,
            filters.get("SubCategory") if filters.get("SubCategory") and filters.get("SubCategory") != 'all' else None,
            filters.get("ExFactory") if filters.get("ExFactory") and filters.get("ExFactory") != 'all' else None,
        ]

        df = pd.read_sql(sql, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"Error fetching table data: {str(e)}")
        return pd.DataFrame()


@app.route('/', methods=['GET', 'POST'])
def index():
    filter_options = fetch_filter_options()

    # Capture filters from the form if POST request
    selected_filters = {key: request.form.get(key) for key in filter_options if request.form.get(key)}

    # Fetch base table data with the selected filters
    base_table = fetch_table_data(selected_filters)
    data = base_table.to_dict(orient='records')

    # Set hidden columns
    hidden_columns = ["StyleDescription", "Color", "Category", "SubCategory", "OrderType", "MasterBrandCode", "ExFactory"]

    # Determine which columns to display (if 'active_cols' are passed, use them)
    columns_to_display = request.form.getlist('active_cols') or hidden_columns

    data_columns = list(base_table.columns)
    return render_template('index.html',
                           filter_options=filter_options,
                           selected_filters=selected_filters or {},
                           data=data,
                           data_columns=data_columns,
                           hidden_columns=hidden_columns,
                           active_columns=columns_to_display)

if __name__ == "__main__":
    app.run(debug=True)
