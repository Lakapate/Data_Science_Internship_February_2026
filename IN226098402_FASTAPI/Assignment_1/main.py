from fastapi import FastAPI

app = FastAPI()

# Initial Products List
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "USB Cable", "price": 199, "category": "Electronics", "in_stock": False},

    # Task 1 – Added Products
    {"id": 5, "name": "Laptop Stand", "price": 899, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1299, "category": "Electronics", "in_stock": False},
]


# Q1 – Show All Products
@app.get("/products")
def get_products():
    return {
        "products": products,
        "total": len(products)
    }


# Q2 – Filter Products by Category
@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):

    filtered = [
        p for p in products
        if p["category"].lower() == category_name.lower()
    ]

    if not filtered:
        return {"error": "No products found in this category"}

    return {
        "category": category_name,
        "products": filtered
    }


# Q3 – Show Only In-Stock Products
@app.get("/products/instock")
def get_instock_products():

    instock = [
        p for p in products
        if p["in_stock"] == True
    ]

    return {
        "in_stock_products": instock,
        "count": len(instock)
    }


# Q4 – Store Summary
@app.get("/store/summary")
def store_summary():

    total = len(products)

    instock = len([p for p in products if p["in_stock"]])

    outstock = total - instock

    categories = list(set([p["category"] for p in products]))

    return {
        "store_name": "My E-commerce Store",
        "total_products": total,
        "in_stock": instock,
        "out_of_stock": outstock,
        "categories": categories
    }


# Q5 – Search Products by Name
@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    matches = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    if not matches:
        return {"message": "No products matched your search"}

    return {
        "matched_products": matches,
        "total_matches": len(matches)
    }


#  BONUS – Cheapest and Most Expensive Product
@app.get("/products/deals")
def product_deals():

    cheapest = min(products, key=lambda x: x["price"])

    expensive = max(products, key=lambda x: x["price"])

    return {
        "best_deal": cheapest,
        "premium_pick": expensive
    }