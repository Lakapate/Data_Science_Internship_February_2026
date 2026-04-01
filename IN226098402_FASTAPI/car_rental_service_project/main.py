from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

# -------------------- MODELS --------------------

class RentalRequest(BaseModel):
    customer_name: str = Field(min_length=2)
    car_id: int = Field(gt=0)
    days: int = Field(gt=0, le=30)
    license_number: str = Field(min_length=8)
    insurance: bool = False
    driver_required: bool = False


class NewCar(BaseModel):
    model: str = Field(min_length=2)
    brand: str = Field(min_length=2)
    type: str = Field(min_length=2)
    price_per_day: int = Field(gt=0)
    fuel_type: str = Field(min_length=2)
    is_available: bool = True


# -------------------- DATA --------------------

cars = [
    {"id": 1, "model": "Swift", "brand": "Maruti", "type": "Hatchback", "price_per_day": 1500, "fuel_type": "Petrol", "is_available": True},
    {"id": 2, "model": "City", "brand": "Honda", "type": "Sedan", "price_per_day": 2500, "fuel_type": "Petrol", "is_available": True},
    {"id": 3, "model": "Creta", "brand": "Hyundai", "type": "SUV", "price_per_day": 3000, "fuel_type": "Diesel", "is_available": False},
    {"id": 4, "model": "Fortuner", "brand": "Toyota", "type": "SUV", "price_per_day": 5000, "fuel_type": "Diesel", "is_available": True},
    {"id": 5, "model": "Nexon EV", "brand": "Tata", "type": "SUV", "price_per_day": 3500, "fuel_type": "Electric", "is_available": True},
    {"id": 6, "model": "i20", "brand": "Hyundai", "type": "Hatchback", "price_per_day": 1800, "fuel_type": "Petrol", "is_available": False}
]

rentals = []
rental_counter = 1


# -------------------- HELPERS --------------------

def find_car(car_id):
    for car in cars:
        if car["id"] == car_id:
            return car
    return None


def calculate_rental_cost(price_per_day, days, insurance, driver_required):
    base_cost = price_per_day * days

    discount = 0
    if days >= 15:
        discount = 0.25 * base_cost
    elif days >= 7:
        discount = 0.15 * base_cost

    insurance_cost = 500 * days if insurance else 0
    driver_cost = 800 * days if driver_required else 0

    total = base_cost - discount + insurance_cost + driver_cost

    return {
        "base_cost": base_cost,
        "discount": discount,
        "insurance_cost": insurance_cost,
        "driver_cost": driver_cost,
        "total_cost": total
    }


def filter_cars_logic(type=None, brand=None, fuel_type=None, max_price=None, is_available=None):
    result = cars

    if type is not None:
        result = [c for c in result if c["type"].lower() == type.lower()]

    if brand is not None:
        result = [c for c in result if c["brand"].lower() == brand.lower()]

    if fuel_type is not None:
        result = [c for c in result if c["fuel_type"].lower() == fuel_type.lower()]

    if max_price is not None:
        result = [c for c in result if c["price_per_day"] <= max_price]

    if is_available is not None:
        result = [c for c in result if c["is_available"] == is_available]

    return result




@app.get("/")
def home():
    return {"message": "Welcome to SpeedRide Car Rentals"}


@app.get("/cars/summary")
def cars_summary():
    total = len(cars)
    available = len([c for c in cars if c["is_available"]])

    type_count = {}
    fuel_count = {}

    for car in cars:
        type_count[car["type"]] = type_count.get(car["type"], 0) + 1
        fuel_count[car["fuel_type"]] = fuel_count.get(car["fuel_type"], 0) + 1

    cheapest = min(cars, key=lambda x: x["price_per_day"])
    expensive = max(cars, key=lambda x: x["price_per_day"])

    return {
        "total": total,
        "available": available,
        "by_type": type_count,
        "by_fuel": fuel_count,
        "cheapest": cheapest,
        "most_expensive": expensive
    }


@app.get("/cars")
def get_cars():
    return {
        "total": len(cars),
        "available_count": len([c for c in cars if c["is_available"]]),
        "cars": cars
    }


@app.get("/rentals")
def get_rentals():
    return {"total": len(rentals), "rentals": rentals}


#  FILTER 

@app.get("/cars/filter")
def filter_cars(type: str = None, brand: str = None, fuel_type: str = None, max_price: int = None, is_available: bool = None):
    result = filter_cars_logic(type, brand, fuel_type, max_price, is_available)
    return {"total": len(result), "cars": result}


# CRUD

@app.post("/cars", status_code=201)
def add_car(car: NewCar):
    for c in cars:
        if c["model"].lower() == car.model.lower() and c["brand"].lower() == car.brand.lower():
            raise HTTPException(status_code=400, detail="Car already exists")

    new_id = max([c["id"] for c in cars]) + 1 if cars else 1

    new_car = {**car.dict(), "id": new_id}
    cars.append(new_car)
    return new_car


@app.put("/cars/{car_id}")
def update_car(car_id: int, price_per_day: int = None, is_available: bool = None):
    car = find_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if price_per_day is not None:
        car["price_per_day"] = price_per_day
    if is_available is not None:
        car["is_available"] = is_available

    return car


