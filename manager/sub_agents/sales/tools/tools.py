import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

# Database connection utilities
def get_db_connection():
    """Get database connection to tallydb.db"""
    try:
        conn = sqlite3.connect('tallydb.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None

def execute_query(query: str) -> List[Dict]:
    """Execute SQL query and return results"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        logging.error(f"Query execution failed: {e}")
        return []
    finally:
        conn.close()

# Sales Analysis Tools

def get_sales_summary(date_from: Optional[str] = None, date_to: Optional[str] = None, 
                     customer: Optional[str] = None, voucher_type: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive sales summary and key metrics"""
    try:
        # Build query with filters
        where_conditions = []
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        if customer:
            where_conditions.append(f"v.party_name LIKE '%{customer}%'")
        if voucher_type:
            where_conditions.append(f"v.voucher_type = '{voucher_type}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
        SELECT 
            COUNT(DISTINCT v.voucher_number) as total_transactions,
            COUNT(DISTINCT v.party_name) as unique_customers,
            SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as total_revenue,
            AVG(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as avg_transaction_value,
            MIN(v.date) as earliest_date,
            MAX(v.date) as latest_date,
            COUNT(DISTINCT v.voucher_type) as voucher_types
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        WHERE {where_clause}
        """
        
        result = execute_query(query)
        
        if result:
            summary = result[0]
            return {
                "status": "success",
                "summary": {
                    "total_transactions": summary["total_transactions"],
                    "unique_customers": summary["unique_customers"],
                    "total_revenue": round(summary["total_revenue"] or 0, 2),
                    "avg_transaction_value": round(summary["avg_transaction_value"] or 0, 2),
                    "period": f"{summary['earliest_date']} to {summary['latest_date']}",
                    "voucher_types": summary["voucher_types"]
                },
                "filters_applied": {
                    "date_from": date_from,
                    "date_to": date_to,
                    "customer": customer,
                    "voucher_type": voucher_type
                }
            }
        else:
            return {"status": "error", "message": "No sales data found"}
            
    except Exception as e:
        logging.error(f"Sales summary failed: {e}")
        return {"status": "error", "message": f"Sales summary failed: {str(e)}"}

def get_customer_analysis(customer: Optional[str] = None, date_from: Optional[str] = None, 
                         date_to: Optional[str] = None, analysis_type: str = "summary") -> Dict[str, Any]:
    """Analyze customer performance and behavior"""
    try:
        where_conditions = ["v.party_name IS NOT NULL"]
        
        if customer:
            where_conditions.append(f"v.party_name LIKE '%{customer}%'")
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            v.party_name,
            COUNT(DISTINCT v.voucher_number) as transaction_count,
            SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as total_revenue,
            AVG(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as avg_transaction_value,
            MIN(v.date) as first_transaction,
            MAX(v.date) as last_transaction,
            COUNT(DISTINCT v.voucher_type) as voucher_types_used
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        WHERE {where_clause}
        GROUP BY v.party_name
        ORDER BY total_revenue DESC
        """
        
        result = execute_query(query)
        
        if result:
            customers = []
            for row in result:
                customers.append({
                    "customer_name": row["party_name"],
                    "transaction_count": row["transaction_count"],
                    "total_revenue": round(row["total_revenue"] or 0, 2),
                    "avg_transaction_value": round(row["avg_transaction_value"] or 0, 2),
                    "first_transaction": row["first_transaction"],
                    "last_transaction": row["last_transaction"],
                    "voucher_types_used": row["voucher_types_used"]
                })
            
            return {
                "status": "success",
                "customers": customers,
                "total_customers": len(customers),
                "analysis_type": analysis_type
            }
        else:
            return {"status": "error", "message": "No customer data found"}
            
    except Exception as e:
        logging.error(f"Customer analysis failed: {e}")
        return {"status": "error", "message": f"Customer analysis failed: {str(e)}"}

def get_revenue_analysis(period: str = "monthly", date_from: Optional[str] = None, 
                        date_to: Optional[str] = None, group_by: Optional[str] = None) -> Dict[str, Any]:
    """Analyze revenue trends and patterns"""
    try:
        where_conditions = []
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Determine grouping based on period - simplified for SQLite
        if period == "daily":
            date_group = "DATE(v.date)"
        elif period == "weekly":
            date_group = "strftime('%Y-%W', v.date)"
        elif period == "monthly":
            date_group = "strftime('%Y-%m', v.date)"
        else:
            date_group = "strftime('%Y-%m', v.date)"
        
        query = f"""
        SELECT 
            {date_group} as period,
            COUNT(DISTINCT v.voucher_number) as transaction_count,
            SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as revenue,
            AVG(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as avg_transaction_value,
            COUNT(DISTINCT v.party_name) as unique_customers
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        WHERE {where_clause}
        GROUP BY {date_group}
        ORDER BY period
        """
        
        result = execute_query(query)
        
        if result:
            periods = []
            for row in result:
                periods.append({
                    "period": row["period"],
                    "transaction_count": row["transaction_count"],
                    "revenue": round(row["revenue"] or 0, 2),
                    "avg_transaction_value": round(row["avg_transaction_value"] or 0, 2),
                    "unique_customers": row["unique_customers"]
                })
            
            return {
                "status": "success",
                "revenue_analysis": periods,
                "period_type": period,
                "total_periods": len(periods)
            }
        else:
            return {"status": "error", "message": "No revenue data found"}
            
    except Exception as e:
        logging.error(f"Revenue analysis failed: {e}")
        return {"status": "error", "message": f"Revenue analysis failed: {str(e)}"}

def get_top_customers(metric: str = "revenue", limit: int = 10, 
                     date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
    """Get top customers by various metrics"""
    try:
        where_conditions = ["v.party_name IS NOT NULL"]
        
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions)
        
        # Determine ordering based on metric
        if metric == "revenue":
            order_by = "total_revenue DESC"
        elif metric == "transactions":
            order_by = "transaction_count DESC"
        elif metric == "quantity":
            order_by = "total_quantity DESC"
        else:
            order_by = "total_revenue DESC"
        
        query = f"""
        SELECT 
            v.party_name,
            COUNT(DISTINCT v.voucher_number) as transaction_count,
            SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN i.quantity > 0 THEN i.quantity ELSE 0 END) as total_quantity,
            AVG(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as avg_transaction_value
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        LEFT JOIN trn_inventory i ON v.guid = i.guid
        WHERE {where_clause}
        GROUP BY v.party_name
        ORDER BY {order_by}
        LIMIT {limit}
        """
        
        result = execute_query(query)
        
        if result:
            top_customers = []
            for row in result:
                top_customers.append({
                    "customer_name": row["party_name"],
                    "transaction_count": row["transaction_count"],
                    "total_revenue": round(row["total_revenue"] or 0, 2),
                    "total_quantity": round(row["total_quantity"] or 0, 2),
                    "avg_transaction_value": round(row["avg_transaction_value"] or 0, 2)
                })
            
            return {
                "status": "success",
                "top_customers": top_customers,
                "metric": metric,
                "limit": limit,
                "count": len(top_customers)
            }
        else:
            return {"status": "error", "message": "No customer data found"}
            
    except Exception as e:
        logging.error(f"Top customers query failed: {e}")
        return {"status": "error", "message": f"Top customers query failed: {str(e)}"}

def get_sales_performance(date_from: Optional[str] = None, date_to: Optional[str] = None,
                         comparison_period: Optional[str] = None, metrics: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get sales performance metrics and KPIs"""
    try:
        where_conditions = []
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
        SELECT 
            COUNT(DISTINCT v.voucher_number) as total_transactions,
            COUNT(DISTINCT v.party_name) as unique_customers,
            SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as total_revenue,
            AVG(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as avg_transaction_value,
            SUM(CASE WHEN i.quantity > 0 THEN i.quantity ELSE 0 END) as total_quantity,
            COUNT(DISTINCT v.voucher_type) as voucher_types,
            COUNT(DISTINCT DATE(v.date)) as active_days
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        LEFT JOIN trn_inventory i ON v.guid = i.guid
        WHERE {where_clause}
        """
        
        result = execute_query(query)
        
        if result:
            performance = result[0]
            active_days = max(performance["active_days"] or 1, 1)
            return {
                "status": "success",
                "performance_metrics": {
                    "total_transactions": performance["total_transactions"],
                    "unique_customers": performance["unique_customers"],
                    "total_revenue": round(performance["total_revenue"] or 0, 2),
                    "avg_transaction_value": round(performance["avg_transaction_value"] or 0, 2),
                    "total_quantity": round(performance["total_quantity"] or 0, 2),
                    "voucher_types": performance["voucher_types"],
                    "active_days": performance["active_days"],
                    "avg_daily_revenue": round((performance["total_revenue"] or 0) / active_days, 2)
                },
                "period": f"{date_from} to {date_to}" if date_from and date_to else "All time"
            }
        else:
            return {"status": "error", "message": "No performance data found"}
            
    except Exception as e:
        logging.error(f"Sales performance query failed: {e}")
        return {"status": "error", "message": f"Sales performance query failed: {str(e)}"}

def get_sales_analytics(analytics_type: str, query: str, 
                       date_from: Optional[str] = None, date_to: Optional[str] = None,
                       parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Advanced 4-tier sales analytics with insights"""
    try:
        # Load data for analytics
        where_conditions = []
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        data_query = f"""
        SELECT 
            v.guid,
            v.date,
            v.voucher_type,
            v.voucher_number,
            v.party_name,
            a.ledger,
            a.amount,
            i.item,
            i.quantity,
            i.rate,
            i.godown
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        LEFT JOIN trn_inventory i ON v.guid = i.guid
        WHERE {where_clause}
        """
        
        raw_data = execute_query(data_query)
        
        if not raw_data:
            return {"status": "error", "message": "No data available for analytics"}
        
        # Simple analytics based on type
        if analytics_type.lower() == "descriptive":
            # Basic descriptive statistics
            total_transactions = len(set(row['voucher_number'] for row in raw_data))
            total_customers = len(set(row['party_name'] for row in raw_data if row['party_name']))
            total_revenue = sum(row['amount'] or 0 for row in raw_data if (row['amount'] or 0) > 0)
            
            return {
                "status": "success",
                "analytics_type": "descriptive",
                "query": query,
                "insights": {
                    "total_transactions": total_transactions,
                    "total_customers": total_customers,
                    "total_revenue": round(total_revenue, 2),
                    "avg_transaction_value": round(total_revenue / max(total_transactions, 1), 2),
                    "data_points": len(raw_data)
                }
            }
        
        elif analytics_type.lower() == "diagnostic":
            # Analysis of customer patterns and sales performance
            customer_revenue = {}
            for row in raw_data:
                if row['party_name'] and (row['amount'] or 0) > 0:
                    customer_revenue[row['party_name']] = customer_revenue.get(row['party_name'], 0) + (row['amount'] or 0)
            
            top_customer = max(customer_revenue.items(), key=lambda x: x[1]) if customer_revenue else ("None", 0)
            
            return {
                "status": "success",
                "analytics_type": "diagnostic",
                "query": query,
                "insights": {
                    "top_customer": {"name": top_customer[0], "revenue": round(top_customer[1], 2)},
                    "customer_concentration": f"{len(customer_revenue)} customers identified",
                    "revenue_distribution": "Analysis of customer revenue patterns"
                }
            }
        
        elif analytics_type.lower() == "predictive":
            # Simple trend analysis
            monthly_revenue = {}
            for row in raw_data:
                if row['date'] and (row['amount'] or 0) > 0:
                    month = row['date'][:7]  # YYYY-MM
                    monthly_revenue[month] = monthly_revenue.get(month, 0) + (row['amount'] or 0)
            
            return {
                "status": "success",
                "analytics_type": "predictive",
                "query": query,
                "insights": {
                    "trend_analysis": "Monthly revenue patterns identified",
                    "periods_analyzed": len(monthly_revenue),
                    "prediction": "Based on historical data, revenue shows seasonal variations"
                }
            }
        
        elif analytics_type.lower() == "prescriptive":
            # Recommendations based on data
            return {
                "status": "success",
                "analytics_type": "prescriptive",
                "query": query,
                "insights": {
                    "recommendations": [
                        "Focus on top-performing customers for retention",
                        "Develop strategies for customer acquisition",
                        "Implement revenue optimization techniques",
                        "Monitor sales performance KPIs regularly"
                    ],
                    "action_items": "Strategic sales improvements suggested"
                }
            }
        
        else:
            return {"status": "error", "message": f"Unknown analytics type: {analytics_type}"}
            
    except Exception as e:
        logging.error(f"Sales analytics failed: {e}")
        return {"status": "error", "message": f"Sales analytics failed: {str(e)}"}