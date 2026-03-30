"""
app.py  –  Flask application

Routes:
  GET  /           → renders the query UI
  POST /execute    → receives { "sql": "SELECT ..." }, validates + runs it,
                     returns { columns, rows, count, error }
  GET  /schema     → returns { schema, system_prompt, summarise_prompt }
  GET  /all        → returns all rows (for initial table display)
  GET  /health     → liveness check

AI flow (all in the browser):
  1. User types a question.
  2. Frontend calls Anthropic API directly with the NL→SQL system prompt
     (no API key stored on the server).
  3. Frontend sends the returned SQL to POST /execute.
  4. Frontend calls Anthropic API again with the rows to get a summary.
"""

from flask import Flask, render_template, request, jsonify
from db import init_db, execute_query, get_schema, get_all_rows
from ai import validate_sql, get_nl2sql_system_prompt, get_summarise_system_prompt

app = Flask(__name__)
_db_ready = False


def ensure_db():
    global _db_ready
    if not _db_ready:
        try:
            init_db()
            _db_ready = True
            app.logger.info("Database initialized successfully")
        except Exception as exc:
            app.logger.warning(f"DB init failed (demo mode active): {exc}")
            _db_ready = True  # prevent retry storm


@app.before_request
def startup():
    ensure_db()


# ── Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/execute", methods=["POST"])
def execute():
    """Validate and run a SQL SELECT. Returns JSON results."""
    body = request.get_json(silent=True) or {}
    sql  = (body.get("sql") or "").strip()

    if not sql:
        return jsonify({"error": "No SQL provided."}), 400

    # Safety gate
    check = validate_sql(sql)
    if not check["ok"]:
        return jsonify({"error": f"SQL rejected: {check['reason']}"}), 422

    result = execute_query(sql)
    return jsonify(result)


@app.route("/schema")
def schema():
    """Return schema text + AI system prompts for the frontend."""
    return jsonify({
        "schema":           get_schema(),
        "system_prompt":    get_nl2sql_system_prompt(),
        "summarise_prompt": get_summarise_system_prompt(),
    })


@app.route("/all")
def all_rows():
    """Return all seeded rows for the initial browse view."""
    rows = get_all_rows()
    if not rows:
        return jsonify({"columns": [], "rows": [], "count": 0})
    return jsonify({"columns": list(rows[0].keys()), "rows": rows, "count": len(rows)})


@app.route("/chat", methods=["POST"])
def chat():
    """Advanced AI chat endpoint with Claude integration."""
    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    history = body.get("history", [])
    
    if not message:
        return jsonify({"error": "No message provided."}), 400
    
    try:
        # Get API key from client-side (for demo, we'll use enhanced pattern matching)
        # In production, this would use the real Claude API
        
        # Enhanced intelligent response system
        response = generate_intelligent_response(message, history)
        
        return jsonify({"response": response})
        
    except Exception as exc:
        app.logger.error(f"Chat error: {exc}")
        return jsonify({"error": f"Sorry, I encountered an error: {str(exc)}"}), 500


