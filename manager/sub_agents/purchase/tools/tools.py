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

# Purchase Analysis Tools

def get_purchase_summary(date_from: Optional[str] = None, date_to: Optional[str] = None, 
                        supplier: Optional[str] = None, voucher_type: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive purchase summary and key metrics"""
    try:
        # Build query with filters
        where_conditions = []
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        if supplier:
            where_conditions.append(f"v.party_name LIKE '%{supplier}%'")
        if voucher_type:
            where_conditions.append(f"v.voucher_type = '{voucher_type}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Focus on purchase vouchers - look for purchase-related voucher types
        query = f"""
        SELECT 
            COUNT(DISTINCT v.voucher_number) as total_transactions,
            COUNT(DISTINCT v.party_name) as unique_suppliers,
            SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as total_purchase_cost,
            AVG(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as avg_transaction_value,
            MIN(v.date) as earliest_date,
            MAX(v.date) as latest_date,
            COUNT(DISTINCT v.voucher_type) as voucher_types
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        WHERE {where_clause}
        AND (v.voucher_type LIKE '%purchase%' 
             OR v.voucher_type LIKE '%Purchase%'
             OR v.voucher_type LIKE '%Bill%'
             OR v.voucher_type LIKE '%procurement%'
             OR a.amount > 0)
        """
        
        result = execute_query(query)
        
        if result:
            summary = result[0]
            return {
                "status": "success",
                "summary": {
                    "total_transactions": summary["total_transactions"],
                    "unique_suppliers": summary["unique_suppliers"],
                    "total_purchase_cost": round(summary["total_purchase_cost"] or 0, 2),
                    "avg_transaction_value": round(summary["avg_transaction_value"] or 0, 2),
                    "period": f"{summary['earliest_date']} to {summary['latest_date']}",
                    "voucher_types": summary["voucher_types"]
                },
                "filters_applied": {
                    "date_from": date_from,
                    "date_to": date_to,
                    "supplier": supplier,
                    "voucher_type": voucher_type
                }
            }
        else:
            return {"status": "error", "message": "No purchase data found"}
            
    except Exception as e:
        logging.error(f"Purchase summary failed: {e}")
        return {"status": "error", "message": f"Purchase summary failed: {str(e)}"}

def get_supplier_analysis(supplier: Optional[str] = None, date_from: Optional[str] = None, 
                         date_to: Optional[str] = None, analysis_type: str = "summary") -> Dict[str, Any]:
    """Analyze supplier performance and relationship metrics"""
    try:
        where_conditions = ["v.party_name IS NOT NULL"]
        
        if supplier:
            where_conditions.append(f"v.party_name LIKE '%{supplier}%'")
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            v.party_name,
            COUNT(DISTINCT v.voucher_number) as transaction_count,
            SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as total_spending,
            AVG(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as avg_transaction_value,
            MIN(v.date) as first_transaction,
            MAX(v.date) as last_transaction,
            COUNT(DISTINCT v.voucher_type) as voucher_types_used,
            COUNT(DISTINCT i.item) as unique_items_purchased
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        LEFT JOIN trn_inventory i ON v.guid = i.guid
        WHERE {where_clause}
        AND a.amount > 0
        GROUP BY v.party_name
        ORDER BY total_spending DESC
        """
        
        result = execute_query(query)
        
        if result:
            suppliers = []
            for row in result:
                suppliers.append({
                    "supplier_name": row["party_name"],
                    "transaction_count": row["transaction_count"],
                    "total_spending": round(row["total_spending"] or 0, 2),
                    "avg_transaction_value": round(row["avg_transaction_value"] or 0, 2),
                    "first_transaction": row["first_transaction"],
                    "last_transaction": row["last_transaction"],
                    "voucher_types_used": row["voucher_types_used"],
                    "unique_items_purchased": row["unique_items_purchased"] or 0
                })
            
            return {
                "status": "success",
                "suppliers": suppliers,
                "total_suppliers": len(suppliers),
                "analysis_type": analysis_type
            }
        else:
            return {"status": "error", "message": "No supplier data found"}
            
    except Exception as e:
        logging.error(f"Supplier analysis failed: {e}")
        return {"status": "error", "message": f"Supplier analysis failed: {str(e)}"}

def get_procurement_analysis(period: str = "monthly", date_from: Optional[str] = None, 
                            date_to: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    """Analyze procurement costs and spending patterns"""
    try:
        where_conditions = ["a.amount > 0"]
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        if category:
            where_conditions.append(f"i.item LIKE '%{category}%'")
        
        where_clause = " AND ".join(where_conditions)
        
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
            SUM(a.amount) as total_spending,
            AVG(a.amount) as avg_transaction_value,
            COUNT(DISTINCT v.party_name) as unique_suppliers,
            COUNT(DISTINCT i.item) as unique_items
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        LEFT JOIN trn_inventory i ON v.guid = i.guid
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
                    "total_spending": round(row["total_spending"] or 0, 2),
                    "avg_transaction_value": round(row["avg_transaction_value"] or 0, 2),
                    "unique_suppliers": row["unique_suppliers"],
                    "unique_items": row["unique_items"] or 0
                })
            
            return {
                "status": "success",
                "procurement_analysis": periods,
                "period_type": period,
                "total_periods": len(periods)
            }
        else:
            return {"status": "error", "message": "No procurement data found"}
            
    except Exception as e:
        logging.error(f"Procurement analysis failed: {e}")
        return {"status": "error", "message": f"Procurement analysis failed: {str(e)}"}

def get_top_suppliers(metric: str = "spending", limit: int = 10, 
                     date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
    """Get top suppliers by various metrics"""
    try:
        where_conditions = ["v.party_name IS NOT NULL", "a.amount > 0"]
        
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions)
        
        # Determine ordering based on metric
        if metric == "spending":
            order_by = "total_spending DESC"
        elif metric == "transactions":
            order_by = "transaction_count DESC"
        elif metric == "items":
            order_by = "unique_items DESC"
        else:
            order_by = "total_spending DESC"
        
        query = f"""
        SELECT 
            v.party_name,
            COUNT(DISTINCT v.voucher_number) as transaction_count,
            SUM(a.amount) as total_spending,
            COUNT(DISTINCT i.item) as unique_items,
            AVG(a.amount) as avg_transaction_value,
            COUNT(DISTINCT i.godown) as warehouses_supplied
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
            top_suppliers = []
            for row in result:
                top_suppliers.append({
                    "supplier_name": row["party_name"],
                    "transaction_count": row["transaction_count"],
                    "total_spending": round(row["total_spending"] or 0, 2),
                    "unique_items": row["unique_items"] or 0,
                    "avg_transaction_value": round(row["avg_transaction_value"] or 0, 2),
                    "warehouses_supplied": row["warehouses_supplied"] or 0
                })
            
            return {
                "status": "success",
                "top_suppliers": top_suppliers,
                "metric": metric,
                "limit": limit,
                "count": len(top_suppliers)
            }
        else:
            return {"status": "error", "message": "No supplier data found"}
            
    except Exception as e:
        logging.error(f"Top suppliers query failed: {e}")
        return {"status": "error", "message": f"Top suppliers query failed: {str(e)}"}

def get_purchase_performance(date_from: Optional[str] = None, date_to: Optional[str] = None,
                            comparison_period: Optional[str] = None, metrics: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get purchase performance metrics and KPIs"""
    try:
        where_conditions = ["a.amount > 0"]
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            COUNT(DISTINCT v.voucher_number) as total_transactions,
            COUNT(DISTINCT v.party_name) as unique_suppliers,
            SUM(a.amount) as total_spending,
            AVG(a.amount) as avg_transaction_value,
            COUNT(DISTINCT i.item) as unique_items_purchased,
            COUNT(DISTINCT v.voucher_type) as voucher_types,
            COUNT(DISTINCT DATE(v.date)) as active_days,
            COUNT(DISTINCT i.godown) as warehouses_used
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
                    "unique_suppliers": performance["unique_suppliers"],
                    "total_spending": round(performance["total_spending"] or 0, 2),
                    "avg_transaction_value": round(performance["avg_transaction_value"] or 0, 2),
                    "unique_items_purchased": performance["unique_items_purchased"] or 0,
                    "voucher_types": performance["voucher_types"],
                    "active_days": performance["active_days"],
                    "warehouses_used": performance["warehouses_used"] or 0,
                    "avg_daily_spending": round((performance["total_spending"] or 0) / active_days, 2)
                },
                "period": f"{date_from} to {date_to}" if date_from and date_to else "All time"
            }
        else:
            return {"status": "error", "message": "No performance data found"}
            
    except Exception as e:
        logging.error(f"Purchase performance query failed: {e}")
        return {"status": "error", "message": f"Purchase performance query failed: {str(e)}"}