@app.delete("/cars/{car_id}")
def delete_car(car_id: int):
    car = find_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    for r in rentals:
        if r["car_id"] == car_id and r["status"] == "active":
            raise HTTPException(status_code=400, detail="Car has active rental")

    cars.remove(car)
    return {"message": "Car deleted successfully"}


# -------------------- RENTALS --------------------

@app.post("/rentals")
def create_rental(request: RentalRequest):
    global rental_counter

    car = find_car(request.car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if not car["is_available"]:
        raise HTTPException(status_code=400, detail="Car not available")

    cost = calculate_rental_cost(car["price_per_day"], request.days, request.insurance, request.driver_required)

    car["is_available"] = False

    rental = {
        "rental_id": rental_counter,
        "customer_name": request.customer_name,
        "car_id": car["id"],
        "car_model": car["model"],
        "brand": car["brand"],
        "days": request.days,
        "insurance": request.insurance,
        "driver_required": request.driver_required,
        "cost": cost,
        "status": "active"
    }

    rentals.append(rental)
    rental_counter += 1

    return rental


@app.get("/rentals/active")
def active_rentals():
    result = [r for r in rentals if r["status"] == "active"]
    return {"total": len(result), "rentals": result}


@app.get("/rentals/by-car/{car_id}")
def rentals_by_car(car_id: int):
    result = [r for r in rentals if r["car_id"] == car_id]
    return {"total": len(result), "rentals": result}


@app.get("/rentals/search")
def search_rentals(keyword: str):
    result = [r for r in rentals if keyword.lower() in r["customer_name"].lower()]
    return {"total_found": len(result), "rentals": result}


@app.get("/rentals/sort")
def sort_rentals(sort_by: str = "total_cost"):
    if sort_by not in ["total_cost", "days"]:
        return {"error": "Invalid sort field"}

    sorted_data = sorted(
        rentals,
        key=lambda x: x["cost"]["total_cost"] if sort_by == "total_cost" else x["days"]
    )
    return {"rentals": sorted_data}


@app.get("/rentals/page")
def paginate_rentals(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit
    total = len(rentals)
    total_pages = (total + limit - 1) // limit

    return {"page": page, "total_pages": total_pages, "rentals": rentals[start:end]}


@app.get("/rentals/{rental_id}")
def get_rental(rental_id: int):
    for r in rentals:
        if r["rental_id"] == rental_id:
            return r
    raise HTTPException(status_code=404, detail="Rental not found")


@app.post("/return/{rental_id}")
def return_car(rental_id: int):
    for r in rentals:
        if r["rental_id"] == rental_id:
            if r["status"] == "returned":
                return {"message": "Already returned"}
            r["status"] = "returned"
            car = find_car(r["car_id"])
            if car:
                car["is_available"] = True
            return r

    raise HTTPException(status_code=404, detail="Rental not found")


# -

@app.get("/cars/search")
def search_cars(keyword: str):
    result = [c for c in cars if keyword.lower() in c["model"].lower() or keyword.lower() in c["brand"].lower() or keyword.lower() in c["type"].lower()]
    return {"total_found": len(result), "cars": result}


@app.get("/cars/sort")
def sort_cars(sort_by: str = "price_per_day", order: str = "asc"):
    if sort_by not in ["price_per_day", "brand", "type"]:
        return {"error": "Invalid sort field"}

    reverse = True if order == "desc" else False
    sorted_data = sorted(cars, key=lambda x: x[sort_by], reverse=reverse)

    return {"cars": sorted_data}


@app.get("/cars/page")
def paginate_cars(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    end = start + limit
    total = len(cars)
    total_pages = (total + limit - 1) // limit

    return {"page": page, "total_pages": total_pages, "cars": cars[start:end]}


@app.get("/cars/unavailable")
def unavailable_cars():
    result = [c for c in cars if not c["is_available"]]
    return {"total": len(result), "cars": result}


@app.get("/cars/browse")
def browse_cars(keyword: str = None, type: str = None, fuel_type: str = None, max_price: int = None,
                is_available: bool = None, sort_by: str = "price_per_day", order: str = "asc",
                page: int = 1, limit: int = 3):

    result = cars

    if keyword:
        result = [c for c in result if keyword.lower() in c["model"].lower() or keyword.lower() in c["brand"].lower() or keyword.lower() in c["type"].lower()]

    if type:
        result = [c for c in result if c["type"].lower() == type.lower()]

    if fuel_type:
        result = [c for c in result if c["fuel_type"].lower() == fuel_type.lower()]

    if max_price:
        result = [c for c in result if c["price_per_day"] <= max_price]

    if is_available is not None:
        result = [c for c in result if c["is_available"] == is_available]

    reverse = True if order == "desc" else False
    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    total = len(result)
    total_pages = (total + limit - 1) // limit

    start = (page - 1) * limit
    end = start + limit

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "cars": result[start:end]
    }



@app.get("/cars/{car_id}")
def get_car(car_id: int):
    car = find_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car