footer:  [Riccardo Tommasini](http://rictomm.me) - riccardo.tommasini@insa-lyon.fr - @rictomm 
slide-dividers: #, ##, ###
slidenumbers: true
autoscale: true
build-lists: true
theme: Plain Jane

# Dimensional Modeling

## What is dimensional modeling?

Dimensional modeling is widely accepted as the preferred technique for presenting analytic data because it addresses two simultaneous requirements:

- Deliver data that’s understandable to business users.
- Deliver fast query performance.

It is a longstanding technique for making databases simple.

---

## Main flow of dimensional modeling

1. **Select the business process**
	- A _business process_ is a set of activities with a goal.  
		- BPs are critical activities that your organization performs, e.g., registering students for a class.
	- Events from the process produce metrics.
	- Most fact tables model one process.
	- Choosing the process sets the design target.
2. **Declare the grain**
	- Grain: what one row in the fact table represents.
	- Everything (facts and dimensions) must align to the grain.
	- Start atomic: model at the lowest captured level possible.
	- Don’t mix grains.

## Main flow of dimensional modeling
	
3. **Identify the dimensions**
	- Dimensions provide context ("features").
	- Used for filtering, grouping, and labeling.
	- Dimensions give meaning to data.
	- Spend more effort modeling dimensions than facts.
        
4. **Identify the facts**
	- Facts are numeric measurements produced by the business process.
	- Prefer modeling **physical events**.

## Facts and dimensions

- **Facts** are the measurements that result from a business process event and are almost always numeric. 
- 
- **Dimensions** provide context to business process events, e.g.,  who, what, where, when, why, and how. 

![inline](../attachments/dim1.png)![inline](../attachments/dim2.png)


### Star schema

![inline](../attachments/dim3.png)

## Facts

[.column]

- Each row corresponds to a **measurement event**.    
- Most useful facts are **numeric** and **additive**.
- **Keys**
    - Fact tables usually have at least two foreign keys.
    - Composite primary key often formed by some/all dimension keys.
    - May also include a *surrogate key*, i.e., a unique identifier that you add to a table to support star schema modeling. By definition, it's not defined or stored in the source data
- The data on each row is at a specific **level of detail (grain)**.
- Grain should be **consistent** for the entire fact table.

[.column]

![inline](../attachments/dim4-facts.png)

### Facts: Grain types

The **grain** establishes exactly what a single fact table row represents.  Three common grains categorize all fact tables: transactional, periodic snapshot, or accumulating snapshot. 
 
![inline](../attachments/dim4-facts2.png)

---

## Dimensions

- Contain the **textual context** associated with a measurement event.
- Describe the **who, what, where, when, how, and why**.
    
- Generally **fewer rows, more columns** than fact tables.
    
- Use a **single surrogate primary key**.
    
- **Heuristic:** identify dimensions with “_by_” phrases:
    
    - Sales **by** store
        
    - Clicks **by** customer
        
    - Events **by** line
        
![inline](../attachments/dim5.png)


## Slowly Changing Dimensions (SCD)

What happens if something “changes”?
- A customer moves
- Product price changes?

## Slowly Changing Dimensions (SCD)

![inline](../attachments/dim9-types.png)

## Slowly Changing Dimensions (SCD)

![inline](../attachments/dim9-types2.png)

### Queryable Table

|Type|Dimension Table Action|Impact on Fact Analysis|
|---|---|---|
|**0**|No change to attribute value|Facts remain associated with the original attribute value|
|**1**|Overwrite attribute value|Facts associated with the **current** value|
|**2**|Add a new dimension row with the new attribute value|Facts associated with the value **in effect when the fact occurred**|
|**3**|Add a new column to preserve current and prior values|Facts analyzable by both current and prior alternative values|
|**4**|Add a mini‑dimension for rapidly changing attributes|Facts associated with the rapidly changing attributes in effect at the time|
|**5**|Type 4 mini‑dimension **plus** type 1 overwrite of mini‑dimension key in base dimension|Facts associated with rapidly changing attributes in effect at the time **plus** current rapidly changing values|
|**6**|Type 2 with type 1 overwrites (a.k.a. hybrid)|Facts associated with historical value **plus** current values|
|**7**|Type 2 with a view limited to current rows/values|Facts associated with historical value **plus** current values|

### Common patterns

- **Type 1:** Overwrite in place.
    
- **Type 2:** Add a new row; invalidate (or end‑date) the old row.
    

---

## Bus matrix

[.column]

- A **blueprint/design tool**.
    
- **Rows:** business processes.
    
- **Columns:** (core) dimensions.
    
- Mark with **X** where a dimension participates in a process.
    
[.column]

![inline](../attachments/dim7.png)

## Facts and dimensions in SQL

![inline](../attachments/dim8.png)

## Facts and dimensions in SQL

[.column]

![inline](../attachments/dim8.png)

[.column]

```sql
SELECT
    store.district_name,
    product.brand,
    SUM(sales_facts.sales_dollars) AS "Sales Dollars"
FROM
    store,
    product,
    date,
    sales_facts
WHERE
    date.month_name = 'January' AND
    date.year = 2013 AND
    store.store_key = sales_facts.store_key AND
    product.product_key = sales_facts.product_key AND
    date.date_key = sales_facts.date_key
GROUP BY
    store.district_name,
    product.brand;
```


## Dimensional modeling is not all…

- **Dimensional modeling** (Star schema / “Kimball”)
    
- **Inmon** (Enterprise Data Warehouse, top‑down)
    
- **Data Vault** (Hub‑Link‑Satellite)
    
- **OBT** (One‑Big‑Table / wide table)
    

---

## Tips, tricks, considerations

- **Handling NULLs**
    
    - **Fact tables:** NULL may be acceptable for the measure itself.
        
    - **Dimension FKs:** avoid NULLs; instead use **Unknown** members (e.g., ID = −1, Name = "Unknown").
        
- **Meta‑columns**
    
    - ValidFrom / ValidTo (SCDs)
        
    - CreatedByJobId, ModifiedByJobId, CreatedAt, ModifiedAt, …
        
- **Is it a fact or a dimension?**
    
    - Be careful with entities like **Claim**, **Support ticket**, **Loan application**.
        
    - Avoid **1:1** fact:dimension mapping.
        
- **Dimensions for feature engineering**
    
    - Especially **DimDate** and **DimTime**.
    
### The 5/10 Essential Rules of Dimensional Modeling (Read)[^42]

1. Load detailed atomic data into dimensional structures.
2. Structure dimensional models around business processes.
3. Ensure that every fact table has an associated date dimension table.
4. Ensure that all facts in a single fact table are at the same grain or level of detail.
5. Resolve many-to-many relationships in fact tables.

### The 10/10 Essential Rules of Dimensional Modeling (Read)[^42]

6. Resolve many-to-one relationships in dimension tables.
7.  Store report labels and filter domain values in dimension tables.
8.  Make certain that dimension tables use a surrogate key.
9.  Create conformed dimensions to integrate data across the enterprise.
10. Continuously balance requirements and realities to deliver a DW/BI solution that’s accepted by business users and that supports their decision-making.

[^42]:https://www.kimballgroup.com/2009/05/the-10-essential-rules-of-dimensional-modeling/

## Further reading

- _The Data Warehouse Toolkit_ (3rd ed.) — Kimball & Ross.  
	- Chapter 2 and 3 on [O’Reilly Online](https://learning.oreilly.com/library/view/the-data-warehouse/9781118530801/)
- [Techniques](http://www.kimballgroup.com/wp-content/uploads/2013/08/2013.09-Kimball-Dimensional-Modeling-Techniques11.pdf)
    
![right fit](https://images-na.ssl-images-amazon.com/images/I/51dvU76edNL._SX399_BO1,204,203,200_.jpg)