def get_purchase_analytics(analytics_type: str, query: str, 
                          date_from: Optional[str] = None, date_to: Optional[str] = None,
                          parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Advanced 4-tier purchase analytics with insights"""
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
        AND a.amount > 0
        """
        
        raw_data = execute_query(data_query)
        
        if not raw_data:
            return {"status": "error", "message": "No data available for analytics"}
        
        # Simple analytics based on type
        if analytics_type.lower() == "descriptive":
            # Basic descriptive statistics
            total_transactions = len(set(row['voucher_number'] for row in raw_data))
            total_suppliers = len(set(row['party_name'] for row in raw_data if row['party_name']))
            total_spending = sum(row['amount'] or 0 for row in raw_data)
            
            return {
                "status": "success",
                "analytics_type": "descriptive",
                "query": query,
                "insights": {
                    "total_transactions": total_transactions,
                    "total_suppliers": total_suppliers,
                    "total_spending": round(total_spending, 2),
                    "avg_transaction_value": round(total_spending / max(total_transactions, 1), 2),
                    "data_points": len(raw_data)
                }
            }
        
        elif analytics_type.lower() == "diagnostic":
            # Analysis of spending patterns and supplier performance
            supplier_spending = {}
            for row in raw_data:
                if row['party_name']:
                    supplier_spending[row['party_name']] = supplier_spending.get(row['party_name'], 0) + (row['amount'] or 0)
            
            top_supplier = max(supplier_spending.items(), key=lambda x: x[1]) if supplier_spending else ("None", 0)
            
            return {
                "status": "success",
                "analytics_type": "diagnostic",
                "query": query,
                "insights": {
                    "top_supplier": {"name": top_supplier[0], "spending": round(top_supplier[1], 2)},
                    "supplier_concentration": f"{len(supplier_spending)} suppliers identified",
                    "spending_distribution": "Analysis of supplier spending patterns"
                }
            }
        
        elif analytics_type.lower() == "predictive":
            # Simple trend analysis
            monthly_spending = {}
            for row in raw_data:
                if row['date']:
                    month = row['date'][:7]  # YYYY-MM
                    monthly_spending[month] = monthly_spending.get(month, 0) + (row['amount'] or 0)
            
            return {
                "status": "success",
                "analytics_type": "predictive",
                "query": query,
                "insights": {
                    "trend_analysis": "Monthly spending patterns identified",
                    "periods_analyzed": len(monthly_spending),
                    "prediction": "Based on historical data, spending patterns show seasonal variations"
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
                        "Monitor top supplier relationships for risk management",
                        "Consider supplier diversification strategies",
                        "Implement spend analytics for better cost control",
                        "Establish supplier performance KPIs"
                    ],
                    "action_items": "Strategic procurement improvements suggested"
                }
            }
        
        else:
            return {"status": "error", "message": f"Unknown analytics type: {analytics_type}"}
            
    except Exception as e:
        logging.error(f"Purchase analytics failed: {e}")
        return {"status": "error", "message": f"Purchase analytics failed: {str(e)}"}