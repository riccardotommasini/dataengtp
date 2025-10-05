-- 1. Update a customer’s email (safely avoid unique-email conflicts)


UPDATE Customers
SET Email = $2
WHERE CustomerID = $1
  AND NOT EXISTS (SELECT 1 FROM Customers WHERE Email = $2)
RETURNING CustomerID, FirstName, LastName, Email;
-- $1 = customer_id, $2 = new_email


-- 2. Move a purchase to a different store


UPDATE Purchases
SET StoreID = $2
WHERE PurchaseID = $1
RETURNING PurchaseID, StoreID, PurchaseDateTime;
-- $1 = purchase_id, $2 = new_store_id


-- 3. Change payment method and amount for a purchase (idempotent on PurchaseID)


UPDATE Payments
SET PaymentMethod = $2, Amount = $3
WHERE PurchaseID = $1
RETURNING PaymentID, PurchaseID, PaymentMethod, Amount;
-- $1 = purchase_id, $2 IN ('Cash','Card','Voucher'), $3 = amount


-- 4. Reassign a product to a category (create category if it doesn’t exist)


WITH upsert_cat AS (
  INSERT INTO Categories (CategoryName)
  VALUES ($2)
  ON CONFLICT (CategoryName) DO UPDATE SET CategoryName = EXCLUDED.CategoryName
  RETURNING CategoryID
)
UPDATE Products
SET CategoryID = (SELECT CategoryID FROM upsert_cat)
WHERE ProductID = $1
RETURNING ProductID, ProductName, CategoryID;
-- $1 = product_id, $2 = category_name


-- 5. Optimistic price change (only if current price matches expected old price)


UPDATE Products
SET Price = $2
WHERE ProductID = $1
  AND Price = $3
RETURNING ProductID, ProductName, Price AS new_price;
-- $1 = product_id, $2 = new_price, $3 = expected_old_price


---

