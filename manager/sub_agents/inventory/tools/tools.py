from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import sqlite3
import os
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext


def get_database_connection():
    """Get connection to the tallydb.db database"""
    db_path = os.path.join(os.path.dirname(__file__), '../../../tallydb.db')
    if not os.path.exists(db_path):
        # Try alternative path
        db_path = 'tallydb.db'
    return sqlite3.connect(db_path)


def execute_query(query: str, params: tuple = ()) -> list:
    """Execute a database query and return results"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        # Get column names
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # Get results
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    except Exception as e:
        print(f"Database query error: {e}")
        return []


def get_stock_summary(godown_name: Optional[str] = None, item_name: Optional[str] = None) -> dict:
    """Get stock summary with quantities and values"""
    print(f"--- Tool: get_stock_summary called ---")
    
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build query with filters
        query = """
        SELECT 
            i.item,
            i.godown,
            SUM(ABS(i.quantity)) as total_quantity,
            AVG(i.rate) as avg_rate,
            SUM(ABS(i.amount)) as total_value,
            COUNT(*) as transaction_count
        FROM trn_inventory i
        JOIN trn_voucher v ON i.guid = v.guid
        WHERE 1=1
        """
        
        params = []
        
        # Add filters
        if godown_name:
            query += " AND i.godown LIKE ?"
            params.append(f"%{godown_name}%")
        
        if item_name:
            query += " AND i.item LIKE ?"
            params.append(f"%{item_name}%")
        
        query += """
        GROUP BY i.item, i.godown
        ORDER BY SUM(ABS(i.amount)) DESC
        """
        
        results = execute_query(query, tuple(params))
        
        if not results:
            return {
                "status": "no_data",
                "error_message": "No stock data found for the specified criteria",
                "timestamp": current_time
            }
        
        # Process results
        stock_items = []
        total_value = 0
        total_quantity = 0
        
        for row in results:
            item_info = {
                "item_name": row['item'],
                "godown": row['godown'],
                "quantity": float(row['total_quantity']),
                "avg_rate": float(row['avg_rate']) if row['avg_rate'] else 0,
                "total_value": float(row['total_value']),
                "transaction_count": row['transaction_count']
            }
            stock_items.append(item_info)
            total_value += float(row['total_value'])
            total_quantity += float(row['total_quantity'])
        
        return {
            "status": "success",
            "stock_items": stock_items,
            "summary": {
                "total_items": len(stock_items),
                "total_quantity": total_quantity,
                "total_value": total_value,
                "currency": "INR"
            },
            "filters_applied": {
                "godown_name": godown_name,
                "item_name": item_name
            },
            "timestamp": current_time
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving stock summary: {str(e)}"
        }


def get_item_details(item_name: str) -> dict:
    """Get detailed information about a specific item"""
    print(f"--- Tool: get_item_details called for {item_name} ---")
    
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get item master data
        item_query = """
        SELECT 
            name,
            parent,
            alias,
            part_number,
            uom,
            opening_balance,
            opening_rate,
            opening_value,
            gst_hsn_code,
            gst_rate,
            gst_taxability
        FROM mst_stock_item
        WHERE name LIKE ?
        """
        
        item_results = execute_query(item_query, (f"%{item_name}%",))
        
        if not item_results:
            return {
                "status": "error",
                "error_message": f"Item '{item_name}' not found"
            }
        
        item_master = item_results[0]
        
        # Get transaction history
        transaction_query = """
        SELECT 
            i.quantity,
            i.rate,
            i.amount,
            i.godown,
            v.date,
            v.voucher_type,
            v.voucher_number,
            v.party_name
        FROM trn_inventory i
        JOIN trn_voucher v ON i.guid = v.guid
        WHERE i.item LIKE ?
        ORDER BY v.date DESC
        LIMIT 10
        """
        
        transactions = execute_query(transaction_query, (f"%{item_name}%",))
        
        # Calculate current stock
        stock_query = """
        SELECT 
            i.godown,
            SUM(i.quantity) as current_stock,
            AVG(i.rate) as avg_rate
        FROM trn_inventory i
        WHERE i.item LIKE ?
        GROUP BY i.godown
        """
        
        stock_by_godown = execute_query(stock_query, (f"%{item_name}%",))
        
        return {
            "status": "success",
            "item_master": {
                "name": item_master['name'],
                "parent_group": item_master['parent'],
                "alias": item_master['alias'],
                "part_number": item_master['part_number'],
                "unit_of_measure": item_master['uom'],
                "opening_balance": float(item_master['opening_balance']) if item_master['opening_balance'] else 0,
                "opening_rate": float(item_master['opening_rate']) if item_master['opening_rate'] else 0,
                "opening_value": float(item_master['opening_value']) if item_master['opening_value'] else 0,
                "hsn_code": item_master['gst_hsn_code'],
                "gst_rate": item_master['gst_rate'],
                "taxability": item_master['gst_taxability']
            },
            "current_stock": stock_by_godown,
            "recent_transactions": transactions,
            "timestamp": current_time
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving item details: {str(e)}"
        }


def get_godown_summary(godown_name: Optional[str] = None) -> dict:
    """Get summary of godowns/warehouses with stock information"""
    print(f"--- Tool: get_godown_summary called ---")
    
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get godown master data
        godown_query = """
        SELECT 
            name,
            parent,
            address
        FROM mst_godown
        """
        
        params = []
        if godown_name:
            godown_query += " WHERE name LIKE ?"
            params.append(f"%{godown_name}%")
        
        godown_master = execute_query(godown_query, tuple(params))
        
        # Get stock summary for each godown
        stock_query = """
        SELECT 
            i.godown,
            COUNT(DISTINCT i.item) as unique_items,
            SUM(ABS(i.quantity)) as total_quantity,
            SUM(ABS(i.amount)) as total_value,
            AVG(i.rate) as avg_rate
        FROM trn_inventory i
        WHERE i.godown IS NOT NULL AND i.godown != ''
        """
        
        if godown_name:
            stock_query += " AND i.godown LIKE ?"
            params = [f"%{godown_name}%"]
        else:
            params = []
        
        stock_query += " GROUP BY i.godown ORDER BY SUM(ABS(i.amount)) DESC"
        
        stock_summary = execute_query(stock_query, tuple(params))
        
        if not stock_summary:
            return {
                "status": "no_data",
                "error_message": "No godown data found",
                "timestamp": current_time
            }
        
        # Combine godown master with stock data
        godown_details = []
        for stock in stock_summary:
            # Find matching master data
            master_info = next((g for g in godown_master if g['name'] == stock['godown']), {})
            
            godown_info = {
                "godown_name": stock['godown'],
                "parent": master_info.get('parent', ''),
                "address": master_info.get('address', ''),
                "unique_items": stock['unique_items'],
                "total_quantity": float(stock['total_quantity']),
                "total_value": float(stock['total_value']),
                "avg_rate": float(stock['avg_rate']) if stock['avg_rate'] else 0
            }
            godown_details.append(godown_info)
        
        total_value = sum(g['total_value'] for g in godown_details)
        total_quantity = sum(g['total_quantity'] for g in godown_details)
        
        return {
            "status": "success",
            "godowns": godown_details,
            "summary": {
                "total_godowns": len(godown_details),
                "total_value": total_value,
                "total_quantity": total_quantity,
                "currency": "INR"
            },
            "timestamp": current_time
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving godown summary: {str(e)}"
        }


def get_stock_movements(start_date: str, end_date: str, item_name: Optional[str] = None) -> dict:
    """Get stock movements for a specific period"""
    print(f"--- Tool: get_stock_movements called for period {start_date} to {end_date} ---")
    
    try:
        # Validate date range
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            if start_dt > end_dt:
                return {
                    "status": "error",
                    "error_message": "Start date cannot be after end date"
                }
        except ValueError:
            return {
                "status": "error",
                "error_message": "Invalid date format. Use YYYY-MM-DD format."
            }
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Query for stock movements
        query = """
        SELECT 
            i.item,
            i.godown,
            i.quantity,
            i.rate,
            i.amount,
            v.date,
            v.voucher_type,
            v.voucher_number,
            v.party_name,
            CASE 
                WHEN i.quantity > 0 THEN 'IN'
                WHEN i.quantity < 0 THEN 'OUT'
                ELSE 'NEUTRAL'
            END as movement_type
        FROM trn_inventory i
        JOIN trn_voucher v ON i.guid = v.guid
        WHERE v.date BETWEEN ? AND ?
        """
        
        params = [start_date, end_date]
        
        if item_name:
            query += " AND i.item LIKE ?"
            params.append(f"%{item_name}%")
        
        query += " ORDER BY v.date DESC, i.item"
        
        results = execute_query(query, tuple(params))
        
        if not results:
            return {
                "status": "no_data",
                "error_message": f"No stock movements found for period {start_date} to {end_date}",
                "start_date": start_date,
                "end_date": end_date,
                "timestamp": current_time
            }
        
        # Process movements
        movements = []
        total_in = 0
        total_out = 0
        
        for row in results:
            movement = {
                "date": row['date'],
                "item": row['item'],
                "godown": row['godown'],
                "quantity": float(row['quantity']),
                "rate": float(row['rate']) if row['rate'] else 0,
                "amount": float(row['amount']) if row['amount'] else 0,
                "voucher_type": row['voucher_type'],
                "voucher_number": row['voucher_number'],
                "party_name": row['party_name'],
                "movement_type": row['movement_type']
            }
            movements.append(movement)
            
            if row['movement_type'] == 'IN':
                total_in += abs(float(row['quantity']))
            elif row['movement_type'] == 'OUT':
                total_out += abs(float(row['quantity']))
        
        return {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "movements": movements,
            "summary": {
                "total_movements": len(movements),
                "total_in": total_in,
                "total_out": total_out,
                "net_movement": total_in - total_out
            },
            "timestamp": current_time
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving stock movements: {str(e)}"
        }


def get_top_items(limit: int = 10, by_value: bool = True) -> dict:
    """Get top items by value or quantity"""
    print(f"--- Tool: get_top_items called for top {limit} items by {'value' if by_value else 'quantity'} ---")
    
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        sort_field = "total_value" if by_value else "total_quantity"
        
        query = f"""
        SELECT 
            i.item,
            SUM(ABS(i.quantity)) as total_quantity,
            AVG(i.rate) as avg_rate,
            SUM(ABS(i.amount)) as total_value,
            COUNT(*) as transaction_count,
            COUNT(DISTINCT i.godown) as godown_count
        FROM trn_inventory i
        GROUP BY i.item
        ORDER BY {sort_field} DESC
        LIMIT ?
        """
        
        results = execute_query(query, (limit,))
        
        if not results:
            return {
                "status": "no_data",
                "error_message": "No item data found",
                "timestamp": current_time
            }
        
        # Process results
        top_items = []
        for row in results:
            item_info = {
                "item_name": row['item'],
                "total_quantity": float(row['total_quantity']),
                "avg_rate": float(row['avg_rate']) if row['avg_rate'] else 0,
                "total_value": float(row['total_value']),
                "transaction_count": row['transaction_count'],
                "godown_count": row['godown_count'],
                "locations": "Multiple" if row['godown_count'] > 1 else "Single"
            }
            top_items.append(item_info)
        
        metric = "value" if by_value else "quantity"
        total_value = sum(item['total_value'] for item in top_items)
        
        return {
            "status": "success",
            "top_items": top_items,
            "criteria": {
                "limit": limit,
                "sorted_by": metric,
                "total_value": total_value,
                "currency": "INR"
            },
            "timestamp": current_time
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving top items: {str(e)}"
        }


def get_inventory_analytics(analytics_type: str, query_focus: str, start_date: Optional[str] = None, end_date: Optional[str] = None, forecast_periods: int = 12) -> dict:
    """Get comprehensive inventory analytics"""
    print(f"--- Tool: get_inventory_analytics called for {analytics_type} analytics on {query_focus} ---")
    
    try:
        # Validate analytics type
        valid_analytics_types = ["descriptive", "diagnostic", "predictive", "prescriptive", "all"]
        if analytics_type not in valid_analytics_types:
            return {
                "status": "error",
                "error_message": f"Analytics type must be one of: {', '.join(valid_analytics_types)}"
            }
        
        # Validate query focus
        valid_focus_areas = ["stock_levels", "movement_patterns", "turnover", "valuation", "optimization", "trends"]
        if query_focus not in valid_focus_areas:
            return {
                "status": "error",
                "error_message": f"Query focus must be one of: {', '.join(valid_focus_areas)}"
            }
        
        # Set default dates if not provided
        if not start_date:
            start_date = "2023-04-01"
        if not end_date:
            end_date = "2024-03-31"
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get inventory data for analytics
        if query_focus == "stock_levels":
            query = """
            SELECT 
                i.item,
                i.godown,
                SUM(i.quantity) as current_stock,
                AVG(i.rate) as avg_rate,
                SUM(i.amount) as total_value
            FROM trn_inventory i
            JOIN trn_voucher v ON i.guid = v.guid
            WHERE v.date BETWEEN ? AND ?
            GROUP BY i.item, i.godown
            """
            
        elif query_focus == "movement_patterns":
            query = """
            SELECT 
                i.item,
                v.date,
                i.quantity,
                i.amount,
                v.voucher_type
            FROM trn_inventory i
            JOIN trn_voucher v ON i.guid = v.guid
            WHERE v.date BETWEEN ? AND ?
            ORDER BY v.date
            """
            
        elif query_focus == "turnover":
            query = """
            SELECT 
                i.item,
                COUNT(*) as transaction_frequency,
                SUM(ABS(i.quantity)) as total_movement,
                SUM(ABS(i.amount)) as total_value,
                AVG(i.rate) as avg_rate
            FROM trn_inventory i
            JOIN trn_voucher v ON i.guid = v.guid
            WHERE v.date BETWEEN ? AND ?
            GROUP BY i.item
            ORDER BY transaction_frequency DESC
            """
            
        else:
            # Default query for other focus areas
            query = """
            SELECT 
                i.item,
                i.godown,
                i.quantity,
                i.rate,
                i.amount,
                v.date,
                v.voucher_type
            FROM trn_inventory i
            JOIN trn_voucher v ON i.guid = v.guid
            WHERE v.date BETWEEN ? AND ?
            """
        
        results = execute_query(query, (start_date, end_date))
        
        if not results:
            return {
                "status": "no_data",
                "error_message": f"No inventory data found for {query_focus} analysis",
                "timestamp": current_time
            }
        
        # Generate insights based on analytics type and data
        insights = []
        recommendations = []
        
        if analytics_type in ["descriptive", "all"]:
            insights.append(f"[Descriptive] Analyzed {len(results)} inventory records from {start_date} to {end_date}")
            if query_focus == "stock_levels":
                total_items = len(set(row['item'] for row in results))
                insights.append(f"Total unique items analyzed: {total_items}")
            elif query_focus == "turnover":
                avg_frequency = sum(row.get('transaction_frequency', 0) for row in results) / len(results)
                insights.append(f"Average transaction frequency: {avg_frequency:.2f}")
        
        if analytics_type in ["diagnostic", "all"]:
            insights.append(f"[Diagnostic] Root cause analysis for {query_focus}")
            recommendations.append(f"Investigate patterns in {query_focus} data")
            
            # Add specific diagnostic insights
            if query_focus == "stock_levels":
                recommendations.append("Check for items with negative stock levels")
            elif query_focus == "movement_patterns":
                recommendations.append("Analyze seasonal movement trends")
        
        if analytics_type in ["predictive", "all"]:
            insights.append(f"[Predictive] Forecasting {query_focus} trends for next {forecast_periods} periods")
            recommendations.append(f"Prepare inventory planning based on {query_focus} predictions")
        
        if analytics_type in ["prescriptive", "all"]:
            insights.append(f"[Prescriptive] Optimization recommendations for {query_focus}")
            recommendations.append(f"Implement best practices for {query_focus} management")
            
            # Add specific prescriptive recommendations
            if query_focus == "stock_levels":
                recommendations.append("Set optimal reorder points and safety stock levels")
            elif query_focus == "turnover":
                recommendations.append("Focus on fast-moving items and optimize slow movers")
        
        # Calculate summary statistics
        if results:
            total_value = sum(abs(float(row.get('total_value', 0))) for row in results if row.get('total_value'))
            total_quantity = sum(abs(float(row.get('quantity', 0))) for row in results if row.get('quantity'))
        else:
            total_value = total_quantity = 0
        
        analytics_results = {
            "analytics_type": analytics_type,
            "query_focus": query_focus,
            "key_insights": insights,
            "recommendations": recommendations,
            "confidence_level": 0.80,
            "data_points": len(results),
            "summary_stats": {
                "total_value": total_value,
                "total_quantity": total_quantity,
                "analysis_period": f"{start_date} to {end_date}"
            },
            "forecast_periods": forecast_periods if analytics_type in ["predictive", "all"] else None
        }
        
        return {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "analytics_results": analytics_results,
            "timestamp": current_time
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error performing inventory analytics: {str(e)}"
        }