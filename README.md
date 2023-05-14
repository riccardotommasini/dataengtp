---
share: true
title: Readme
---
# Data Engineering

The course aims at giving an overview of Data Engineering foundational concepts. It is tailored for 1st and 2nd year Msc students and PhDs who would like to strengthen their fundamental understanding of Data Engineering, i.e., Data Modelling, Collection, and Wrangling.

## Origin and Design

The course was originally held in different courses at Politecnico di Milano (🇮🇹) by Emanuele Della Valle and Marco Brambilla. The first issue as a unified journey into the data world dates back to 2020 at the University of Tartu (🇪🇪) by Riccardo Tommasini, and where it is still held by professor Ahmed Awad (course LTAT.02.007). At the same time, the course was adopted by INSA Lyon (🇫🇷) as OT7 (2022) and PLD "Data"

![logo tartu](https://upload.wikimedia.org/wikipedia/en/3/39/Tartu_%C3%9Clikool_logo.svg)
![logo polimi](http://datascience.deib.polimi.it/wp-content/uploads/2016/02/polimi-logo.png)

![logo insa](https://www.edarabia.com/wp-content/uploads/2018/02/insa-lyon-villeurbanne-france.jpg)

## Contributors

- [Riccardo Tommasini](../Riccardo%20Tommasini.md)
- [Emanuele Della Valle](emanueledellavalle.org/) (Big Data )
- [Marco Brambilla](https://marco-brambilla.com/) (NoSQL)
- [Ahmed Awad](Ahmed%20Awad) (Lecturing and Maintenance)
- [Radwa ElShawi](Radwa%20ElShawi) (Data Wrangling)
- [Fabiano Spiga](mailto:),  (Practices)
- [Mohamed Ragab](https://bigdata.cs.ut.ee/mohamed-ragab), (Practices)
- [Hassan Eldeeb](mailto:hassan.eldeeb@ut.ee) (Practices)



## Learning Goals

 Students of this course will obtain two sets of skills: one that is deeply technical and necessarily technologically biased, one that is more abstract (soft) yet essential to build the professional figure that fits in a data team. 

### Soft Skills

- Build a general overview of the data lifecycle and its problems
	- ETL, ELT
	- Data Pipelines
- Understand the role of the Data Engineer, as opposed to the more famous figure of Data Scientist. 
	- Skills required by data engineers
	- Fitting in a data team
- Presenting a data project
	- Writing a post mortem

**Creativity Bonus**: the students will be encouraged to come up with their information needs about a domain of their choice.


### Hard Skills


After a general overview of the data lifecycle, the course deeps into an (**opinionated**) view of the modern [[Data Warehouse]]. To this extent, the will touch basic notions of Data Wrangling, in particular Cleansing and Transformation.

At the core of the course learning outcome there is the **ability to design, build, and maintain** a data pipelines.

**Technological Choice (May 2023): Apache Airlfow**

[[Why Apache Airfllow?]]

Regarding the technological stack of the course, modulo the choice of the lecturer, the following systems are encourages.

- Data Formats 
	- JSON, CSV, Avro
	- Parquet
- Relational Databases
	- Postgres
- Document Databases
	- MongoDB
- Columnar Stores
	- DuckDB
- Key-Value Stores
	- Redis
 - Graph Databases
	 - Neo4J


The interaction with the aforementioned systems is via python using Jupyter notebooks. The environment is powered by [[Docker]] and orchestrated using [[Docker Compose]]. 


### Challenge Based Learning

The cours follows a challenge based learning approach. In particular, each system is approached independently with a uniform interface (python API). The students main task is to build a pipelines managed by [Apache Airflow](../Apache%20Airflow.md) that integrates 3/5 of the presented systems. The course schedule **does not** include an explanation on how such integration should be done. Indeed, it is up for each group to figure out how to do it, if developing a custom operator or scheduling scripts or more. The students are then encouraged to discuss their approach and present the limitations.

## Prerequisites

- Git and Github
- SQL and Relational Databases
- Python
- Java (basics)

# Syllabus

🖐️ = Practice
📓 = Lecture

- Into: Who is the Data Engineer + Data Lifecycle (📓)
- Docker Fundamentals (🖐️)
- Data Modelling (📓) 
	- ER (basics)
	- Dimensional Modelling and Star Schema (basics)
	- Data Formats: JSON, CSV, Avro, Parquet (🖐️)
- Data Orchestrations and Data Pipelines (📓) 
	- Apache Airflow (🖐️)
- Data Wrangling and Cleansing  (📓) 
	-  Pandas (🖐)
- Data Ingestion and Document Databases (📓) 
	- MongoDB  (🖐)
- Caching and  Key-Value Stores (📓) 
	- Redis or RocksDB  (🖐)
- Querying: (📓) 
	- Postgres or SQLLite (🖐)
- Advanced Querying: Wide Columns Stores and Graph Databases  (📓) 
	- Cassandra or DuckDB
	- Neo4J or Memgraph  (🖐)


### Evaluation

- Multiple Choice Questions (30%)
- Project (60%)
- Presentation (10%)

[Latest Course Issue](https://www.riccardotommasini.com/courses/2022-10-03-dataeng-insa-ot/)

# Books

 Database System Concepts 7th Edition Avi Silberschatz Henry F. Korth S. Sudarshan McGraw-Hill ISBN 9780078022159
  - [Table of contents](https://www.db-book.com/db7/toc-dir/toc.pdf)
  - [slides](https://www.db-book.com/db7/slides-dir/index.html)
-  The Data Warehouse Toolkit - The Definitive Guide to Dimensional Modeling Third Edition  Ralph Kimball Margy Ross
- [Designing Data-Intensive Applications - Martin Kleppmann ](https://dataintensive.net/)
-  [Designing Event-Driven Systems](https://www.oreilly.com/library/view/designing-event-driven-systems/9781492038252/)
-  [Graph Databases](https://neo4j.com/graph-databases-book/)