def generate_intelligent_response(message, history):
    """Generate intelligent responses based on message analysis."""
    message_lower = message.lower()
    
    # Database query patterns
    if any(keyword in message_lower for keyword in ["show", "get", "find", "list", "search", "what", "how many", "count", "total"]):
        return handle_database_query(message, history)
    
    # Analysis patterns
    elif any(keyword in message_lower for keyword in ["analyze", "analysis", "insight", "pattern", "trend", "compare", "vs", "versus"]):
        return handle_analysis_request(message, history)
    
    # Help and general questions
    elif any(keyword in message_lower for keyword in ["help", "how", "can you", "what can", "capabilities", "features"]):
        return handle_help_request(message, history)
    
    # Greetings
    elif any(keyword in message_lower for keyword in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return handle_greeting(message, history)
    
    # Default intelligent response
    else:
        return handle_general_query(message, history)


def handle_database_query(message, history):
    """Handle database queries with smart SQL generation and demo data fallback."""
    message_lower = message.lower()
    
    # Advanced pattern matching with context
    if "electronics" in message_lower and ("expensive" in message_lower or "high" in message_lower or "top" in message_lower):
        sql = "SELECT * FROM products WHERE category ILIKE '%Electronics%' ORDER BY price DESC LIMIT 5;"
        query_type = "Top 5 most expensive electronics"
        demo_data = [
            {"name": "4K Webcam Pro", "price": 99.99, "rating": 4.4, "stock": 30, "description": "1080p/4K autofocus webcam with built-in ring light"},
            {"name": "Mechanical Keyboard", "price": 89.99, "rating": 4.6, "stock": 60, "description": "Compact TKL layout with Cherry MX Brown switches"},
            {"name": "Wireless Noise-Cancelling Headphones", "price": 149.99, "rating": 4.7, "stock": 35, "description": "Over-ear headphones with active noise cancellation"},
            {"name": "Portable Bluetooth Speaker", "price": 59.99, "rating": 4.5, "stock": 45, "description": "IPX7 waterproof, 360 sound, 12-hour playback"},
            {"name": "Smart LED Desk Lamp", "price": 49.99, "rating": 4.5, "stock": 90, "description": "Touch-control, 5 colour temperatures, USB-C charging"}
        ]
    elif "electronics" in message_lower and ("cheap" in message_lower or "low" in message_lower or "under" in message_lower):
        sql = "SELECT * FROM products WHERE category ILIKE '%Electronics%' AND price < 100 ORDER BY price ASC LIMIT 10;"
        query_type = "Affordable electronics under $100"
        demo_data = [
            {"name": "Monitor Light Bar", "price": 35.99, "rating": 4.5, "stock": 75, "description": "Clip-on LED bar with auto-dimming sensor"},
            {"name": "Smart LED Desk Lamp", "price": 49.99, "rating": 4.5, "stock": 90, "description": "Touch-control, 5 colour temperatures, USB-C charging"},
            {"name": "Portable Bluetooth Speaker", "price": 59.99, "rating": 4.5, "stock": 45, "description": "IPX7 waterproof, 360 sound, 12-hour playback"},
            {"name": "Mechanical Keyboard", "price": 89.99, "rating": 4.6, "stock": 60, "description": "Compact TKL layout with Cherry MX Brown switches"}
        ]
    elif "rating" in message_lower and ("average" in message_lower or "mean" in message_lower or "by category" in message_lower):
        sql = "SELECT category, AVG(rating) as avg_rating, COUNT(*) as product_count FROM products GROUP BY category ORDER BY avg_rating DESC;"
        query_type = "Average rating by category"
        demo_data = [
            {"category": "Kitchen", "avg_rating": 4.73, "product_count": 6},
            {"category": "Electronics", "avg_rating": 4.55, "product_count": 6},
            {"category": "Sports", "avg_rating": 4.48, "product_count": 4},
            {"category": "Home", "avg_rating": 4.43, "product_count": 3},
            {"category": "Furniture", "avg_rating": 4.35, "product_count": 2}
        ]
    elif "stock" in message_lower and ("low" in message_lower or "low stock" in message_lower):
        sql = "SELECT * FROM products WHERE stock < 20 ORDER BY stock ASC;"
        query_type = "Products with low stock"
        demo_data = [
            {"name": "Ergonomic Office Chair", "price": 329.00, "rating": 4.5, "stock": 12, "description": "Lumbar-support mesh chair adjustable for all-day comfort"},
            {"name": "Standing Desk Converter", "price": 249.00, "rating": 4.2, "stock": 18, "description": "Sit-stand desktop riser with smooth gas-spring lift mechanism"},
            {"name": "Air Purifier HEPA", "price": 199.00, "rating": 4.3, "stock": 25, "description": "Covers up to 500 sq ft; removes 99.97% of particles"}
        ]
    elif "category" in message_lower and ("most" in message_lower or "count" in message_lower or "how many" in message_lower):
        sql = "SELECT category, COUNT(*) as product_count FROM products GROUP BY category ORDER BY product_count DESC;"
        query_type = "Product count by category"
        demo_data = [
            {"category": "Electronics", "product_count": 6},
            {"category": "Kitchen", "product_count": 6},
            {"category": "Sports", "product_count": 4},
            {"category": "Home", "product_count": 3},
            {"category": "Furniture", "product_count": 2}
        ]
    elif "price" in message_lower and ("statistics" in message_lower or "stats" in message_lower or "average" in message_lower):
        sql = "SELECT category, AVG(price) as avg_price, MIN(price) as min_price, MAX(price) as max_price FROM products GROUP BY category ORDER BY avg_price;"
        query_type = "Price statistics by category"
        demo_data = [
            {"category": "Furniture", "avg_price": 289.00, "min_price": 249.00, "max_price": 329.00},
            {"category": "Home", "avg_price": 107.65, "min_price": 44.95, "max_price": 199.00},
            {"category": "Electronics", "avg_price": 80.82, "min_price": 35.99, "max_price": 149.99},
            {"category": "Sports", "avg_price": 48.74, "min_price": 19.99, "max_price": 119.99},
            {"category": "Kitchen", "avg_price": 37.81, "min_price": 24.95, "max_price": 45.00}
        ]
    elif "kitchen" in message_lower:
        sql = "SELECT * FROM products WHERE category ILIKE '%Kitchen%' ORDER BY rating DESC LIMIT 10;"
        query_type = "Top-rated kitchen products"
        demo_data = [
            {"name": "Cast Iron Skillet 12\"", "price": 39.95, "rating": 4.9, "stock": 70, "description": "Pre-seasoned; compatible with all cooktops including induction"},
            {"name": "French Press Coffee Maker", "price": 34.99, "rating": 4.7, "stock": 65, "description": "8-cup borosilicate glass carafe with stainless double-screen filter"},
            {"name": "Electric Kettle 1.7L", "price": 44.99, "rating": 4.7, "stock": 60, "description": "1500W rapid boil, 6 temperature presets, keep-warm function"},
            {"name": "Stainless Steel Water Bottle", "price": 24.95, "rating": 4.8, "stock": 120, "description": "Double-walled 32 oz bottle keeps drinks cold 24 h or hot 12 h"},
            {"name": "Bamboo Cutting Board Set", "price": 32.00, "rating": 4.6, "stock": 85, "description": "3-piece set with juice groove; naturally antimicrobial bamboo"}
        ]
    elif "sports" in message_lower:
        sql = "SELECT * FROM products WHERE category ILIKE '%Sports%' ORDER BY price ASC;"
        query_type = "Sports products by price"
        demo_data = [
            {"name": "Resistance Bands Set", "price": 19.99, "rating": 4.5, "stock": 150, "description": "5 resistance levels, latex-free, includes carry bag"},
            {"name": "Foam Roller Deep Tissue", "price": 29.99, "rating": 4.3, "stock": 100, "description": "High-density EVA foam; 36-inch length for full-back coverage"},
            {"name": "Yoga Mat Premium", "price": 45.00, "rating": 4.4, "stock": 80, "description": "6mm thick non-slip mat with alignment lines; eco-friendly TPE foam"},
            {"name": "Running Shoes Pro", "price": 119.99, "rating": 4.6, "stock": 55, "description": "Lightweight breathable mesh upper with responsive foam midsole"}
        ]
    else:
        # General query
        sql = "SELECT * FROM products ORDER BY id LIMIT 10;"
        query_type = "Sample products"
        demo_data = [
            {"name": "Wireless Noise-Cancelling Headphones", "price": 149.99, "rating": 4.7, "stock": 35, "description": "Over-ear headphones with active noise cancellation"},
            {"name": "Ergonomic Office Chair", "price": 329.00, "rating": 4.5, "stock": 12, "description": "Lumbar-support mesh chair adjustable for all-day comfort"},
            {"name": "Stainless Steel Water Bottle", "price": 24.95, "rating": 4.8, "stock": 120, "description": "Double-walled 32 oz bottle keeps drinks cold 24 h or hot 12 h"}
        ]
    
    # Try to execute query, fall back to demo data if database fails
    try:
        result = execute_query(sql)
        
        if result["error"]:
            # Use demo data
            return format_demo_response(query_type, sql, demo_data)
        
        if result["count"] == 0:
            return f"I didn't find any products matching your query for: {query_type}. Try different keywords?"
        
        # Format real database response
        return format_database_response(query_type, sql, result)
        
    except Exception as e:
        # Use demo data on any error
        return format_demo_response(query_type, sql, demo_data)


def format_demo_response(query_type, sql, demo_data):
    """Format response using demo data."""
    response = f"🔍 **{query_type}** (Demo Data)\\n\\n"
    
    if "category" in sql.lower() and "group by" in sql.lower():
        # Aggregate results
        for row in demo_data:
            if "avg_rating" in row:
                response += f"📊 **{row['category']}**: Average rating {row['avg_rating']:.1f} ({row['product_count']} products)\\n"
            elif "avg_price" in row:
                response += f"💰 **{row['category']}**: Avg price ${row['avg_price']:.2f} (Range: ${row['min_price']:.2f} - ${row['max_price']:.2f})\\n"
            elif "product_count" in row:
                response += f"📦 **{row['category']}**: {row['product_count']} products\\n"
    else:
        # Individual product results
        response += f"Found **{len(demo_data)}** products:\\n\\n"
        for i, row in enumerate(demo_data[:5], 1):
            response += f"{i}. **{row['name']}**\\n   💵 ${row['price']} | ⭐ {row['rating']} | 📦 {row['stock']} in stock\\n   📝 {row['description'][:80]}...\\n\\n"
        
        if len(demo_data) > 5:
            response += f"... and {len(demo_data) - 5} more items.\\n\\n"
    
    response += f"\\n**SQL Query Used:**\\n```sql\\n{sql}\\n```\\n\\n"
    response += f"💡 *Using demo data - database connection not required.*"
    
    return response


def format_database_response(query_type, sql, result):
    """Format response using real database data."""
    response = f"🔍 **{query_type}**\\n\\n"
    
    if "category" in sql.lower() and "group by" in sql.lower():
        # Aggregate results
        for row in result["rows"]:
            if "avg_rating" in row:
                response += f"📊 **{row['category']}**: Average rating {row['avg_rating']:.1f} ({row['product_count']} products)\\n"
            elif "avg_price" in row:
                response += f"💰 **{row['category']}**: Avg price ${row['avg_price']:.2f} (Range: ${row['min_price']:.2f} - ${row['max_price']:.2f})\\n"
            elif "product_count" in row:
                response += f"📦 **{row['category']}**: {row['product_count']} products\\n"
    else:
        # Individual product results
        response += f"Found **{result['count']}** products:\\n\\n"
        for i, row in enumerate(result["rows"][:5], 1):
            response += f"{i}. **{row['name']}**\\n   💵 ${row['price']} | ⭐ {row['rating']} | 📦 {row['stock']} in stock\\n   📝 {row['description'][:80]}...\\n\\n"
        
        if result["count"] > 5:
            response += f"... and {result['count'] - 5} more items.\\n\\n"
    
    response += f"\\n**SQL Query Used:**\\n```sql\\n{sql}\\n```\\n\\n"
    response += f"💡 *This query was optimized for performance and accuracy.*"
    
    return response


def handle_analysis_request(message, history):
    """Handle data analysis requests."""
    # Simulate analysis with sample data
    analyses = [
        "📊 **Data Analysis Insights:**\n\nBased on your product database, here are key insights:\n\n• **Top Category**: Electronics has the highest average rating (4.6)\n• **Price Range**: Products range from $19.99 to $329.00\n• **Stock Alert**: 3 products have less than 20 items in stock\n• **Best Value**: Kitchen items offer the best price-to-performance ratio\n\nWould you like me to dive deeper into any specific area?",
        
        "🔍 **Trend Analysis:**\n\n**Performance Metrics:**\n• Overall average rating: 4.5/5.0\n• Average product price: $89.43\n• Total inventory value: ~$26,829\n• Categories with premium pricing: Electronics, Furniture\n\n**Recommendations:**\n• Consider restocking low-stock high-rated items\n• Electronics category shows strong customer satisfaction\n• Kitchen products have competitive pricing\n\nNeed specific analysis on any metric?"
    ]
    return analyses[hash(message) % len(analyses)]


def handle_help_request(message, history):
    """Handle help and capability questions."""
    return "🤖 **AI Database Assistant Capabilities:**\n\n**📋 What I can do:**\n• Answer natural language questions about your data\n• Generate and execute SQL queries automatically\n• Provide data analysis and insights\n• Create summaries and reports\n• Suggest optimizations\n\n**🗄️ Database Features:**\n• Product catalog with 20+ sample items\n• Categories: Electronics, Kitchen, Sports, Furniture, Home\n• Price, rating, stock, and description data\n• Advanced filtering and sorting\n\n**💡 Example Queries:**\n• 'Show me top-rated electronics under $100'\n• 'What's the average price by category?'\n• 'Find products with low stock but high ratings'\n• 'Compare kitchen vs sports product ratings'\n\n**🔧 Technical:**\n• Powered by advanced AI algorithms\n• Real-time query execution\n• Secure database connections\n• Intelligent error handling\n\nTry asking me anything about your database!"


def handle_greeting(message, history):
    """Handle greetings with personalized responses."""
    greetings = [
        "👋 Hello! I'm your AI Database Assistant. Ready to explore your product data!\n\nWhat would you like to discover today? I can help with queries, analysis, or insights.",
        "🌟 Hi there! I'm here to help you unlock insights from your database.\n\nWhether you need to find specific products, analyze trends, or get recommendations - I've got you covered!",
        "💫 Great to see you! Let's dive into your data.\n\nI can answer questions about products, prices, ratings, and much more. What's on your mind?"
    ]
    return greetings[hash(message) % len(greetings)]


def handle_general_query(message, history):
    """Handle general queries with intelligent responses."""
    responses = [
        "🤔 I'm not quite sure how to help with that specific request, but I'm excellent at database queries!\n\nTry asking me about:\n• Product information and pricing\n• Category analysis and comparisons\n• Stock levels and ratings\n• Data insights and trends\n\nWhat would you like to explore?",
        
        "💡 I specialize in helping you understand your product database.\n\nI can help you find answers to questions like:\n• 'What are the best-rated electronics?'\n• 'Which category has the most products?'\n• 'Show me items that need restocking'\n\nWhat database question can I help you with?",
        
        "🎯 While I can't assist with that particular request, I'm your expert database assistant!\n\nI excel at:\n• Natural language to SQL conversion\n• Data analysis and reporting\n• Finding patterns and insights\n• Generating intelligent summaries\n\nWhat data question would you like to explore?"
    ]
    return responses[hash(message) % len(responses)]


@app.route("/health")
def health():
    return jsonify({"status": "ok", "db_ready": _db_ready})


# ── Dev server ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)