import sqlite3
import logging
from datetime import datetime, timedelta
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

# Manager Coordination Tools

def get_business_overview(date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive business overview across all departments"""
    try:
        where_conditions = []
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Comprehensive business metrics query
        query = f"""
        SELECT 
            -- Transaction Overview
            COUNT(DISTINCT v.voucher_number) as total_transactions,
            COUNT(DISTINCT v.party_name) as unique_parties,
            COUNT(DISTINCT v.voucher_type) as voucher_types,
            
            -- Financial Metrics
            SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as total_inflows,
            SUM(CASE WHEN a.amount < 0 THEN ABS(a.amount) ELSE 0 END) as total_outflows,
            SUM(a.amount) as net_position,
            
            -- Inventory Metrics
            COUNT(DISTINCT i.item) as unique_items,
            COUNT(DISTINCT i.godown) as active_warehouses,
            SUM(CASE WHEN i.quantity > 0 THEN i.quantity ELSE 0 END) as total_inward_qty,
            SUM(CASE WHEN i.quantity < 0 THEN ABS(i.quantity) ELSE 0 END) as total_outward_qty,
            
            -- Time Period
            MIN(v.date) as period_start,
            MAX(v.date) as period_end,
            COUNT(DISTINCT DATE(v.date)) as active_days
            
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        LEFT JOIN trn_inventory i ON v.guid = i.guid
        WHERE {where_clause}
        """
        
        result = execute_query(query)
        
        if result:
            data = result[0]
            active_days = max(data["active_days"] or 1, 1)
            
            return {
                "status": "success",
                "business_overview": {
                    "transaction_metrics": {
                        "total_transactions": data["total_transactions"],
                        "unique_parties": data["unique_parties"],
                        "voucher_types": data["voucher_types"],
                        "active_days": data["active_days"]
                    },
                    "financial_metrics": {
                        "total_inflows": round(data["total_inflows"] or 0, 2),
                        "total_outflows": round(data["total_outflows"] or 0, 2),
                        "net_position": round(data["net_position"] or 0, 2),
                        "daily_avg_inflows": round((data["total_inflows"] or 0) / active_days, 2),
                        "daily_avg_outflows": round((data["total_outflows"] or 0) / active_days, 2)
                    },
                    "operational_metrics": {
                        "unique_items": data["unique_items"] or 0,
                        "active_warehouses": data["active_warehouses"] or 0,
                        "total_inward_qty": round(data["total_inward_qty"] or 0, 2),
                        "total_outward_qty": round(data["total_outward_qty"] or 0, 2),
                        "inventory_turnover": "High" if data["total_outward_qty"] and data["total_inward_qty"] else "Low"
                    },
                    "period_info": {
                        "start_date": data["period_start"],
                        "end_date": data["period_end"],
                        "duration_days": active_days
                    }
                }
            }
        else:
            return {"status": "error", "message": "No business data found"}
            
    except Exception as e:
        logging.error(f"Business overview failed: {e}")
        return {"status": "error", "message": f"Business overview failed: {str(e)}"}

def get_kpi_dashboard(date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
    """Get key performance indicators across all business functions"""
    try:
        where_conditions = []
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # KPI calculation query
        query = f"""
        SELECT 
            -- Revenue KPIs
            SUM(CASE WHEN a.amount > 0 AND v.voucher_type LIKE '%sale%' THEN a.amount ELSE 0 END) as sales_revenue,
            COUNT(DISTINCT CASE WHEN a.amount > 0 AND v.voucher_type LIKE '%sale%' THEN v.party_name END) as active_customers,
            
            -- Cost KPIs  
            SUM(CASE WHEN a.amount > 0 AND v.voucher_type LIKE '%purchase%' THEN a.amount ELSE 0 END) as purchase_costs,
            COUNT(DISTINCT CASE WHEN a.amount > 0 AND v.voucher_type LIKE '%purchase%' THEN v.party_name END) as active_suppliers,
            
            -- Operational KPIs
            COUNT(DISTINCT v.voucher_number) as total_transactions,
            COUNT(DISTINCT DATE(v.date)) as operational_days,
            
            -- Cash Flow KPIs
            SUM(CASE WHEN a.ledger LIKE '%cash%' AND a.amount > 0 THEN a.amount ELSE 0 END) as cash_inflows,
            SUM(CASE WHEN a.ledger LIKE '%cash%' AND a.amount < 0 THEN ABS(a.amount) ELSE 0 END) as cash_outflows
            
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        WHERE {where_clause}
        """
        
        result = execute_query(query)
        
        if result:
            data = result[0]
            operational_days = max(data["operational_days"] or 1, 1)
            
            # Calculate derived KPIs
            sales_revenue = data["sales_revenue"] or 0
            purchase_costs = data["purchase_costs"] or 0
            gross_margin = sales_revenue - purchase_costs
            margin_percentage = (gross_margin / sales_revenue * 100) if sales_revenue > 0 else 0
            
            return {
                "status": "success",
                "kpi_dashboard": {
                    "revenue_kpis": {
                        "total_sales_revenue": round(sales_revenue, 2),
                        "active_customers": data["active_customers"] or 0,
                        "avg_daily_sales": round(sales_revenue / operational_days, 2),
                        "revenue_per_customer": round(sales_revenue / max(data["active_customers"] or 1, 1), 2)
                    },
                    "cost_kpis": {
                        "total_purchase_costs": round(purchase_costs, 2),
                        "active_suppliers": data["active_suppliers"] or 0,
                        "avg_daily_purchases": round(purchase_costs / operational_days, 2),
                        "cost_per_supplier": round(purchase_costs / max(data["active_suppliers"] or 1, 1), 2)
                    },
                    "profitability_kpis": {
                        "gross_margin": round(gross_margin, 2),
                        "margin_percentage": round(margin_percentage, 2),
                        "revenue_cost_ratio": round(sales_revenue / max(purchase_costs, 1), 2)
                    },
                    "operational_kpis": {
                        "total_transactions": data["total_transactions"],
                        "operational_days": operational_days,
                        "transactions_per_day": round(data["total_transactions"] / operational_days, 2)
                    },
                    "cash_flow_kpis": {
                        "cash_inflows": round(data["cash_inflows"] or 0, 2),
                        "cash_outflows": round(data["cash_outflows"] or 0, 2),
                        "net_cash_flow": round((data["cash_inflows"] or 0) - (data["cash_outflows"] or 0), 2)
                    }
                }
            }
        else:
            return {"status": "error", "message": "No KPI data found"}
            
    except Exception as e:
        logging.error(f"KPI dashboard failed: {e}")
        return {"status": "error", "message": f"KPI dashboard failed: {str(e)}"}

def get_cross_functional_analysis(analysis_type: str = "sales_inventory", 
                                date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
    """Perform cross-functional analysis between different business areas"""
    try:
        where_conditions = []
        if date_from:
            where_conditions.append(f"v.date >= '{date_from}'")
        if date_to:
            where_conditions.append(f"v.date <= '{date_to}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        if analysis_type == "sales_inventory":
            # Sales vs Inventory correlation
            query = f"""
            SELECT 
                i.item,
                SUM(CASE WHEN i.quantity < 0 THEN ABS(i.quantity) ELSE 0 END) as items_sold,
                SUM(CASE WHEN i.quantity > 0 THEN i.quantity ELSE 0 END) as items_purchased,
                SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as revenue_generated,
                COUNT(DISTINCT v.party_name) as customers_involved
            FROM trn_voucher v
            LEFT JOIN trn_accounting a ON v.guid = a.guid
            LEFT JOIN trn_inventory i ON v.guid = i.guid
            WHERE {where_clause} AND i.item IS NOT NULL
            GROUP BY i.item
            HAVING items_sold > 0
            ORDER BY revenue_generated DESC
            LIMIT 20
            """
            
        elif analysis_type == "supplier_customer":
            # Supplier vs Customer relationship
            query = f"""
            SELECT 
                v.party_name,
                SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as total_inflows,
                SUM(CASE WHEN a.amount < 0 THEN ABS(a.amount) ELSE 0 END) as total_outflows,
                COUNT(DISTINCT v.voucher_type) as transaction_types,
                'Mixed' as relationship_type
            FROM trn_voucher v
            LEFT JOIN trn_accounting a ON v.guid = a.guid
            WHERE {where_clause} AND v.party_name IS NOT NULL
            GROUP BY v.party_name
            HAVING total_inflows > 0 AND total_outflows > 0
            ORDER BY (total_inflows + total_outflows) DESC
            LIMIT 15
            """
            
        else:  # financial_operational
            # Financial vs Operational metrics
            query = f"""
            SELECT 
                strftime('%Y-%m', v.date) as month,
                COUNT(DISTINCT v.voucher_number) as transactions,
                SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as inflows,
                SUM(CASE WHEN a.amount < 0 THEN ABS(a.amount) ELSE 0 END) as outflows,
                COUNT(DISTINCT i.item) as unique_items,
                COUNT(DISTINCT v.party_name) as unique_parties
            FROM trn_voucher v
            LEFT JOIN trn_accounting a ON v.guid = a.guid
            LEFT JOIN trn_inventory i ON v.guid = i.guid
            WHERE {where_clause}
            GROUP BY strftime('%Y-%m', v.date)
            ORDER BY month
            """
        
        result = execute_query(query)
        
        if result:
            return {
                "status": "success",
                "analysis_type": analysis_type,
                "cross_functional_insights": result,
                "data_points": len(result),
                "summary": f"Cross-functional analysis completed for {analysis_type} with {len(result)} data points"
            }
        else:
            return {"status": "error", "message": f"No data found for {analysis_type} analysis"}
            
    except Exception as e:
        logging.error(f"Cross-functional analysis failed: {e}")
        return {"status": "error", "message": f"Cross-functional analysis failed: {str(e)}"}

def get_strategic_insights(focus_area: str = "overall") -> Dict[str, Any]:
    """Generate strategic business insights and recommendations"""
    try:
        # Get recent data for strategic analysis
        recent_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        query = f"""
        SELECT 
            COUNT(DISTINCT v.voucher_number) as total_transactions,
            COUNT(DISTINCT v.party_name) as total_parties,
            SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) as total_inflows,
            SUM(CASE WHEN a.amount < 0 THEN ABS(a.amount) ELSE 0 END) as total_outflows,
            COUNT(DISTINCT i.item) as total_items,
            COUNT(DISTINCT v.voucher_type) as voucher_types,
            AVG(CASE WHEN a.amount > 0 THEN a.amount END) as avg_inflow_amount,
            AVG(CASE WHEN a.amount < 0 THEN ABS(a.amount) END) as avg_outflow_amount
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        LEFT JOIN trn_inventory i ON v.guid = i.guid
        WHERE v.date >= '{recent_date}'
        """
        
        result = execute_query(query)
        
        if result:
            data = result[0]
            
            # Generate strategic insights based on data
            insights = []
            recommendations = []
            
            # Transaction volume insights
            if data["total_transactions"] > 1000:
                insights.append("High transaction volume indicates active business operations")
                recommendations.append("Implement automation for transaction processing efficiency")
            else:
                insights.append("Moderate transaction volume suggests room for business growth")
                recommendations.append("Focus on customer acquisition and market expansion")
            
            # Financial health insights
            net_position = (data["total_inflows"] or 0) - (data["total_outflows"] or 0)
            if net_position > 0:
                insights.append("Positive cash flow indicates healthy financial position")
                recommendations.append("Consider strategic investments for business expansion")
            else:
                insights.append("Negative cash flow requires attention to liquidity management")
                recommendations.append("Review cost structure and optimize cash flow management")
            
            # Operational diversity insights
            if data["total_items"] > 50:
                insights.append("Diverse product portfolio provides multiple revenue streams")
                recommendations.append("Analyze top-performing products for focused marketing")
            
            # Party relationship insights
            if data["total_parties"] > 100:
                insights.append("Extensive network of business relationships")
                recommendations.append("Implement CRM system for better relationship management")
            
            return {
                "status": "success",
                "strategic_analysis": {
                    "focus_area": focus_area,
                    "analysis_period": f"Last 90 days from {recent_date}",
                    "key_metrics": {
                        "transaction_volume": data["total_transactions"],
                        "business_network": data["total_parties"],
                        "financial_position": round(net_position, 2),
                        "operational_diversity": data["total_items"]
                    },
                    "strategic_insights": insights,
                    "recommendations": recommendations,
                    "priority_actions": [
                        "Monitor cash flow trends weekly",
                        "Review top customer and supplier relationships",
                        "Analyze product performance and profitability",
                        "Implement business intelligence dashboards"
                    ]
                }
            }
        else:
            return {"status": "error", "message": "Insufficient data for strategic analysis"}
            
    except Exception as e:
        logging.error(f"Strategic insights failed: {e}")
        return {"status": "error", "message": f"Strategic insights failed: {str(e)}"}
